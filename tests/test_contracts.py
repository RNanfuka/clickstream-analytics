from __future__ import annotations

import pytest

from omnihealth.contracts import DataContractError, read_events

HEADER = "timestamp,visitorid,event,itemid,transactionid\n"


@pytest.mark.parametrize("content,reason", [
    ("", "empty"),
    ("timestamp,visitorid,event,itemid,itemid,transactionid\n", "Duplicate"),
    (HEADER + "1433221200000,001,view,01,,extra\n", "more fields"),
    (HEADER + '"unterminated', "Unable to read"),
])
def test_reject_unreadable_or_ambiguous_csv(tmp_path, content, reason):
    source = tmp_path / "events.csv"
    source.write_text(content)
    with pytest.raises(DataContractError, match=reason):
        read_events(str(source))


def test_preserve_identifier_text_and_handle_utf8_bom(tmp_path):
    source = tmp_path / "events.csv"
    source.write_text(HEADER + "1433221200000,001,view,NA,\n", encoding="utf-8-sig")
    row = read_events(str(source)).iloc[0]
    assert row["visitorid"] == "001"
    assert row["itemid"] == "NA"
    assert row["transactionid"] == ""
