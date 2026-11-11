# Prefer the project environment even when the shell resolves system Python first.
# Override explicitly when needed: make demo PYTHON=/path/to/python
PYTHON ?= $(or $(wildcard .conda/bin/python),$(wildcard .venv/bin/python),python3)

ifneq ($(wildcard .conda/lib/jvm/bin/java),)
export JAVA_HOME ?= $(abspath .conda/lib/jvm)
endif
SPARK_LOCAL_IP ?= 127.0.0.1
PYSPARK_SUBMIT_ARGS ?= --master local[2] --conf spark.sql.shuffle.partitions=2 pyspark-shell
SPARK_ENV = SPARK_LOCAL_IP="$(SPARK_LOCAL_IP)" PYSPARK_SUBMIT_ARGS="$(PYSPARK_SUBMIT_ARGS)" PYSPARK_PYTHON="$(shell $(PYTHON) -c 'import sys; print(sys.executable)')"

.PHONY: install install-spark demo demo-spark test test-spark test-all lint validate report
install:
	$(PYTHON) -m pip install -e '.[dev]'

install-spark:
	$(PYTHON) -m pip install -e '.[dev,spark]'

demo:
	$(PYTHON) -m omnihealth.cli run --input data/samples/synthetic_retail_events.csv --output-dir artifacts/demo --source-type synthetic_fixture

demo-spark:
	$(SPARK_ENV) $(PYTHON) -m omnihealth.cli spark-run --input data/samples/synthetic_retail_events.csv --output-dir artifacts/demo_spark --source-type synthetic_fixture

test:
	$(PYTHON) -m pytest -q

test-spark:
	$(SPARK_ENV) OMNIHEALTH_TEST_SPARK=1 $(PYTHON) -m pytest -q tests/test_spark.py

test-all:
	$(SPARK_ENV) OMNIHEALTH_TEST_SPARK=1 $(PYTHON) -m pytest -q

validate:
	$(PYTHON) -m omnihealth.cli validate --input data/samples/synthetic_retail_events.csv --source-type synthetic_fixture

report:
	$(PYTHON) -m omnihealth.cli report --output-dir artifacts/demo --format markdown

lint:
	$(PYTHON) -m ruff check .
