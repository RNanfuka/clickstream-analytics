import csv
import io
import json

import pytest

from omnihealth.pipeline import run_pipeline
from omnihealth.reporting import read_report, report_csv


@pytest.fixture
def completed_run(tmp_path):
    output = tmp_path / "out"
    run_pipeline("data/samples/synthetic_retail_events.csv", output, "synthetic_fixture")
    return output


def test_report_reads_metrics_and_provenance_without_mutating_database(completed_run):
    database = completed_run / "analytics" / "omnihealth.db"
    original = database.read_bytes()
    report = read_report(completed_run)
    assert report["source_type"] == "synthetic_fixture"
    assert len(report["input_sha256"]) == 64
    assert report["rows"][0]["session_count"] == 8
    assert report["rows"][0]["session_conversion_rate"] == 0.5
    assert database.read_bytes() == original


def test_report_refuses_failed_run_and_unknown_view(completed_run):
    with pytest.raises(ValueError, match="Unknown report"):
        read_report(completed_run, "event_facts; DROP TABLE event_facts")
    (completed_run / "reports" / "run_status.json").write_text(json.dumps({"status": "failed"}))
    with pytest.raises(ValueError, match="completed"):
        read_report(completed_run)


def test_missing_run_does_not_create_database(tmp_path):
    with pytest.raises(ValueError, match="status is missing"):
        read_report(tmp_path)
    assert not list(tmp_path.iterdir())


def test_csv_export_keeps_source_labels_and_metric_values(completed_run):
    report = read_report(completed_run, "daily_events")
    rows = list(csv.DictReader(io.StringIO(report_csv(report))))
    assert len(rows) == 1
    assert rows[0]["event_count"] == "28"
    assert rows[0]["source_type"] == "synthetic_fixture"
    assert rows[0]["input_sha256"] == report["input_sha256"]


def test_visitor_metrics_reconcile_with_session_and_event_totals(completed_run):
    rows = read_report(completed_run, "visitors")["rows"]
    assert len(rows) == 5
    assert sum(row["session_count"] for row in rows) == 8
    assert sum(row["event_count"] for row in rows) == 28
    assert sum(row["converted_sessions"] for row in rows) == 4
    for row in rows:
        assert row["first_observed_session"] <= row["last_observed_event"]
        assert (row["observed_session_type"] == "multiple_sessions") == (row["session_count"] > 1)
