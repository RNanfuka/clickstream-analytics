"""Optional distributed ETL using Spark SQL (requires `pip install -e '.[spark]`').

The Spark backend writes Parquet facts and daily marts. It does not collect
all events to the driver, and it never treats retail events as health records.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from omnihealth.contracts import (
    HIGHEST_TIMESTAMP_MS,
    LOWEST_TIMESTAMP_MS,
    RAW_COLUMNS,
    DataContractError,
)
from omnihealth.pipeline import _write_json
from omnihealth.provenance import input_manifest


def run_spark_pipeline(
    input_path: str | Path,
    output_dir: str | Path,
    source_type: str,
    gap_minutes: int = 30,
    max_rejected_fraction: float = 0.01,
) -> dict:
    """Run Spark ETL against RetailRocket-shaped local CSV (no pandas conversion)."""
    if source_type not in {"retailrocket", "synthetic_fixture"}:
        raise ValueError("source_type must be 'retailrocket' or 'synthetic_fixture'")
    if gap_minutes <= 0:
        raise ValueError("gap_minutes must be positive")
    if not 0 <= max_rejected_fraction <= 1:
        raise ValueError("max_rejected_fraction must be between 0 and 1")
    try:
        from pyspark.sql import SparkSession, Window
        from pyspark.sql import functions as F
        from pyspark.storagelevel import StorageLevel
    except ImportError as exc:
        raise RuntimeError(
            "PySpark is optional. Install with: python -m pip install -e '.[spark]'"
        ) from exc

    source = Path(input_path)
    if not source.is_file():
        raise DataContractError(f"Input CSV not found: {source}")
    provenance = input_manifest(source, "pyspark")
    output = Path(output_dir)
    spark = (
        SparkSession.builder.appName("OmniHealth-Phase1")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    cached = None
    try:
        incoming = spark.read.option("header", "true").option("inferSchema", "false").csv(
            str(source)
        )
        absent = set(RAW_COLUMNS).difference(incoming.columns)
        if absent:
            raise DataContractError(f"Missing required columns: {', '.join(sorted(absent))}")

        raw = incoming.select(
            *[F.trim(F.coalesce(F.col(c).cast("string"), F.lit(""))).alias(c)
              for c in RAW_COLUMNS]
        )
        # TRY_CAST prevents a malformed timestamp from crashing Spark in ANSI mode.
        staged = raw.withColumn("timestamp_ms", F.expr("try_cast(`timestamp` AS BIGINT)"))
        time_ok = (
            F.col("timestamp").rlike("^[0-9]+$")
            & F.col("timestamp_ms").isNotNull()
            & (F.col("timestamp_ms") >= LOWEST_TIMESTAMP_MS)
            & (F.col("timestamp_ms") < HIGHEST_TIMESTAMP_MS)
        )
        visitor_ok = F.length("visitorid") > 0
        item_ok = F.length("itemid") > 0
        type_ok = F.col("event").isin("view", "addtocart", "transaction")
        transaction_ok = (F.length("transactionid") > 0) == (
            F.col("event") == "transaction"
        )
        flags = {
            "invalid_timestamp": ~time_ok,
            "missing_visitor_id": ~visitor_ok,
            "missing_item_id": ~item_ok,
            "invalid_event_type": ~type_ok,
            "invalid_transaction_id_for_event": ~transaction_ok,
        }
        staged = staged.withColumn(
            "rejection_reason",
            F.concat_ws(";", *[F.when(flag, F.lit(name)) for name, flag in flags.items()]),
        )
        cached = staged.persist(StorageLevel.MEMORY_AND_DISK)
        counts = cached.agg(
            F.count("*").alias("rows_read"),
            F.sum(F.when(F.length("rejection_reason") > 0, 1).otherwise(0)).alias(
                "rows_rejected"
            ),
            *[F.sum(F.when(flag, 1).otherwise(0)).alias(name) for name, flag in flags.items()],
        ).first().asDict()
        if counts["rows_read"] == 0:
            raise DataContractError("Input CSV contains no event rows")
        counts["rows_valid"] = counts["rows_read"] - counts["rows_rejected"]
        counts["rejected_fraction"] = round(
            counts["rows_rejected"] / counts["rows_read"], 8
        )
        counts.update(
            {
                "source_type": source_type,
                "session_gap_minutes": gap_minutes,
                "input_file": source.name,
                "duplicate_policy": "retain_and_report",
            }
        )
        # Exact duplicates need not be removed. Count them once, separately from bad rows.
        clean = cached.filter(F.col("rejection_reason") == "").drop("rejection_reason")
        counts["exact_duplicate_valid_rows"] = (
            counts["rows_valid"] - clean.select(*RAW_COLUMNS).dropDuplicates().count()
        )
        _write_json(output / "reports" / "data_quality.json", counts)
        if counts["rows_rejected"]:
            (
                cached.filter(F.col("rejection_reason") != "")
                .select(*RAW_COLUMNS, "rejection_reason")
                .write.mode("overwrite")
                .option("header", "true")
                .csv(str(output / "reports" / "rejected_events"))
            )
        if counts["rows_rejected"] / counts["rows_read"] > max_rejected_fraction:
            raise DataContractError(
                f"Data quality gate failed: {counts['rejected_fraction']:.2%} rejected "
                f"> {max_rejected_fraction:.2%} allowed"
            )
        if counts["rows_valid"] == 0:
            raise DataContractError("No valid events available after validation")

        typed = clean.select(
            F.expr("timestamp_millis(timestamp_ms)").alias("event_ts"),
            F.to_date(F.expr("timestamp_millis(timestamp_ms)")).alias("event_date"),
            F.col("visitorid").alias("visitor_id"),
            F.col("event").alias("event_type"),
            F.col("itemid").alias("item_id"),
            F.when(F.col("transactionid") != "", F.col("transactionid")).alias(
                "transaction_id"
            ),
            "timestamp_ms",
        )
        ordering = Window.partitionBy("visitor_id").orderBy(
            "timestamp_ms", "event_type", "item_id", "transaction_id"
        )
        previous_ms = F.lag("timestamp_ms").over(ordering)
        started = F.when(
            previous_ms.isNull() | ((F.col("timestamp_ms") - previous_ms) > gap_minutes * 60000),
            1,
        ).otherwise(0)
        cumulative = ordering.rowsBetween(Window.unboundedPreceding, Window.currentRow)
        numbered = typed.withColumn("session_number", F.sum(started).over(cumulative))
        events = numbered.withColumn(
            "session_id",
            F.concat(
                F.col("visitor_id"), F.lit("-"), F.format_string("%06d", "session_number")
            ),
        )
        facts = events.drop("timestamp_ms", "session_number")
        facts.write.mode("overwrite").parquet(str(output / "processed" / "events.parquet"))

        sessions = events.groupBy("session_id", "visitor_id").agg(
            F.min("event_ts").alias("session_start"),
            F.max("event_ts").alias("session_end"),
            F.round(
                (F.max("timestamp_ms") - F.min("timestamp_ms")) / F.lit(1000.0), 3
            ).alias("duration_seconds"),
            F.count("*").alias("event_count"),
            F.sum(F.when(F.col("event_type") == "view", 1).otherwise(0)).alias(
                "view_events"
            ),
            F.sum(F.when(F.col("event_type") == "addtocart", 1).otherwise(0)).alias(
                "cart_events"
            ),
            F.sum(F.when(F.col("event_type") == "transaction", 1).otherwise(0)).alias(
                "transaction_events"
            ),
            F.countDistinct("transaction_id").alias("order_count"),
        ).withColumn(
            "converted", F.when(F.col("transaction_events") > 0, 1).otherwise(0)
        )
        sessions.write.mode("overwrite").parquet(str(output / "processed" / "sessions.parquet"))

        # Spark SQL marts: compute summary in cluster, never materialize 2.7M rows locally.
        facts.createOrReplaceTempView("event_facts")
        sessions.createOrReplaceTempView("session_facts")
        daily_events = spark.sql("""
            SELECT event_date, COUNT(*) AS event_count,
                   COUNT(DISTINCT visitor_id) AS unique_visitors,
                   SUM(CASE WHEN event_type='view' THEN 1 ELSE 0 END) AS views,
                   SUM(CASE WHEN event_type='addtocart' THEN 1 ELSE 0 END) AS cart_adds,
                   SUM(CASE WHEN event_type='transaction' THEN 1 ELSE 0 END)
                       AS transaction_events
            FROM event_facts GROUP BY event_date
        """)
        daily_sessions = spark.sql("""
            SELECT to_date(session_start) AS session_date,
                   COUNT(*) AS session_count, SUM(converted) AS converted_sessions,
                   ROUND(SUM(converted) * 1.0 / COUNT(*), 4) AS session_conversion_rate,
                   SUM(order_count) AS distinct_orders_within_sessions
            FROM session_facts GROUP BY to_date(session_start)
        """)
        daily_events.write.mode("overwrite").parquet(
            str(output / "analytics" / "daily_events.parquet")
        )
        daily_sessions.write.mode("overwrite").parquet(
            str(output / "analytics" / "daily_session_kpis.parquet")
        )
        totals = sessions.agg(
            F.count("*").alias("sessions"),
            F.sum("converted").alias("converted_sessions"),
        ).first()
        summary = {
            **provenance,
            "max_rejected_fraction": max_rejected_fraction,
            "project": "OmniHealth AI",
            "phase": "1 - distributed clickstream analytics engineering",
            "engine": "pyspark",
            "source_type": source_type,
            "input_file": source.name,
            "data_domain": "retail_ecommerce_clickstream",
            "clinical_or_patient_data_present": False,
            "marketing_channel_data_present": False,
            "conversion_definition": "session_contains_retail_transaction_event",
            "session_gap_minutes": gap_minutes,
            "input_rows": counts["rows_read"],
            "valid_events": counts["rows_valid"],
            "sessions": totals["sessions"],
            "converted_sessions": totals["converted_sessions"],
            "session_conversion_rate": round(totals["converted_sessions"] / totals["sessions"], 4),
            "warning": "Sample-only metrics are not representative of full RetailRocket data"
            if source_type == "synthetic_fixture" else None,
            "generated_at_utc": datetime.now(UTC).isoformat(),
        }
        _write_json(output / "reports" / "pipeline_summary.json", summary)
        return summary
    finally:
        if cached is not None:
            cached.unpersist()
        spark.stop()
