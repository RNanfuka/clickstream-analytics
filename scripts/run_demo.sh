#!/usr/bin/env bash
set -euo pipefail
python -m omnihealth.cli run \
  --input data/samples/synthetic_retail_events.csv \
  --output-dir artifacts/demo \
  --source-type synthetic_fixture
