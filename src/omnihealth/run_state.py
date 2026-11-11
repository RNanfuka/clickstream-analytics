"""Track run completion and prevent stale or partially written analytical results."""

from __future__ import annotations

import json
import shutil
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from omnihealth.contracts import DataContractError

FACTS = (
    "processed/events.csv", "processed/sessions.csv", "analytics/omnihealth.db",
    "processed/events.parquet", "processed/sessions.parquet",
    "analytics/daily_events.parquet", "analytics/daily_session_kpis.parquet",
    "reports/pipeline_summary.json",
)
AUDITS = ("reports/data_quality.json", "reports/rejected_events.csv", "reports/rejected_events")


def _remove_managed(output: Path, names: tuple[str, ...]) -> None:
    for name in names:
        path = output / name
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)


@contextmanager
def pipeline_run(input_path: str | Path, output_dir: str | Path):
    source, output = Path(input_path).resolve(), Path(output_dir).resolve()
    if not source.is_file():
        raise DataContractError(f"Unable to read input CSV: {source.name} does not exist")
    if source.is_relative_to(output):
        raise ValueError("Input must be outside the output directory")
    for name in ("reports", "processed", "analytics"):
        if (output / name).is_symlink():
            raise ValueError("Output subdirectories must not be symbolic links")
    output.mkdir(parents=True, exist_ok=True)
    lock = output / ".omnihealth.lock"
    try:
        handle = lock.open("x")
    except FileExistsError as exc:
        raise ValueError(f"Output directory is locked by another run: {output}") from exc
    handle.close()
    status_path = output / "reports" / "run_status.json"
    started = datetime.now(UTC).isoformat()

    def save(status, **extra):
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(json.dumps({
            "status": status, "started_at_utc": started,
            "updated_at_utc": datetime.now(UTC).isoformat(), **extra,
        }, indent=2) + "\n")

    try:
        _remove_managed(output, FACTS + AUDITS)
        save("running")
        try:
            yield
        except Exception as exc:
            _remove_managed(output, FACTS)
            save("failed", error_type=type(exc).__name__, error=str(exc))
            raise
        else:
            save("complete")
    finally:
        lock.unlink(missing_ok=True)
