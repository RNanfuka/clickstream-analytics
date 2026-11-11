# Reproducing and inspecting a run

Every successful summary includes an input SHA-256 fingerprint, input byte size, software versions, engine, row limit, rejection threshold, and session gap. The fingerprint covers the entire input file even when `--limit-rows` processes only a prefix. It detects content changes; it does not prove the source label is correct.

```bash
make demo
python -m omnihealth.cli report --output-dir artifacts/demo
python -m omnihealth.cli report --output-dir artifacts/demo --view daily_events --format csv
```

JSON and CSV reports retain the source type and input fingerprint. SQLite is opened read-only. Available reports are listed by `python -m omnihealth.cli report --help`.

## Run lifecycle

`reports/run_status.json` records `running`, `failed`, or `complete`. A rerun clears the pipeline's managed outputs before processing. If it fails, partial facts and old success summaries are removed; the current quality report and rejected rows remain available when validation reached that stage. Keep separate output directories if previous results must be retained.

An exclusive `.omnihealth.lock` prevents simultaneous writes to one destination. An interrupted process may leave a lock and a running status. Confirm the process has stopped before removing that lock and rerunning. An input file cannot live inside its output directory.

JSON and SQLite files use unique temporary files and replacement. This prevents readers from seeing partially serialized individual files, but it does not make a whole run transactional. The report command requires completed status. Spark writes Parquet directories and does not support the SQLite report command.

Input files should remain unchanged during a run. A fixed input, configuration, and software environment should reproduce analytical values. Run timestamps and measured durations will differ.

## Local commands

`make validate`, `make demo`, and `make report` inspect the fixture, process it, and show its results. `make test-all` runs the full suite including Spark. The Makefile prefers the project environment, locates its Java installation, and supplies the same Python executable to Spark workers. Local Spark commands default to two workers and two shuffle partitions. Explicit `PYTHON`, `JAVA_HOME`, and `PYSPARK_SUBMIT_ARGS` overrides are respected.
