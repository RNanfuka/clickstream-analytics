# Measured verification results

The [machine-readable record](verification.json) was generated on November 11, 2026. It contains input fingerprints, the source-code fingerprint, software versions, raw durations, and test totals. All data in this record is **synthetic**.

## Correctness

The full local suite passed **47 tests, with zero failures or skips**, including four Spark cases. The hand-authored fixture produced 28 events, 5 visitors, 8 sessions, and 4 converted sessions. Its ordered funnel contains 8 viewing sessions, 4 sessions with a later cart, and 3 with a later purchase.

The 50% session conversion and 37.5% ordered view-to-purchase rates differ because the definitions differ. These are fixture checks, not estimates of customer behavior.

## Pandas timings

| Generated events | Expected sessions | Runs | Median elapsed time |
|---:|---:|---:|---:|
| 10,000 | 2,500 | 3 | 1.195 seconds |
| 100,000 | 25,000 | 3 | 12.551 seconds |

Measured on macOS ARM64 with 12 logical CPUs, Python 3.11.18, pandas 2.3.3, and NumPy 2.4.6. Runs include CSV reading, validation, fingerprinting, sessionization, CSV/SQLite writes, and run reports. Data generation is excluded. There was no dedicated warm-up and filesystem caching was uncontrolled. The expected event, session, and conversion counts were checked after every run.

These are local engineering measurements, not production throughput guarantees, distributed Spark measurements, or full RetailRocket performance claims.

## Reproduce

From the activated development environment:

```bash
PYTEST_ADDOPTS="--junitxml=artifacts/verification/pytest.xml" make test-all
python scripts/measure_results.py --junit artifacts/verification/pytest.xml
```

The script uses seed 42, 2,500 and 25,000 sessions, and three runs per size. It refuses to publish evidence from a JUnit result containing failures, errors, or skipped tests. It overwrites generated benchmark files in `artifacts/measurements/`; use `--work-dir` to choose another destination. Timings will vary between runs and machines.
