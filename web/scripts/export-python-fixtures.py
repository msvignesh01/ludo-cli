#!/usr/bin/env python3
"""Export deterministic Python oracle fixtures for the web game core."""

from __future__ import annotations

import hashlib
import json
import platform
import random
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "web" / "fixtures"
ROLLS_PER_SEED = 10_000
SEEDS = [-1, 0, 1, 42, 2**32, 2**64 + 7, *range(20_000, 20_020)]


def source_revision() -> str:
    """Return the repository revision that produced the fixture payload."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def canonical_bytes(value: object) -> bytes:
    """Encode one fixture using Python's canonical JSON formatting."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def export_rng() -> dict[str, object]:
    """Write the fixed-seed dice stream and return its manifest entry."""
    records = []
    for seed in SEEDS:
        rng = random.Random(seed)
        records.append(
            {
                "seed": str(seed),
                "rolls": [rng.randint(1, 6) for _ in range(ROLLS_PER_SEED)],
            }
        )
    payload = {
        "schema": 1,
        "python": platform.python_version(),
        "rolls_per_seed": ROLLS_PER_SEED,
        "seeds": records,
    }
    encoded = canonical_bytes(payload)
    (FIXTURES / "rng.json").write_bytes(encoded)
    return {"sha256": hashlib.sha256(encoded).hexdigest(), "seeds": len(records)}


def main() -> None:
    """Regenerate all oracle fixtures and their content manifest."""
    FIXTURES.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": 1,
        "revision": source_revision(),
        "python": platform.python_version(),
        "fixtures": {"rng.json": export_rng()},
    }
    (FIXTURES / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Exported RNG fixtures for {len(SEEDS)} seeds to {FIXTURES}")


if __name__ == "__main__":
    main()
