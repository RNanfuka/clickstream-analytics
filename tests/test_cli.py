from __future__ import annotations

import json
import subprocess
import sys

import pytest


def cli(*arguments):
    return subprocess.run(
        [sys.executable, "-m", "omnihealth.cli", *arguments],
        capture_output=True, text=True,
    )


@pytest.mark.parametrize("option,value", [
    ("--gap-minutes", "0"), ("--limit-rows", "-1"),
    ("--max-rejected-fraction", "nan"), ("--max-rejected-fraction", "2"),
])
def test_invalid_options_fail_before_creating_outputs(tmp_path, option, value):
    output = tmp_path / "out"
    result = cli("run", "--input", "absent.csv", "--output-dir", str(output),
                 "--source-type", "synthetic_fixture", option, value)
    assert result.returncode == 2
    assert "error:" in result.stderr
    assert "Traceback" not in result.stderr
    assert not output.exists()


def test_missing_input_has_actionable_error(tmp_path):
    result = cli("run", "--input", "absent.csv", "--output-dir", str(tmp_path / "out"),
                 "--source-type", "synthetic_fixture")
    assert result.returncode == 2
    assert "Unable to read input CSV" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_produces_parseable_summary(tmp_path):
    result = cli("run", "--input", "data/samples/synthetic_retail_events.csv",
                 "--output-dir", str(tmp_path / "out"), "--source-type", "synthetic_fixture")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["sessions"] == 8


def test_validate_reports_failure_without_creating_analytics(tmp_path):
    source = tmp_path / "input.csv"
    source.write_text("timestamp,visitorid,event,itemid,transactionid\nbad,a,view,1,\n")
    result = cli("validate", "--input", str(source), "--source-type", "synthetic_fixture")
    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["rows_rejected"] == 1
    assert report["validation_passed"] is False
    assert list(tmp_path.iterdir()) == [source]


def test_validate_reports_success():
    result = cli("validate", "--input", "data/samples/synthetic_retail_events.csv",
                 "--source-type", "synthetic_fixture")
    assert result.returncode == 0
    assert json.loads(result.stdout)["validation_passed"] is True
