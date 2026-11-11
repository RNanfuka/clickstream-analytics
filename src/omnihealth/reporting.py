"""Read completed SQLite analytics without modifying the source database."""

from __future__ import annotations

import csv
import html
import io
import json
import sqlite3
from pathlib import Path

VIEWS = {
    "overall": "v_overall_kpis",
    "daily_events": "v_daily_events",
    "daily_sessions": "v_daily_session_kpis",
    "stages": "v_session_stage_presence",
    "visitors": "v_visitor_kpis",
    "funnel": "v_ordered_session_funnel",
    "engagement": "v_session_engagement",
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
            cursor = connection.execute(f"SELECT * FROM {VIEWS[view]}")
            columns = [column[0] for column in cursor.description]
            rows = [dict(row) for row in cursor]
    except sqlite3.DatabaseError as exc:
        raise ValueError(f"Unable to read analytics: {exc}") from exc
    return {"report": view, "source_type": summary["source_type"],
            "input_sha256": summary["input_sha256"], "columns": columns, "rows": rows}


def report_csv(report: dict) -> str:
    """Keep source labels on each exported record for downstream reporting."""
    stream = io.StringIO(newline="")
    provenance = {key: report[key] for key in ("source_type", "input_sha256")}
    writer = csv.DictWriter(stream, fieldnames=[*provenance, *report["columns"]])
    writer.writeheader()
    writer.writerows({**provenance, **row} for row in report["rows"])
    return stream.getvalue()


def report_markdown(report: dict) -> str:
    def cell(value):
        if value is None:
            return "—"
        return html.escape(str(value)).replace("|", "\\|").replace("\n", " ")

    label = (
        "Synthetic data: software verification only; not observed customer behavior."
        if report["source_type"] == "synthetic_fixture"
        else "RetailRocket retail data: descriptive observations, not campaign attribution."
    )
    lines = [f"# {report['report'].replace('_', ' ').title()} report", "", label, "",
             f"Input SHA-256: `{report['input_sha256']}`", "",
             "| " + " | ".join(cell(column) for column in report["columns"]) + " |",
             "| " + " | ".join("---" for _ in report["columns"]) + " |"]
    for row in report["rows"]:
        lines.append("| " + " | ".join(cell(row[column]) for column in report["columns"]) + " |")
    lines.extend(["", "Conversion means a session containing a retail transaction. "
                  "The ordered funnel requires strictly increasing timestamps; "
                  "stage presence alone does not establish that sequence.", ""])
    return "\n".join(lines)
