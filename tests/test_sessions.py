from __future__ import annotations

import pandas as pd
import pytest

from omnihealth.quality import validate_events
from omnihealth.sessions import sessionize


def _events(rows):
    return validate_events(
        pd.DataFrame(
            rows, columns=["timestamp", "visitorid", "event", "itemid", "transactionid"]
        )
    ).valid


def test_inactivity_gap_per_visitor_and_order_deduplication():
    frame = _events(
        [
            ["1433221200000", "a", "view", "1", ""],
            ["1433221260000", "b", "view", "1", ""],
            ["1433223000000", "a", "transaction", "1", "order_1"],  # exactly 30m
            ["1433223000000", "a", "transaction", "2", "order_1"],
            ["1433224801000", "a", "view", "2", ""],  # 30m + 1s
        ]
    )
    events, sessions = sessionize(frame, gap_minutes=30)
    a = sessions.loc[sessions["visitor_id"] == "a"].sort_values("session_start")
    assert len(a) == 2
    assert a.iloc[0]["order_count"] == 1
    assert a.iloc[0]["transaction_events"] == 2
    assert a.iloc[0]["converted"] == 1
    assert a.iloc[1]["converted"] == 0
    assert len(sessions) == 3
    assert len(events) == 5


def test_nonpositive_gap_raises():
    frame = _events([["1433221200000", "a", "view", "1", ""]])
    with pytest.raises(ValueError, match="positive"):
        sessionize(frame, gap_minutes=0)
