"""Optional Spark integration test; run with `pip install -e '.[spark,dev]'`."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

pytest.importorskip("pyspark")

from omnihealth.contracts import DataContractError  # noqa: E402
from omnihealth.pipeline import run_pipeline  # noqa: E402
from omnihealth.spark_pipeline import run_spark_pipeline  # noqa: E402

pytestmark = pytest.mark.skipif(
    not os.environ.get("OMNIHEALTH_TEST_SPARK"), reason="Spark test is opt-in"
)


def test_spark_quality_threshold_uses_unrounded_fraction(tmp_path):
    source = tmp_path / "boundary.csv"
    source.write_text(
        "timestamp,visitorid,event,itemid,transactionid\n"
        "1433221200000,a,view,1,\n"
        "1433221260000,a,view,2,\n"
        "bad,a,view,1,\n"
    )
    with pytest.raises(DataContractError, match="quality gate"):
        run_spark_pipeline(source, tmp_path / "spark", "synthetic_fixture",
                           max_rejected_fraction=0.33333333)
    assert (tmp_path / "spark" / "reports" / "rejected_events").exists()
    assert not (tmp_path / "spark" / "processed").exists()


def test_spark_etl_small_fixture(tmp_path):
    sample = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "samples"
        / "synthetic_retail_events.csv"
    )
    result = run_spark_pipeline(sample, tmp_path / "spark", "synthetic_fixture")
    assert result["input_rows"] == 28
    assert result["valid_events"] == 28
    assert result["sessions"] == 8
    assert result["converted_sessions"] == 4
    assert result["session_conversion_rate"] == 0.5
    assert (tmp_path / "spark" / "processed" / "events.parquet").exists()
    assert (tmp_path / "spark" / "analytics" / "daily_session_kpis.parquet").exists()
    quality = json.loads((tmp_path / "spark" / "reports" / "data_quality.json").read_text())
    assert quality["rows_rejected"] == 0


@pytest.mark.parametrize("gap_minutes,expected_sessions", [(30, 3), (5, 4)])
def test_spark_and_pandas_agree_on_session_boundaries_and_duplicates(
    tmp_path, gap_minutes, expected_sessions
):
    # Deliberately unordered: an exact 30-minute gap, a gap of 30m + 1s,
    # another visitor, duplicate actions, and two line items in one order.
    source = tmp_path / "boundaries.csv"
    source.write_text(
        "timestamp,visitorid,event,itemid,transactionid\n"
        "1433224801000,001,view,02,\n"
        "1433221200000,001,view,01,\n"
        "1433223000000,001,transaction,01,order_1\n"
        "1433221260000,002,view,01,\n"
        "1433221200000,001,view,01,\n"
        "1433223000000,001,transaction,02,order_1\n",
        encoding="utf-8",
    )
    pandas_summary = run_pipeline(
        source, tmp_path / "pandas", "synthetic_fixture", gap_minutes=gap_minutes
    )
    spark_summary = run_spark_pipeline(
        source, tmp_path / "spark", "synthetic_fixture", gap_minutes=gap_minutes
    )
    expected = {
        "input_rows": 6,
        "valid_events": 6,
        "sessions": expected_sessions,
        "converted_sessions": 1,
        "session_conversion_rate": round(1 / expected_sessions, 4),
    }
    for key, value in expected.items():
        assert pandas_summary[key] == value, key
        assert spark_summary[key] == value, key

    for engine in ("pandas", "spark"):
        quality = json.loads(
            (tmp_path / engine / "reports" / "data_quality.json").read_text()
        )
        assert quality["rows_rejected"] == 0
        assert quality["exact_duplicate_valid_rows"] == 1
