"""Explicit data contract for the RetailRocket clickstream events file."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import pandas as pd

RAW_COLUMNS = ("timestamp", "visitorid", "event", "itemid", "transactionid")
EVENT_TYPES = frozenset({"view", "addtocart", "transaction"})
LOWEST_TIMESTAMP_MS = 946684800000  # 2000-01-01 UTC; catches unit mistakes
HIGHEST_TIMESTAMP_MS = 4102444800000  # 2100-01-01 UTC


class DataContractError(ValueError):
    """Raised when an input does not meet the declared dataset contract."""


def read_events(path: str, limit_rows: int | None = None) -> pd.DataFrame:
    """Read RetailRocket CSV as strings to protect anonymized identifiers."""
    if limit_rows is not None and limit_rows <= 0:
        raise ValueError("limit_rows must be positive")
    try:
        with Path(path).open(encoding="utf-8-sig", newline="") as stream:
            header = next((row for row in csv.reader(stream, strict=True) if row), [])
        if not header:
            raise DataContractError("Input CSV is empty")
        duplicates = sorted(name for name, count in Counter(header).items() if count > 1)
        if duplicates:
            raise DataContractError(f"Duplicate CSV columns: {', '.join(duplicates)}")
        frame = pd.read_csv(
            path,
            dtype="string",
            keep_default_na=False,
            nrows=limit_rows,
        )
    except (OSError, UnicodeError, csv.Error, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise DataContractError(f"Unable to read input CSV: {exc}") from exc
    if not isinstance(frame.index, pd.RangeIndex):
        raise DataContractError("Input CSV contains more fields than its header")
    missing = set(RAW_COLUMNS).difference(frame.columns)
    if missing:
        raise DataContractError(f"Missing required columns: {', '.join(sorted(missing))}")
    return frame.loc[:, list(RAW_COLUMNS)].copy()
