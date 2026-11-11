# Project milestones

Each milestone is a tagged, testable increment. Tags mark completed capabilities, not elapsed development time or production deployments.

| Version | Milestone | Acceptance evidence |
|---|---|---|
| v0.1.0 | Initial analytics foundation | Synthetic fixture, pandas and Spark paths, SQL marts, baseline tests and CI |
| v0.2.0 | Trustworthy input handling | Explicit CSV errors, nullable-value auditing, exact quality thresholds, deterministic sessions, validation CLI |
| v0.3.0 | Reproducible and reliable runs | Input hashes, software versions, run status, output locks, isolated file writes, JSON and CSV reports |
| v0.4.0 | Behavioral analytics and shareable reports | Visitor and engagement summaries, strictly ordered session funnel, Markdown exports, seeded synthetic generator |
| v0.5.0 | Verified delivery and measured results | 47 passing tests, Python 3.11/3.12 CI, installed-wheel check, non-root Docker demo, documented 10k/100k-event benchmarks |

The five milestones complete the current engineering and descriptive analytics scope. Future model training, API/dashboard development, and cloud deployment remain on the [roadmap](roadmap.md). Release notes are stored in [`.github/release-notes`](../.github/release-notes/).

## Learning sequence

1. Explain an event, a session, and the conversion definition.
2. Run `validate` and explain why a row was rejected.
3. Run the pipeline and reconcile the CSV facts with SQL metrics.
4. Compare pandas and Spark behavior on boundary cases.
5. Use the documented evidence to discuss what has and has not been measured.
