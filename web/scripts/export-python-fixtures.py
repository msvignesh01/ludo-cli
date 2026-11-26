#!/usr/bin/env python3
"""Export deterministic Python oracle fixtures for the web game core."""

from __future__ import annotations

import hashlib
import json
import platform
import random
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from v1_initial.func_ludo.state import create_game_state, export_canonical_state
from v1_initial.shared.contracts import build_config
from v1_initial.shared.geometry import build_board_geometry
from v1_initial.shared.gui_support import build_gui_view_model
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


def export_geometry() -> dict[str, object]:
    """Write all seating geometries and one mixed-location view model."""
    payload: dict[str, object] = {
        "schema": 1,
        "python": platform.python_version(),
    }
    for mode in ("quick", "classic"):
        for count in (2, 3, 4):
            config = build_config(mode, "classic", count)
            payload[f"{mode}{count}p"] = build_board_geometry(config)

    config = build_config("quick", "showcase", 3)
    state = create_game_state(config, ["Ada", "Grace", "Linus"], 42, ["human", "bot", "human"])
    state["players"][0]["tokens"][0]["steps"] = -1
    state["players"][0]["tokens"][1]["steps"] = 0
    state["players"][1]["tokens"][0]["steps"] = 21
    state["players"][1]["tokens"][1]["steps"] = 27
    state["players"][2]["tokens"][0]["steps"] = config["home_finish"]
    state["players"][2]["tokens"][1]["steps"] = config["home_finish"]
    state["players"][0]["captures_made"] = 2
    state["current_player"] = 1
    state["turn_count"] = 7
    state["last_event"] = "Geometry fixture."
    snapshot = export_canonical_state(state)
    payload["snapshot"] = snapshot
    payload["view_model"] = build_gui_view_model(snapshot)
    encoded = canonical_bytes(payload)
    (FIXTURES / "geometry.json").write_bytes(encoded)
    return {"sha256": hashlib.sha256(encoded).hexdigest(), "boards": 6}


def main() -> None:
    """Regenerate all oracle fixtures and their content manifest."""
    FIXTURES.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": 1,
        "revision": source_revision(),
        "python": platform.python_version(),
        "fixtures": {
            "rng.json": export_rng(),
            "geometry.json": export_geometry(),
        },
    }
    (FIXTURES / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Exported RNG and geometry fixtures to {FIXTURES}")


if __name__ == "__main__":
    main()
