# Data contract and metric dictionary

## Upstream schema (`events.csv`)

| Column | Expected representation | Guardrail |
|---|---|---|
| `timestamp` | Unix epoch milliseconds (digits) | Between 2000-01-01 UTC and 2100-01-01 UTC, exclusive upper bound |
| `visitorid` | String-like anonymized ID | Nonblank |
| `event` | Enum | `view`, `addtocart`, `transaction` |
| `itemid` | String-like anonymized ID | Nonblank |
| `transactionid` | String-like order ID | Required for `transaction`, blank for other events |

The broad timestamp validity range is a *technical unit sanity check*, not a claim that the source covers the entire range. The published real data was collected over a roughly 4.5-month period.

## `event_facts`

| Column | Meaning |
|---|---|
| `event_ts` | UTC timestamp parsed from millisecond Unix epoch |
| `event_date` | UTC date (`YYYY-MM-DD`) |
| `visitor_id` | Original anonymized visitor identifier |
| `event_type` | Retail interaction type |
| `item_id` | Original anonymized item identifier |
| `transaction_id` | Order reference on purchase events; otherwise NULL |
| `session_id` | Inferred per-visitor session key |

## `session_facts`

| Column | Meaning |
|---|---|
| `session_id` | Visitor ID + six-digit sequence index |
| `visitor_id` | Anonymized visitor |
| `session_start`, `session_end` | First and last event time in the inferred session, UTC |
| `event_count` | Number of event rows, including duplicates |
| `view_events`, `cart_events`, `transaction_events` | Event counts by action type |
| `order_count` | Distinct non-null transaction IDs within one session |
| `duration_seconds` | Seconds between first and last recorded event; single-event sessions are 0 |
| `converted` | 1 when ≥1 transaction event occurs in the session, otherwise 0 |

No `revenue`, `attributed_conversion`, `campaign_roi`, or `customer_lifetime_value` metric can be computed from Phase 1 events alone.

## SQL views

- `v_daily_events`: daily number of events, distinct visitors, views, carts, transaction event rows.
- `v_daily_session_kpis`: by **session start date**, session count, converted sessions, converted session share, order count within sessions.
- `v_overall_kpis`: all-session summary including average recorded session duration.
- `v_session_stage_presence`: number of sessions containing views/carts/transactions, independently of event sequence.

**Conversion rate** = `converted_sessions / session_count`. This is a *descriptive proxy*. It does not imply exposure, marketing incrementality, attribution or controlled lift.

## Validation policy

`invalid_timestamp`, `missing_visitor_id`, `missing_item_id`, `invalid_event_type`, and `invalid_transaction_id_for_event` can all be reported on a single rejected event. Exact duplicates are retained and counted. Pipeline fails if `rows_rejected / rows_read` exceeds configured threshold (default 0.01). The source type is mandatory in the CLI and saved in summary metadata.
