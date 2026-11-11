"""Phase 1 pandas ETL -> audited event/session facts -> SQLite SQL marts."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path

import pandas as pd

from omnihealth.contracts import DataContractError, read_events
from omnihealth.quality import validate_events
from omnihealth.sessions import sessionize

SQL_MARTS = files("omnihealth").joinpath("sql/marts.sql")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_sqlite(events: pd.DataFrame, sessions: pd.DataFrame, database_path: Path) -> None:
    """Rebuild analytics database atomically in a temporary local file."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = database_path.with_suffix(".tmp.db")
    if temp_path.exists():
        temp_path.unlink()
    try:
        with sqlite3.connect(temp_path) as connection:
            # Explicit types and values for simple portable SQLite usage.
            event_records = events.copy()
            event_records["event_ts"] = event_records["event_ts"].dt.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            session_records = sessions.copy()
            for column in ("session_start", "session_end"):
                session_records[column] = session_records[column].dt.strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                )
            event_records.to_sql("event_facts", connection, if_exists="replace", index=False)
            session_records.to_sql("session_facts", connection, if_exists="replace", index=False)
            connection.execute("CREATE INDEX idx_events_date ON event_facts (event_date)")
            connection.execute("CREATE INDEX idx_events_session ON event_facts (session_id)")
            connection.execute("CREATE INDEX idx_sessions_start ON session_facts (session_start)")
            if not SQL_MARTS.is_file():
                raise RuntimeError(f"SQL marts not found: {SQL_MARTS}")
            connection.executescript(SQL_MARTS.read_text(encoding="utf-8"))
            check = connection.execute("PRAGMA integrity_check").fetchone()[0]
            if check != "ok":
                raise RuntimeError(f"SQLite integrity check failed: {check}")
        temp_path.replace(database_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def run_pipeline(
    input_path: str | Path,
    output_dir: str | Path,
    source_type: str,
    gap_minutes: int = 30,
    max_rejected_fraction: float = 0.01,
    limit_rows: int | None = None,
) -> dict:
    """Run local ETL. The supplied source provenance is written in every run manifest."""
    if source_type not in {"retailrocket", "synthetic_fixture"}:
        raise ValueError("source_type must be 'retailrocket' or 'synthetic_fixture'")
    if not 0 <= max_rejected_fraction <= 1:
        raise ValueError("max_rejected_fraction must be between 0 and 1")
    if gap_minutes <= 0:
        raise ValueError("gap_minutes must be positive")

    output = Path(output_dir)
    quality_dir = output / "reports"
    raw = read_events(str(input_path), limit_rows)
    if raw.empty:
        raise DataContractError("Input CSV contains no event rows")
    validation = validate_events(raw)
    report = dict(validation.report)
    report["source_type"] = source_type
    report["session_gap_minutes"] = gap_minutes
    report["input_file"] = Path(input_path).name
    _write_json(quality_dir / "data_quality.json", report)
    if not validation.rejected.empty:
        quality_dir.mkdir(parents=True, exist_ok=True)
        validation.rejected.to_csv(quality_dir / "rejected_events.csv", index=False)
    if report["rows_rejected"] / report["rows_read"] > max_rejected_fraction:
        raise DataContractError(
            "Data quality gate failed: "
            f"{report['rejected_fraction']:.2%} rejected > {max_rejected_fraction:.2%} allowed. "
            f"See {quality_dir / 'data_quality.json'}."
        )
    if validation.valid.empty:
        raise DataContractError("No valid events available after validation")

    events, sessions = sessionize(validation.valid, gap_minutes)
    processed_dir = output / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    events.to_csv(processed_dir / "events.csv", index=False)
    sessions.to_csv(processed_dir / "sessions.csv", index=False)
    build_sqlite(events, sessions, output / "analytics" / "omnihealth.db")

    summary = {
        "project": "OmniHealth AI",
        "phase": "1 - clickstream analytics engineering",
        "source_type": source_type,
        "input_file": Path(input_path).name,
        "data_domain": "retail_ecommerce_clickstream",
        "clinical_or_patient_data_present": False,
        "marketing_channel_data_present": False,
        "conversion_definition": "session_contains_retail_transaction_event",
        "session_gap_minutes": gap_minutes,
        "input_rows": int(report["rows_read"]),
        "valid_events": len(events),
        "sessions": len(sessions),
        "converted_sessions": int(sessions["converted"].sum()),
        "session_conversion_rate": round(float(sessions["converted"].mean()), 4),
        "warning": "Sample-only metrics are not representative of full RetailRocket data"
        if source_type == "synthetic_fixture" or limit_rows is not None
        else None,
        "generated_at_utc": datetime.now(UTC).isoformat(),
    }
    _write_json(quality_dir / "pipeline_summary.json", summary)
    return summary
