from __future__ import annotations

import pandas as pd
import pytest

from omnihealth.contracts import DataContractError, read_events
from omnihealth.quality import validate_events


def test_nullable_values_and_repeated_indices_are_audited_without_crashing():
    raw = pd.DataFrame(
        [
            ["1433221200000", "001", "view", "01", None],
            [None, None, None, None, None],
            ["1433221200000", "001", "transaction", "01", pd.NA],
        ],
        columns=["timestamp", "visitorid", "event", "itemid", "transactionid"],
        index=[7, 7, 7],
    )
    outcome = validate_events(raw)
    assert outcome.report["rows_valid"] == 1
    assert outcome.report["rows_rejected"] == 2
    assert set(outcome.rejected.iloc[0]["rejection_reason"].split(";")) == {
        "invalid_timestamp", "missing_visitor_id", "missing_item_id", "invalid_event_type"
    }
    assert outcome.rejected.iloc[1]["rejection_reason"] == "invalid_transaction_id_for_event"


def test_validation_rejects_multiple_errors_and_preserves_exact_duplicates():
    raw = pd.DataFrame(
        [
            ["1433221200000", "a", "view", "1", ""],
            ["1433221200000", "a", "view", "1", ""],
            ["not-a-timestamp", "a", "view", "1", ""],
            ["1433221200000", "", "view", "1", ""],
            ["1433221200000", "a", "impression", "1", ""],
            ["1433221200000", "a", "transaction", "1", ""],
            ["1433221200000", "a", "view", "1", "order_x"],
            ["1433221200000", "a", "view", "", ""],
        ],
        columns=["timestamp", "visitorid", "event", "itemid", "transactionid"],
    )
    outcome = validate_events(raw)
    assert outcome.report["rows_valid"] == 2
    assert outcome.report["rows_rejected"] == 6
    assert outcome.report["exact_duplicate_valid_rows"] == 1
    assert outcome.report["invalid_timestamp"] == 1
    assert outcome.report["invalid_transaction_id_for_event"] == 2
    assert "invalid_event_type" in outcome.rejected["rejection_reason"].to_string()
    assert str(outcome.valid["event_ts"].dt.tz) == "UTC"


def test_contract_missing_columns(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_text("timestamp,visitorid,event\n123,1,view\n", encoding="utf-8")
    with pytest.raises(DataContractError, match="Missing required columns"):
        read_events(str(source))


def test_timestamp_seconds_not_mistaken_for_milliseconds():
    raw = pd.DataFrame(
        [["1433221200", "a", "view", "1", ""]],
        columns=["timestamp", "visitorid", "event", "itemid", "transactionid"],
    )
    assert validate_events(raw).report["rows_rejected"] == 1
