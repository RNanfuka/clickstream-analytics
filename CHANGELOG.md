# Changelog

## 0.5.0 — Verified delivery and measured results

- Verify wheel installation and packaged SQL outside the source directory.
- Use one package-version definition and consistent Python/Java selection for local Spark.
- Run Python 3.11/3.12, Spark, package, and non-root container checks in GitHub CI.
- Record 47 passing tests and reproducible 10,000/100,000-event synthetic benchmarks.
- Publish a results-led README, five milestone summaries, and a step-by-step learning guide.

## 0.4.0 — Behavioral analytics and reports

- Add visitor summaries and engagement groups with reconciled totals.
- Measure strictly ordered view/cart/transaction sequences separately from stage presence.
- Export shareable Markdown with source labels and escaped identifiers.
- Generate seeded synthetic event files with independently known expected metrics.

## 0.3.0 — Reproducible and reliable runs

- Record content fingerprints, processing configuration, and software versions.
- Track completion status, clear stale managed outputs, and prevent concurrent writes.
- Protect individual JSON and SQLite writes with unique temporary files.
- Add read-only JSON and CSV analytics reports with provenance.

## 0.2.0 — Trustworthy input handling

- Reject empty or ambiguous CSV files and preserve identifier text.
- Audit missing values and repeated DataFrame indices safely.
- Compare quality thresholds before rounding percentages in both engines.
- Sort simultaneous transactions deterministically and test midnight behavior.
- Validate command-line options and add a read-only `validate` command.

## 0.1.0 — Phase 1 foundation

- Initialized reproducible Python package and CLI.
- Added RetailRocket event data contract, quality audits and failure threshold.
- Added 30-minute visitor sessionization and explicit retail conversion proxy.
- Built local CSV/SQLite SQL marts and optional Spark/Parquet path.
- Added tests, Docker ETL image, GitHub Actions workflow and documentation.

No machine learning model, healthcare record analysis, real omnichannel attribution, live API, user interface or cloud deployment is claimed in this release.
