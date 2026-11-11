"""Content fingerprints and software versions for reproducible run reports."""

from __future__ import annotations

import hashlib
import platform
from importlib.metadata import version
from pathlib import Path

from omnihealth import __version__


def input_manifest(path: str | Path, engine: str, limit_rows: int | None = None) -> dict:
    source = Path(path)
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    packages = ["pandas", "numpy"] if engine == "pandas" else ["pyspark"]
    return {
        "input_sha256": digest.hexdigest(),
        "input_size_bytes": source.stat().st_size,
        "limit_rows": limit_rows,
        "input_scope": "prefix" if limit_rows is not None else "full_file",
        "engine": engine,
        "software_versions": {
            "omnihealth": __version__, "python": platform.python_version(),
            **{package: version(package) for package in packages},
        },
    }
