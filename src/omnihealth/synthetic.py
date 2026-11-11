"""Deterministic synthetic retail events for engineering benchmarks, never model evidence."""

from __future__ import annotations

import csv
import random
from pathlib import Path

from omnihealth.artifacts import write_json
from omnihealth.contracts import RAW_COLUMNS


def generate_events(output: str | Path, sessions: int = 1000, seed: int = 42,
                    conversion_probability: float = 0.25, overwrite: bool = False) -> dict:
    if sessions <= 0 or not 0 <= conversion_probability <= 1:
        raise ValueError("sessions must be positive and conversion probability between 0 and 1")
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    converted = 0
    with target.open("w" if overwrite else "x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(RAW_COLUMNS)
        for session in range(sessions):
            visitor = f"synthetic_{session // 3:08d}"
            start = 1735689600000 + ((session // 3) % 30) * 86400000 + (session % 3) * 3600000
            item = f"{rng.randrange(1, 1001):04d}"
            purchase = rng.random() < conversion_probability
            converted += purchase
            for step, event in enumerate(("view", "view", "addtocart",
                                          "transaction" if purchase else "view")):
                writer.writerow((start + step * 60000, visitor, event, item,
                                 f"synthetic_order_{session:08d}" if event == "transaction" else ""))
    metadata = {
        "source_type": "synthetic_fixture", "generator_seed": seed,
        "events": sessions * 4, "sessions": sessions, "visitors": (sessions + 2) // 3,
        "converted_sessions": converted, "conversion_probability": conversion_probability,
        "session_conversion_rate": round(converted / sessions, 4),
        "warning": "Artificial behavior for software and timing checks; not model or market evidence",
    }
    write_json(target.with_suffix(".metadata.json"), metadata)
    return metadata
