# Phase 1 pandas pipeline image; Spark is a separate optional local installation.
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY data/samples/ ./data/samples/
RUN python -m pip install --no-cache-dir .
RUN mkdir -p /app/artifacts
ENTRYPOINT ["omnihealth"]
CMD ["run", "--input", "data/samples/synthetic_retail_events.csv", "--output-dir", "artifacts/demo", "--source-type", "synthetic_fixture"]
