# Prefer the project environment even when the shell resolves system Python first.
# Override explicitly when needed: make demo PYTHON=/path/to/python
PYTHON ?= $(or $(wildcard .conda/bin/python),$(wildcard .venv/bin/python),python3)

.PHONY: install install-spark demo demo-spark test test-spark lint
install:
	$(PYTHON) -m pip install -e '.[dev]'

install-spark:
	$(PYTHON) -m pip install -e '.[dev,spark]'

demo:
	$(PYTHON) -m omnihealth.cli run --input data/samples/synthetic_retail_events.csv --output-dir artifacts/demo --source-type synthetic_fixture

demo-spark:
	$(PYTHON) -m omnihealth.cli spark-run --input data/samples/synthetic_retail_events.csv --output-dir artifacts/demo_spark --source-type synthetic_fixture

test:
	$(PYTHON) -m pytest -q

test-spark:
	OMNIHEALTH_TEST_SPARK=1 $(PYTHON) -m pytest -q tests/test_spark.py

lint:
	$(PYTHON) -m ruff check .
