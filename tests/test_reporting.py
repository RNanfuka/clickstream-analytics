import json

import pytest

from omnihealth.pipeline import run_pipeline
from omnihealth.reporting import read_report


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
