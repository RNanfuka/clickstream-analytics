"""Read completed SQLite analytics without modifying the source database."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

VIEWS = {
    "overall": "v_overall_kpis",
    "daily_events": "v_daily_events",
    "daily_sessions": "v_daily_session_kpis",
    "stages": "v_session_stage_presence",
}


def read_report(output_dir: str | Path, view: str = "overall") -> dict:
    if view not in VIEWS:
        raise ValueError(f"Unknown report: {view}")
    output = Path(output_dir)
    status_path = output / "reports" / "run_status.json"
    if not status_path.is_file():
        raise ValueError("Run status is missing; rerun the pipeline before reporting")
    if json.loads(status_path.read_text())["status"] != "complete":
        raise ValueError("Reports require a completed pipeline run")
    summary = json.loads((output / "reports" / "pipeline_summary.json").read_text())
    if summary.get("engine") != "pandas":
        raise ValueError("SQLite reports require the pandas pipeline; Spark outputs are Parquet")
    database = (output / "analytics" / "omnihealth.db").resolve()
    if not database.is_file():
        raise ValueError("Analytics database is missing; rerun the pipeline")
    try:
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            rows = [dict(row) for row in connection.execute(f"SELECT * FROM {VIEWS[view]}")]
    except sqlite3.DatabaseError as exc:
        raise ValueError(f"Unable to read analytics: {exc}") from exc
    return {"report": view, "source_type": summary["source_type"],
            "input_sha256": summary["input_sha256"], "rows": rows}
