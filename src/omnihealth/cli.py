"""Command-line entry point for Phase 1 ETL."""

from __future__ import annotations

import argparse
import json

from omnihealth import __version__
from omnihealth.contracts import DataContractError, read_events
from omnihealth.pipeline import run_pipeline
from omnihealth.quality import validate_events


def positive_integer(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def fraction(value: str) -> float:
    number = float(value)
    if not 0 <= number <= 1:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OmniHealth AI ETL and analytics")
    parser.add_argument("--version", action="version", version=f"OmniHealth {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="Inspect CSV quality without writing outputs")
    validate.add_argument("--input", required=True)
    validate.add_argument("--source-type", required=True,
                          choices=["retailrocket", "synthetic_fixture"])
    validate.add_argument("--limit-rows", type=positive_integer, default=None)
    validate.add_argument("--max-rejected-fraction", type=fraction, default=0.01)
    run = subparsers.add_parser("run", help="Run validated pandas clickstream ETL")
    run.add_argument("--input", required=True, help="Path to events.csv")
    run.add_argument("--output-dir", required=True, help="Destination for generated artifacts")
    run.add_argument(
        "--source-type", required=True, choices=["retailrocket", "synthetic_fixture"]
    )
    run.add_argument("--gap-minutes", type=positive_integer, default=30)
    run.add_argument("--max-rejected-fraction", type=fraction, default=0.01)
    run.add_argument("--limit-rows", type=positive_integer, default=None)
    spark = subparsers.add_parser("spark-run", help="Run distributed PySpark ETL to Parquet")
    spark.add_argument("--input", required=True, help="Path to events.csv")
    spark.add_argument("--output-dir", required=True, help="Destination for generated artifacts")
    spark.add_argument(
        "--source-type", required=True, choices=["retailrocket", "synthetic_fixture"]
    )
    spark.add_argument("--gap-minutes", type=positive_integer, default=30)
    spark.add_argument("--max-rejected-fraction", type=fraction, default=0.01)
    return parser


def _execute(args: argparse.Namespace) -> dict:
    if args.command == "validate":
        raw = read_events(args.input, args.limit_rows)
        if raw.empty:
            raise DataContractError("Input CSV contains no event rows")
        report = validate_events(raw).report
        report["source_type"] = args.source_type
        report["validation_passed"] = (
            report["rows_valid"] > 0
            and report["rows_rejected"] / report["rows_read"] <= args.max_rejected_fraction
        )
        return report
    elif args.command == "run":
        summary = run_pipeline(
            input_path=args.input,
            output_dir=args.output_dir,
            source_type=args.source_type,
            gap_minutes=args.gap_minutes,
            max_rejected_fraction=args.max_rejected_fraction,
            limit_rows=args.limit_rows,
        )
    elif args.command == "spark-run":
        from omnihealth.spark_pipeline import run_spark_pipeline

        summary = run_spark_pipeline(
            input_path=args.input,
            output_dir=args.output_dir,
            source_type=args.source_type,
            gap_minutes=args.gap_minutes,
            max_rejected_fraction=args.max_rejected_fraction,
        )
    return summary


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        summary = _execute(args)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps(summary, indent=2))
    if args.command == "validate" and not summary["validation_passed"]:
        parser.exit(2)


if __name__ == "__main__":
    main()
