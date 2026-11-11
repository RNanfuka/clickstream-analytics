"""Explicit data contract for the RetailRocket clickstream events file."""

from __future__ import annotations

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
        frame = pd.read_csv(
            path,
            dtype="string",
            keep_default_na=False,
            nrows=limit_rows,
        )
    except (OSError, pd.errors.ParserError) as exc:
        raise DataContractError(f"Unable to read input CSV: {exc}") from exc
    missing = set(RAW_COLUMNS).difference(frame.columns)
    if missing:
        raise DataContractError(f"Missing required columns: {', '.join(sorted(missing))}")
    return frame.loc[:, list(RAW_COLUMNS)].copy()
