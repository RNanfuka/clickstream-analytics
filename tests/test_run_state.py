import json

import pytest

from omnihealth.contracts import DataContractError
from omnihealth.pipeline import run_pipeline

SAMPLE = "data/samples/synthetic_retail_events.csv"


def test_failed_rerun_cannot_leave_old_successful_results(tmp_path):
    output = tmp_path / "out"
    run_pipeline(SAMPLE, output, "synthetic_fixture")
    bad = tmp_path / "bad.csv"
    bad.write_text("timestamp,visitorid,event,itemid,transactionid\nbad,a,view,1,\n")
    with pytest.raises(DataContractError, match="quality gate"):
        run_pipeline(bad, output, "synthetic_fixture")
    assert not (output / "analytics" / "omnihealth.db").exists()
    assert not (output / "reports" / "pipeline_summary.json").exists()
    assert (output / "reports" / "rejected_events.csv").exists()
    status = json.loads((output / "reports" / "run_status.json").read_text())
    assert status["status"] == "failed"
    run_pipeline(SAMPLE, output, "synthetic_fixture")
    assert not (output / "reports" / "rejected_events.csv").exists()
    assert json.loads((output / "reports" / "run_status.json").read_text())["status"] == "complete"


def test_input_inside_output_is_protected(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text("important input")
    with pytest.raises(ValueError, match="outside"):
        run_pipeline(source, tmp_path, "synthetic_fixture")
    assert source.read_text() == "important input"


def test_existing_output_lock_prevents_concurrent_writes(tmp_path):
    lock = tmp_path / ".omnihealth.lock"
    lock.write_text("owned by another run")
    with pytest.raises(ValueError, match="locked"):
        run_pipeline(SAMPLE, tmp_path, "synthetic_fixture")
    assert lock.read_text() == "owned by another run"
