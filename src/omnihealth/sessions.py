"""Visitor-scoped inactivity-gap sessionization and conversion proxy measures."""

from __future__ import annotations

import pandas as pd


def sessionize(events: pd.DataFrame, gap_minutes: int = 30) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return event facts and session facts, ordered deterministically.

    A new session begins after a gap strictly greater than `gap_minutes`.
    Conversion means a RetailRocket transaction event in that session;
    it does NOT mean a healthcare or ad-attributed conversion.
    """
    if gap_minutes <= 0:
        raise ValueError("gap_minutes must be positive")
    if events.empty:
        raise ValueError("Cannot sessionize an empty validated dataset")

    enriched = events.sort_values(
        ["visitor_id", "event_ts", "event_type", "item_id"], kind="mergesort"
    ).reset_index(drop=True).copy()
    gaps = enriched.groupby("visitor_id", sort=False)["event_ts"].diff()
    starts = gaps.isna() | gaps.gt(pd.Timedelta(minutes=gap_minutes))
    session_numbers = starts.groupby(enriched["visitor_id"]).cumsum().astype("int64")
    enriched["session_id"] = (
        enriched["visitor_id"].astype(str)
        + "-"
        + session_numbers.astype(str).str.zfill(6)
    )

    enriched["is_view"] = enriched["event_type"].eq("view").astype("int8")
    enriched["is_cart"] = enriched["event_type"].eq("addtocart").astype("int8")
    enriched["is_purchase"] = enriched["event_type"].eq("transaction").astype("int8")
    grouped = enriched.groupby(["session_id", "visitor_id"], sort=False)
    sessions = grouped.agg(
        session_start=("event_ts", "min"),
        session_end=("event_ts", "max"),
        event_count=("event_type", "size"),
        view_events=("is_view", "sum"),
        cart_events=("is_cart", "sum"),
        transaction_events=("is_purchase", "sum"),
        order_count=("transaction_id", "nunique"),
    ).reset_index()
    sessions["duration_seconds"] = (
        sessions["session_end"] - sessions["session_start"]
    ).dt.total_seconds()
    sessions["converted"] = sessions["transaction_events"].gt(0).astype("int8")
    enriched = enriched.drop(columns=["is_view", "is_cart", "is_purchase"])
    return enriched, sessions
