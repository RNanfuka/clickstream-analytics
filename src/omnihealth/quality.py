"""Deterministic field-level data validation and rejection reporting."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from omnihealth.contracts import (
    EVENT_TYPES,
    HIGHEST_TIMESTAMP_MS,
    LOWEST_TIMESTAMP_MS,
    RAW_COLUMNS,
    DataContractError,
)


@dataclass
class ValidationResult:
    valid: pd.DataFrame
    rejected: pd.DataFrame
    report: dict[str, int | float | str]


def validate_events(raw: pd.DataFrame) -> ValidationResult:
    """Validate without silently dropping rows or removing repeat user actions.

    A duplicate event can be a genuine repeated action. We *report* exact
    duplicates but intentionally do not deduplicate the input.
    """
    missing = set(RAW_COLUMNS).difference(raw.columns)
    if missing:
        raise DataContractError(f"Missing required columns: {', '.join(sorted(missing))}")

    raw = raw.loc[:, list(RAW_COLUMNS)].copy().astype("string")
    for col in RAW_COLUMNS:
        raw[col] = raw[col].str.strip()

    numeric_timestamp = pd.to_numeric(raw["timestamp"], errors="coerce")
    is_integer_timestamp = raw["timestamp"].str.fullmatch(r"[0-9]+", na=False)
    timestamp_valid = (
        is_integer_timestamp
        & numeric_timestamp.between(LOWEST_TIMESTAMP_MS, HIGHEST_TIMESTAMP_MS, inclusive="left")
    ).fillna(False)
    visitor_valid = raw["visitorid"].notna() & raw["visitorid"].ne("")
    item_valid = raw["itemid"].notna() & raw["itemid"].ne("")
    event_valid = raw["event"].isin(EVENT_TYPES)
    has_transaction = raw["transactionid"].notna() & raw["transactionid"].ne("")
    transaction_valid = has_transaction.eq(raw["event"].eq("transaction"))

    problems = {
        "invalid_timestamp": ~timestamp_valid,
        "missing_visitor_id": ~visitor_valid,
        "missing_item_id": ~item_valid,
        "invalid_event_type": ~event_valid,
        "invalid_transaction_id_for_event": ~transaction_valid,
    }
    good_mask = pd.Series(True, index=raw.index)
    for mask in problems.values():
        good_mask &= ~mask.fillna(True)

    rejected = raw.loc[~good_mask].copy()
    # Include ALL error causes, not just the first, for auditability.
    rejected["rejection_reason"] = [
        ";".join(name for name, mask in problems.items() if bool(mask.loc[idx]))
        for idx in rejected.index
    ]

    valid = raw.loc[good_mask].copy()
    event_ts = pd.to_datetime(
        pd.to_numeric(valid["timestamp"], errors="raise"),
        unit="ms",
        utc=True,
    )
    valid = pd.DataFrame(
        {
            "event_ts": event_ts,
            "event_date": event_ts.dt.strftime("%Y-%m-%d"),
            "visitor_id": valid["visitorid"],
            "event_type": valid["event"],
            "item_id": valid["itemid"],
            "transaction_id": valid["transactionid"].replace("", pd.NA),
        },
        index=valid.index,
    ).reset_index(drop=True)

    total = len(raw)
    report: dict[str, int | float | str] = {
        "rows_read": total,
        "rows_valid": len(valid),
        "rows_rejected": len(rejected),
        "rejected_fraction": round(len(rejected) / total, 8) if total else 0.0,
        "exact_duplicate_valid_rows": int(valid.duplicated().sum()),
        "duplicate_policy": "retain_and_report",
    }
    for name, mask in problems.items():
        report[name] = int(mask.fillna(True).sum())
    return ValidationResult(valid=valid, rejected=rejected, report=report)
