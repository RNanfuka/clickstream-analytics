"""Command-line entry point for Phase 1 ETL."""

from __future__ import annotations

import argparse
import json

from omnihealth.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="OmniHealth AI ETL and analytics")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="Run validated pandas clickstream ETL")
    run.add_argument("--input", required=True, help="Path to events.csv")
    run.add_argument("--output-dir", required=True, help="Destination for generated artifacts")
    run.add_argument(
        "--source-type", required=True, choices=["retailrocket", "synthetic_fixture"]
    )
    run.add_argument("--gap-minutes", type=int, default=30)
    run.add_argument("--max-rejected-fraction", type=float, default=0.01)
    run.add_argument("--limit-rows", type=int, default=None)
    spark = subparsers.add_parser("spark-run", help="Run distributed PySpark ETL to Parquet")
    spark.add_argument("--input", required=True, help="Path to events.csv")
    spark.add_argument("--output-dir", required=True, help="Destination for generated artifacts")
    spark.add_argument(
        "--source-type", required=True, choices=["retailrocket", "synthetic_fixture"]
    )
    spark.add_argument("--gap-minutes", type=int, default=30)
    spark.add_argument("--max-rejected-fraction", type=float, default=0.01)
    args = parser.parse_args()
    if args.command == "run":
        summary = run_pipeline(
            input_path=args.input,
            output_dir=args.output_dir,
            source_type=args.source_type,
            gap_minutes=args.gap_minutes,
            max_rejected_fraction=args.max_rejected_fraction,
            limit_rows=args.limit_rows,
        )
        print(json.dumps(summary, indent=2))
    elif args.command == "spark-run":
        from omnihealth.spark_pipeline import run_spark_pipeline

        summary = run_spark_pipeline(
            input_path=args.input,
            output_dir=args.output_dir,
            source_type=args.source_type,
            gap_minutes=args.gap_minutes,
            max_rejected_fraction=args.max_rejected_fraction,
        )
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
