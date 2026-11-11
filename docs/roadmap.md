# OmniHealth AI — executable milestone roadmap

The following stages are planned, **not complete**.

## Phase 1 — Evidence-first data foundation (implemented)

- Validate RetailRocket event records, manage rejected-row audit and provenance.
- Infer sessions, track conversion proxy, build SQLite and Spark SQL marts.
- Automate tests and containerize the local pipeline.

**Acceptance:** Running the synthetic fixture yields an auditable local SQLite database and reports. A separate real RetailRocket run is needed before reporting real-user findings.

## Phase 2 — Reproducible prediction and evaluation

- Define an honest target: **any retail transaction within seven days following a visitor observation timestamp** (not a prescription or clinician response).
- Build features available **only before** the prediction timestamp: prior view/cart counts, last activity age, distinct items, recent sessions, etc. Avoid using post-cutoff transaction events and any future item metadata.
- Use a carefully designed **time-based** train/validation/test split with embargo/window handling to avoid labels that cross boundaries. Decide whether the deployment unit is a visitor or visitor-snapshot and address repeat-visitor dependence.
- Start with a prior-rate or simple logistic regression baseline; then compare tree-based scikit-learn models. No untested model result in the README.
- Evaluate **PR-AUC**, ROC-AUC (secondary), precision/recall at an operational threshold, calibration/Brier score and drift across time. Include uncertainty/error analysis and business intervention capacity assumptions.
- Save serialized model, feature contract, model card, and reproducible predictions with versioned run settings.

**Acceptance:** Deterministic experiment, time-safe features, explicit baseline comparisons, no leakage, test-set evaluation and clear limitations.

## Phase 3 — Interactive consulting demo

- Serve scored retail sessions/visitors through versioned FastAPI endpoints, with Pydantic validation and Swagger docs.
- Build Streamlit decision cockpit: descriptive engagement, conversion proxy trends, data-quality alerts, score calibration and suggested next actions.
- Optionally generate a **separate, clearly synthetic healthcare marketing event stream** with synthetic channels and campaigns. Never join it to RetailRocket as if it were observed pharma behavior.
- Provide a consulting-style explanation: client's question, available evidence, limitations and recommendations.

**Acceptance:** Integration tests, API request/response contract, metric definitions, separate scenario selector with permanent source labels.

## Phase 4 — Deploy, monitor, and demonstrate

- Docker Compose for ETL, API and dashboard; pin dependency versions and add security checks.
- Deploy Streamlit/FastAPI to an explicitly chosen cloud target, configure secret management and cost limits.
- GitHub Actions deployment gates, health checks, metrics for model quality and service latency, basic alerting.
- Add reproducibility notes, architecture decision records, real RetailRocket EDA, performance profile and interview case study.

**Acceptance:** Public live demonstration (using only licensed/allowed data), documented deployment steps, monitoring evidence and meaningful test coverage.

## Interview talking points

**Business:** "I clarified that purchase events were an observable retail conversion proxy, not campaign-attributed pharmaceutical outcomes."

**Data engineering:** "I implemented schema contracts, rejection thresholds, reproducible sessionization, lineage tags, and equivalent analytic semantics across pandas and Spark SQL."

**Machine learning:** Only after Phase 2: explain time-based validation, class imbalance, threshold selection, calibration, and why post-snapshot activity was excluded.

**Consulting:** "I framed the data limitations explicitly and specified which new instrumentation a client would need for true omnichannel measurement: reliable channel/campaign IDs, consent-aware identifiers, impression events, cost data, and governed conversion definitions."
