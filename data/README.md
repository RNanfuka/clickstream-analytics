# Data storage and provenance

- `samples/synthetic_retail_events.csv`: small **hand-authored synthetic retail fixture** in the RetailRocket event schema, versioned only for tests/demonstration. These are **not** actual RetailRocket events or healthcare events.
- `raw/events.csv`: **real RetailRocket events**, which you must download yourself; the entire `raw/` directory is gitignored.
- Generated processed data and reports are written to `artifacts/` (gitignored).

Official source: https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset

**License note:** The Kaggle dataset is marked CC BY-NC-SA 4.0. Review the source terms before distributing data or using it commercially. We do not redistribute the data.

Only `events.csv` is in Phase 1 scope. Item properties and category hierarchy may be added later through validated, point-in-time joins.
