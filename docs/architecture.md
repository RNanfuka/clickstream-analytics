# Architecture decisions — Phase 1

## Target audience

Marketing analytics and data solutions consultants who need to translate event data into defendable business metrics, with reproducible engineering and explainable tradeoffs.

## Context and constraints

- Accepted real-data source: RetailRocket anonymized e-commerce events. Included fixtures and generated benchmarks are synthetic and labeled separately.
- Phase 1's transaction proxy is not a patient, HCP, prescription, or medical outcome.
- Original events do not contain channel IDs, campaign spend, impressions, creative, demographics, or marketing exposures.
- Source records may legitimately contain repeated user actions; retain event duplicates and report their frequency instead of silently dropping them.
- Source license is CC BY-NC-SA 4.0; downloaded data must never be included in the repository.

## Component-level flow

1. **Ingestion:** Read required columns, treat visitor/item/transaction IDs as strings, parse milliseconds timestamps as UTC. A representative fixture is deliberately *not* inferred from a 28-row test file.
2. **Validation:** Produce field-specific reasons and a rejection audit. Abort if rejection fraction exceeds threshold. Keep reproducible quality metadata.
3. **Sessionization:** Visitor partition, time order, gap >30 minutes. Deterministic visitor-session ID. No cross-visitor mixing.
4. **Facts:** Write session and event facts. Transaction event count, distinct order count, and converted-session flags use explicitly different definitions.
5. **SQL analytics:** Local path writes SQLite views to make KPI definitions reviewable in plain SQL. Scalable path uses Spark SQL and Parquet tables for similar daily marts.
6. **CI:** Smoke test, unit tests, e2e SQL view checks. Gitignore protects source data.

## Why pandas AND Spark?

The lightweight pandas path is easy to run on a hiring manager's laptop. The Spark path demonstrates scalable, window-based transformations and Parquet output. It is **not** useful to demand a cluster just to run 28 synthetic rows. The optional Spark test should be run in a compatible Java-enabled environment and is not a substitute for full-scale performance testing.

## Deployment boundary

The current Dockerfile packages only the pandas ETL. It is not an API service; there is no healthcare decision-making service or live prediction endpoint yet. We will consider separate API/UI Docker images after model evaluation.

## Business decisions supported

A marketing analyst can audit whether transaction-event sessions changed over time and see upstream activity levels. A consultant can identify what source fields are missing for attribution rather than inferring channels from behavior. Neither the base event table nor the synthetic fixture establishes causal impact of any campaign.

## Known limitations and next hardening tasks

- Pandas reads the full CSV into memory; PySpark is the optional scaling path.
- Output directories are locked during processing. Reports expose running/failed/complete status. Failed runs remove managed analytical results and preserve quality audits; reporting requires complete status. File replacement protects individual JSON and SQLite writes, but the entire directory is not an ACID transaction.
- Visitor sessions based on inactivity are inferred; no true first-party session identifier is provided.
- Session IDs remain stable for the same whole-dataset input, but appending previously unseen earlier events could renumber sessions for a visitor.
- Distinct orders are counted *within* session, not across the whole dataset.
- Day-level SQL marts are descriptive, not predictive or causal.
- Invalid rows are retained in a local audit file: assess privacy handling before processing any sensitive future datasets.
- Spark and pandas output formats differ. Synthetic session-boundary parity tests pass; distributed-cluster performance remains unmeasured.
