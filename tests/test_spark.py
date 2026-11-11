"""Optional Spark integration test; run with `pip install -e '.[spark,dev]'`."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

pytest.importorskip("pyspark")

from omnihealth.spark_pipeline import run_spark_pipeline  # noqa: E402


@pytest.mark.skipif(not os.environ.get("OMNIHEALTH_TEST_SPARK"), reason="Spark test is opt-in")
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
    assert result["sessions"] >= 5
    assert (tmp_path / "spark" / "processed" / "events.parquet").exists()
    assert (tmp_path / "spark" / "analytics" / "daily_session_kpis.parquet").exists()
    quality = json.loads((tmp_path / "spark" / "reports" / "data_quality.json").read_text())
    assert quality["rows_rejected"] == 0
