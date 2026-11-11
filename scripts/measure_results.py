"""Generate audited fixture results and repeatable, explicitly synthetic timing evidence."""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import statistics
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

from omnihealth.artifacts import write_json
from omnihealth.cli import positive_integer
from omnihealth.pipeline import run_pipeline
from omnihealth.reporting import read_report
from omnihealth.synthetic import generate_events


def measure(work_dir: Path, session_counts: list[int], repeats: int, junit: Path) -> dict:
    repository = Path(__file__).resolve().parents[1]
    fixture = run_pipeline(repository / "data/samples/synthetic_retail_events.csv",
                           work_dir / "fixture", "synthetic_fixture")
    source_digest = hashlib.sha256()
    for source in sorted((repository / "src/omnihealth").rglob("*")):
        if source.suffix in {".py", ".sql"}:
            source_digest.update(str(source.relative_to(repository)).encode())
            source_digest.update(source.read_bytes())
    benchmarks = []
    for sessions in session_counts:
        source = work_dir / f"synthetic-{sessions}.csv"
        expected = generate_events(source, sessions=sessions, seed=42, overwrite=True)
        durations = []
        for repeat in range(repeats):
            started = time.perf_counter()
            actual = run_pipeline(source, work_dir / f"run-{sessions}-{repeat}", "synthetic_fixture")
            durations.append(time.perf_counter() - started)
            assert actual["valid_events"] == expected["events"]
            for key in ("sessions", "converted_sessions", "session_conversion_rate"):
                assert actual[key] == expected[key], key
        median = statistics.median(durations)
        benchmarks.append({
            "source_type": "synthetic_fixture", "seed": 42,
            "events": expected["events"], "sessions": sessions,
            "converted_sessions": expected["converted_sessions"],
            "input_sha256": actual["input_sha256"],
            "elapsed_seconds": [round(value, 6) for value in durations],
            "median_seconds": round(median, 6),
            "median_events_per_second": round(expected["events"] / median),
        })
    suites = ET.parse(junit).getroot().findall("testsuite")
    assert suites, "JUnit results are required"
    tests = {key: sum(int(suite.get(key, "0")) for suite in suites)
             for key in ("tests", "failures", "errors", "skipped")}
    assert tests["failures"] == tests["errors"] == tests["skipped"] == 0
    return {
        "measured_at_utc": datetime.now(UTC).isoformat(),
        "source_tree_sha256": source_digest.hexdigest(),
        "data_scope": "Synthetic fixture and seeded synthetic benchmarks only",
        "method": "Sequential pandas runs including validation, SHA-256, CSV, SQLite, and reports. "
                  "Generation excluded; no dedicated warm-up; local filesystem cache uncontrolled.",
        "machine": {"system": platform.system(), "architecture": platform.machine(),
                    "logical_cpus": os.cpu_count()},
        "tests": tests,
        "fixture": fixture,
        "reports": {name: read_report(work_dir / "fixture", name)["rows"]
                    for name in ("overall", "daily_events", "funnel", "engagement")},
        "benchmarks": benchmarks,
        "limitations": ["Not real RetailRocket observations", "Not a distributed Spark benchmark",
                        "Timing varies with hardware, software versions, and filesystem caches",
                        "No machine learning model has been trained or evaluated"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=Path("artifacts/measurements"))
    parser.add_argument("--sessions", type=positive_integer, nargs="+", default=[2500, 25000])
    parser.add_argument("--repeats", type=positive_integer, default=3)
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("docs/results/verification.json"))
    args = parser.parse_args()
    payload = measure(args.work_dir, args.sessions, args.repeats, args.junit)
    write_json(args.output, payload)
    for benchmark in payload["benchmarks"]:
        print(f"{benchmark['events']:,} synthetic events: {benchmark['median_seconds']:.3f}s median")
    print(f"Evidence saved to {args.output}")
