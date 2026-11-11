# Learn the project one step at a time

Complete one lesson, inspect its output, and explain it in your own words before moving on. The examples use synthetic retail data.

## 1. Events and the business question

Open `data/samples/synthetic_retail_events.csv`. Each row is one recorded action: a view, cart addition, or transaction. Several actions may belong to one visitor's session.

Question: “How many visits contain a purchase?” That requires a definition of a visit and a purchase before a percentage is useful.

**Explain:** What is an event? Why are 28 events not necessarily 28 visits?

## 2. Validation

Run `make validate`. Inspect `rows_read`, `rows_valid`, `rows_rejected`, and the duplicate count. Missing IDs, invalid timestamps, and inconsistent transaction IDs are checked before analytics.

**Explain:** Why preserve an identifier like `001` as text? Why report repeated actions rather than silently deleting them? See [the validation guide](input_validation.md) and `tests/test_quality.py`.

## 3. Sessionization and SQL

Run `make demo`, then open `artifacts/demo/processed/sessions.csv`. The fixture produces 8 sessions, and 4 contain transactions. A gap of exactly 30 minutes stays in one session; a longer gap starts another.

Run `make report`. SQLite provides named views that express metric definitions independently of the display format.

**Explain:** Why does session conversion equal 4/8? Why can two transaction rows represent one order? Check `src/omnihealth/sql/marts.sql`.

## 4. Sequence versus presence

```bash
python -m omnihealth.cli report --output-dir artifacts/demo --view stages
python -m omnihealth.cli report --output-dir artifacts/demo --view funnel
```

Four fixture sessions contain transactions, but only three follow an observed view → later cart → later purchase sequence. Events with identical timestamps do not establish which came first.

**Explain:** Why are 50% session conversion and 37.5% ordered view-to-purchase both correct for this fixture?

## 5. Reliability and testing

Run `make test-all`. The tests exercise boundary times, malformed data, failed reruns, CLI errors, reporting, and Spark/pandas agreement. `run_status.json` records completion; a SHA-256 fingerprint identifies input bytes.

GitHub Actions repeats checks on Linux and verifies package installation and the container. A passing workflow is evidence for those checks, not proof of every possible input or production scale.

**Explain:** What would an incorrect `>= 30 minutes` session boundary change? Why is a previous successful database misleading after a failed rerun?

## 6. Discuss the evidence

Read [the measured results](results/README.md). The 100,000-event timing is a local synthetic pandas measurement. Spark's tests verify correctness on small inputs; there is no cluster benchmark or trained model.

A concise description of the completed work:

> “The project validates retail clickstream events, infers sessions, and exposes SQL metrics with explicit definitions. It includes tests for boundary cases, reproducible input records, and automated package and container checks. The published results use labeled synthetic inputs; real-data modeling is the next stage.”

When discussing your own contribution, describe the changes you understand, the checks you ran, and the decisions you can explain. Use the commit history to revisit each improvement rather than trying to memorize a pitch.
