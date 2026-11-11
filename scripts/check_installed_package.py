"""Run against an installed wheel from outside the source tree."""

from importlib.metadata import version
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory

from omnihealth import __version__
from omnihealth.pipeline import run_pipeline
from omnihealth.reporting import read_report

assert version("omnihealth-ai") == __version__
assert files("omnihealth").joinpath("sql/marts.sql").is_file()
with TemporaryDirectory() as directory:
    root = Path(directory)
    source = root / "events.csv"
    source.write_text(
        "timestamp,visitorid,event,itemid,transactionid\n"
        "1433221200000,001,view,01,\n"
        "1433221260000,001,transaction,01,order_1\n"
    )
    summary = run_pipeline(source, root / "out", "synthetic_fixture")
    assert summary["sessions"] == 1
    assert summary["converted_sessions"] == 1
    assert read_report(root / "out")["rows"][0]["session_conversion_rate"] == 1.0
print(f"Installed wheel {__version__}: version, SQL resources, pipeline, and report verified")
