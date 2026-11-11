# Inspecting data before a run

Start with an activated project environment, then run:

```bash
python -m omnihealth.cli validate \
  --input data/samples/synthetic_retail_events.csv \
  --source-type synthetic_fixture
```

This command reads the CSV and prints a JSON quality report without creating event facts or a database. Exit code 0 means the quality gate passed; 2 means invalid arguments, an unreadable input, or a failed gate. A failed gate still prints its quality report. Reading errors go to stderr.

Required columns are `timestamp`, `visitorid`, `event`, `itemid`, and `transactionid`. Empty files, duplicate column names, and excess fields that would shift identifiers into an index are rejected. Identifier text such as `001` and `NA` stays intact. Timestamps must be integer milliseconds between 2000 and 2100 UTC.

The default rejection threshold is 1%. `--max-rejected-fraction 0.05` allows up to 5% rejected rows. The comparison uses the unrounded fraction; the displayed fraction is rounded for readability. A threshold of 1 still cannot make a dataset with no valid events usable.

Use `--limit-rows 10000` for an initial inspection of a large file. This checks only the beginning of the file and is not a representative sample or a full validation.

Session processing sorts equal-time events by visitor, event type, item, and transaction ID. A gap of exactly 30 minutes stays in the same session; a longer gap starts another session. Midnight alone does not start a new session.
