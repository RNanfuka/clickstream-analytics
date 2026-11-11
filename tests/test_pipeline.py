from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from omnihealth.contracts import DataContractError
from omnihealth.pipeline import run_pipeline

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "samples" / "synthetic_retail_events.csv"


def test_end_to_end_demo_creates_analytics_and_provenance(tmp_path):
    summary = run_pipeline(SAMPLE, tmp_path / "result", "synthetic_fixture")
    assert summary["input_rows"] == 28
    assert summary["valid_events"] == 28
    assert summary["sessions"] == 8
    assert summary["converted_sessions"] == 4
    assert summary["source_type"] == "synthetic_fixture"
    assert summary["marketing_channel_data_present"] is False
    assert summary["clinical_or_patient_data_present"] is False
    assert (tmp_path / "result" / "processed" / "events.csv").exists()
    assert (tmp_path / "result" / "processed" / "sessions.csv").exists()
    quality = json.loads((tmp_path / "result" / "reports" / "data_quality.json").read_text())
    assert quality["rows_rejected"] == 0

    with sqlite3.connect(tmp_path / "result" / "analytics" / "omnihealth.db") as db:
        total_events = db.execute("SELECT SUM(event_count) FROM v_daily_events").fetchone()[0]
        count, converted, rate = db.execute(
            "SELECT session_count, converted_sessions, session_conversion_rate FROM v_overall_kpis"
        ).fetchone()
        assert total_events == 28
        assert count == summary["sessions"]
        assert converted == summary["converted_sessions"]
        assert rate == summary["session_conversion_rate"]
        assert db.execute("SELECT COUNT(*) FROM v_daily_session_kpis").fetchone()[0] == 1
    result = pd.read_csv(tmp_path / "result" / "processed" / "sessions.csv")
    assert len(result) == count


def test_quality_gate_fails_and_writes_report(tmp_path):
    bad_data = tmp_path / "bad.csv"
    bad_data.write_text(
        "timestamp,visitorid,event,itemid,transactionid\n"
        "1433221200000,a,view,1,\n"
        "xxx,a,view,1,\n",
        encoding="utf-8",
    )
    with pytest.raises(DataContractError, match="Data quality gate failed"):
        run_pipeline(bad_data, tmp_path / "out", "synthetic_fixture")
    assert (tmp_path / "out" / "reports" / "data_quality.json").exists()
    assert (tmp_path / "out" / "reports" / "rejected_events.csv").exists()
    assert not (tmp_path / "out" / "analytics" / "omnihealth.db").exists()


def test_reject_invalid_source_type(tmp_path):
    with pytest.raises(ValueError, match="source_type"):
        run_pipeline(SAMPLE, tmp_path / "out", "healthcare_records")


def test_repeatable_pipeline_results(tmp_path):
    run_pipeline(SAMPLE, tmp_path / "first", "synthetic_fixture")
    run_pipeline(SAMPLE, tmp_path / "second", "synthetic_fixture")
    for filename in ("events.csv", "sessions.csv"):
        assert (tmp_path / "first" / "processed" / filename).read_bytes() == (
            tmp_path / "second" / "processed" / filename
        ).read_bytes()


def test_allowed_rejections_are_audited(tmp_path):
    source = tmp_path / "partial.csv"
    source.write_text(
        "timestamp,visitorid,event,itemid,transactionid\n"
        "1433221200000,a,view,1,\n"
        "not-a-time,a,view,1,\n",
        encoding="utf-8",
    )
    summary = run_pipeline(
        source, tmp_path / "out", "synthetic_fixture", max_rejected_fraction=0.5
    )
    assert summary["valid_events"] == 1
    assert (tmp_path / "out" / "reports" / "rejected_events.csv").exists()
    assert (tmp_path / "out" / "analytics" / "omnihealth.db").exists()


def test_quality_threshold_uses_unrounded_fraction(tmp_path):
    source = tmp_path / "boundary.csv"
    source.write_text(
        "timestamp,visitorid,event,itemid,transactionid\n"
        "1433221200000,a,view,1,\n"
        "1433221260000,a,view,2,\n"
        "bad,a,view,1,\n"
    )
    with pytest.raises(DataContractError, match="quality gate"):
        run_pipeline(source, tmp_path / "out", "synthetic_fixture",
                     max_rejected_fraction=0.33333333)
