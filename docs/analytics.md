# Analytical reports and their interpretation

Run `make demo`, then choose a view:

```bash
python -m omnihealth.cli report --output-dir artifacts/demo --view overall
python -m omnihealth.cli report --output-dir artifacts/demo --view funnel --format markdown
python -m omnihealth.cli report --output-dir artifacts/demo --view engagement --format csv
```

| View | Question answered |
|---|---|
| `overall` | How many sessions contained a transaction? |
| `daily_events` | How many actions and distinct visitors occurred on each UTC date? |
| `daily_sessions` | How many sessions started on each UTC date, and how many converted? |
| `stages` | How many sessions contain each type of action, irrespective of order? |
| `funnel` | How many sessions have a view, then a later cart, then a later transaction? |
| `visitors` | How many sessions and actions belong to each observed visitor? |
| `engagement` | How do session counts and conversion vary across 1, 2–5, and 6+ events? |

## Definitions that matter

- Event dates use UTC. Sessions crossing midnight remain intact and are assigned to their start date in session reports.
- The ordered funnel uses strictly increasing timestamps. Equal-time events cannot establish order. It is a session-level path; actions may reference different items.
- The funnel's view-to-purchase denominator is sessions with a view. Overall session conversion uses all sessions. These rates answer different questions.
- Multiple sessions mean multiple observed sessions within this input; they do not establish a customer's full lifetime history.
- Engagement groups are descriptive. A one-event session is not automatically a bounce, and association with purchase is not causation.
- `order_count` is distinct within a session. Summing it does not guarantee global order uniqueness.

## Reproducible larger inputs

```bash
python -m omnihealth.cli generate --output artifacts/synthetic/events.csv --sessions 25000 --seed 42
python -m omnihealth.cli run --input artifacts/synthetic/events.csv --output-dir artifacts/synthetic-run --source-type synthetic_fixture
```

The generator produces four events per session, up to three sessions per visitor, and a configurable artificial conversion probability. It also writes expected totals to a metadata file. The seed reproduces the bytes. The output is useful for performance and correctness checks; it is not evidence about real customers or a suitable basis for claiming predictive accuracy.
