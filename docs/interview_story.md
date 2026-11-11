# An interview-ready Phase 1 story (only claim what has been completed)

**Situation:** Marketing and customer-engagement teams often work with clickstream logs but need reproducible definitions before they can trust conversion KPIs or build predictive models.

**Task:** I designed OmniHealth AI as a data-solutions portfolio system. The goal is to demonstrate how to transform raw event data into validated, interpretable analytics, with a future pathway to healthcare-inspired omnichannel scenarios.

**Actions:** I chose public RetailRocket e-commerce events rather than pretending to have pharmaceutical records. I documented the exact data contract, implemented typed ingestion and rejection auditing, inferred 30-minute inactivity sessions, exposed explicit transaction-presence KPIs in SQL, and added portable tests, CI and containerization. I designed an optional Spark execution path that writes Parquet and verified its synthetic-fixture metrics and session-boundary behavior against pandas. Performance at scale remains unmeasured.

**Result so far:** The local end-to-end implementation successfully processes the **synthetic retail verification fixture** and produces event facts, session facts, an SQLite analytics database and lineage-aware quality reports. The tests pass. This proves the engineering workflow works on the fixture, **not** that a model improves outcomes or that any pharma campaign has been evaluated.

**Consulting judgment:** The key distinction is that a retail purchase event is not a marketing-attributed, clinical, prescription or HCP engagement event. I would ask a client for consent-aware channel/campaign identifiers, impression and spend data, governance definitions, and real conversion labels before implementing omnichannel attribution.

## Anticipate these technical follow-ups

**Why not randomly split the data?** Time leakage and repeated visitors can inflate model metrics. Phase 2 will use time-based evaluation with a prediction timestamp and a clearly defined horizon.

**Why count transaction IDs as well as events?** An order may generate multiple item-level transaction records. Event count and distinct orders answer different questions.

**Why retain duplicates?** Identical log records can be repeated actions. Unexplained deduplication would corrupt the event history. We report exact duplicates and make the policy explicit.

**What is the biggest remaining weakness?** The initial source lacks marketing channel or healthcare context, so it cannot support pharmaceutical attribution. We treat that as a data requirement, not a modeling trick.
