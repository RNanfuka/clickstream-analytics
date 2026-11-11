import pandas as pd
import pytest

from omnihealth import pipeline
from omnihealth.artifacts import write_json


def test_failed_json_serialization_preserves_existing_report(tmp_path):
    target = tmp_path / "report.json"
    write_json(target, {"status": "complete"})
    original = target.read_bytes()
    with pytest.raises(ValueError):
        write_json(target, {"value": float("nan")})
    assert target.read_bytes() == original
    assert list(tmp_path.iterdir()) == [target]


def test_failed_database_build_preserves_existing_database(tmp_path, monkeypatch):
    output = tmp_path / "out"
    pipeline.run_pipeline("data/samples/synthetic_retail_events.csv", output, "synthetic_fixture")
    target = output / "analytics" / "omnihealth.db"
    original = target.read_bytes()
    events = pd.read_csv(output / "processed" / "events.csv")
    events["event_ts"] = pd.to_datetime(events["event_ts"], utc=True)
    sessions = pd.read_csv(output / "processed" / "sessions.csv")
    for field in ("session_start", "session_end"):
        sessions[field] = pd.to_datetime(sessions[field], utc=True)
    monkeypatch.setattr(pipeline, "SQL_MARTS", tmp_path / "missing.sql")
    with pytest.raises(RuntimeError, match="SQL marts not found"):
        pipeline.build_sqlite(events, sessions, target)
    assert target.read_bytes() == original
    assert list(target.parent.iterdir()) == [target]
