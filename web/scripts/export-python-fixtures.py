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
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from testing.parity_test import SCENARIOS, scenario_config
from v1_initial.func_ludo.rules import (
    advance_turn,
    apply_move,
    declare_mutual_draw,
    get_valid_moves,
    preview_move,
    process_roll,
    quit,
)
from v1_initial.func_ludo.state import create_game_state, export_canonical_state
from v1_initial.oop_ludo.bot import BotPolicy
from v1_initial.oop_ludo.engine import LudoGame
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


def export_games(revision: str) -> dict[str, object]:
    """Record every Python transition needed to replay the full game matrix."""
    path = FIXTURES / "games.jsonl"
    totals = {"games": 0, "wins": 0, "draws": 0, "rolls": 0, "moves": 0, "snapshots": 0}
    game_number = 0
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for scenario in SCENARIOS:
            for _ in range(scenario[7]):
                game_number += 1
                seed = 20_000 + game_number
                mode, players, _, _, _, _, _, _, _ = scenario
                names = [f"P{index + 1}" for index in range(players)]
                kinds = ["bot"] * players
                config = scenario_config(scenario, seed)
                game = LudoGame(config, names, seed=seed, player_kinds=kinds)
                policy = BotPolicy()
                actions: list[dict[str, Any]] = []
                stats = {"rolls": 0, "moves": 0, "snapshots": 1}
                digest = hashlib.sha256()
                digest.update(canonical_bytes(game.export_canonical_state()))

                for _ in range(100_000):
                    if game.status != "PLAYING":
                        break
                    roll = game.roll_die()
                    actions.append({"type": "roll", "roll": roll})
                    result = game.process_roll(roll)
                    digest.update(canonical_bytes(game.export_canonical_state()))
                    stats["rolls"] += 1
                    stats["snapshots"] += 1
                    valid_moves = result["valid_moves"]
                    if valid_moves:
                        choice = policy.decision_details(game, roll, valid_moves)
                        token_idx = int(choice["token_idx"])
                        actions.append(
                            {
                                "type": "bot",
                                "token_idx": token_idx,
                                "reason": choice["reason"],
                            }
                        )
                        game.record_bot_decision(token_idx, roll, choice["reason"])
                        digest.update(canonical_bytes(game.export_canonical_state()))
                        stats["snapshots"] += 1
                        actions.append({"type": "move", "token_idx": token_idx, "roll": roll})
                        game.apply_move(token_idx, roll)
                        digest.update(canonical_bytes(game.export_canonical_state()))
                        stats["moves"] += 1
                        stats["snapshots"] += 1
                else:
                    raise AssertionError(f"Game exceeded the safety limit: {mode}, seed={seed}")

                final = game.export_canonical_state()
                digest.update(canonical_bytes(final))
                stats["snapshots"] += 1
                if final["status"] not in {"WON", "DRAW"}:
                    raise AssertionError(f"Game did not terminate: {mode}, seed={seed}")
                record = {
                    "schema": 1,
                    "revision": revision,
                    "scenario": list(scenario),
                    "seed": seed,
                    "config": config,
                    "names": names,
                    "kinds": kinds,
                    "actions": actions,
                    "transition_hash": digest.hexdigest(),
                    "final": final,
                    "stats": stats,
                }
                stream.write(canonical_bytes(record).decode("utf-8") + "\n")
                totals["games"] += 1
                totals["wins"] += int(final["status"] == "WON")
                totals["draws"] += int(final["status"] == "DRAW")
                totals["rolls"] += stats["rolls"]
                totals["moves"] += stats["moves"]
                totals["snapshots"] += stats["snapshots"]

    expected = {
        "games": 1080,
        "wins": 362,
        "draws": 718,
        "rolls": 93403,
        "moves": 71678,
        "snapshots": 238919,
    }
    if totals != expected:
        raise AssertionError(f"Python matrix totals changed: {totals}")
    encoded = path.read_bytes()
    return {
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "bytes": len(encoded),
        **totals,
    }


def apply_setup(state: dict[str, Any], mutations: list[dict[str, Any]]) -> None:
    """Apply explicit fixture mutations without hiding setup in engine code."""
    for mutation in mutations:
        kind = mutation["type"]
        if kind == "token_steps":
            state["players"][mutation["player"]]["tokens"][mutation["token"]]["steps"] = mutation[
                "steps"
            ]
        elif kind == "captures_made":
            state["players"][mutation["player"]]["captures_made"] = mutation["value"]
        elif kind == "current_player":
            state["current_player"] = mutation["value"]
        elif kind == "turn_count":
            state["turn_count"] = mutation["value"]
        elif kind == "consecutive_sixes":
            state["consecutive_sixes"] = mutation["value"]
        elif kind == "finish_order":
            state["finish_order"] = list(mutation["value"])
        else:
            raise AssertionError(f"Unknown setup mutation: {kind}")


def export_rules(revision: str) -> dict[str, object]:
    """Export focused Python examples for every rule and terminal transition."""
    records: list[dict[str, Any]] = []

    def add_record(
        name: str,
        overrides: dict[str, Any],
        setup: list[dict[str, Any]],
        action: dict[str, Any],
        players: int = 2,
        tokens: int = 2,
    ) -> None:
        """Build one fixture and derive its expected values from Python."""
        config = build_config("quick", "classic", players, {"tokens_per_player": tokens, **overrides})
        names = [f"P{index + 1}" for index in range(players)]
        kinds = ["human"] * players
        state = create_game_state(config, names, seed=42, player_kinds=kinds)
        apply_setup(state, setup)
        expected: dict[str, Any] = {}
        kind = action["type"]
        if kind == "preview":
            expected["preview"] = preview_move(
                state,
                action["player"],
                action["token_idx"],
                action["roll"],
            )
        elif kind == "valid_moves":
            expected["valid_moves"] = get_valid_moves(state, action["player"], action["roll"])
        elif kind == "roll":
            expected["roll_result"] = process_roll(state, action["roll"])
        elif kind == "turn":
            expected["roll_result"] = process_roll(state, action["roll"])
            expected["valid_moves"] = get_valid_moves(state, state["current_player"], action["roll"])
            if action["token_idx"] is not None:
                expected["preview"] = preview_move(
                    state,
                    state["current_player"],
                    action["token_idx"],
                    action["roll"],
                )
                expected["result"] = apply_move(state, action["token_idx"], action["roll"])
        elif kind == "move":
            expected["preview"] = preview_move(
                state,
                state["current_player"],
                action["token_idx"],
                action["roll"],
            )
            expected["result"] = apply_move(state, action["token_idx"], action["roll"])
        elif kind == "advance":
            advance_turn(state)
        elif kind == "draw":
            declare_mutual_draw(state)
        elif kind == "quit":
            quit(state)
        else:
            raise AssertionError(f"Unknown rule action: {kind}")
        expected["snapshot"] = export_canonical_state(state)
        records.append(
            {
                "name": name,
                "config": config,
                "names": names,
                "kinds": kinds,
                "setup": setup,
                "action": action,
                "expected": expected,
            }
        )

    add_record(
        "safe-tile-non-capture",
        {},
        [
            {"type": "token_steps", "player": 0, "token": 0, "steps": 6},
            {"type": "token_steps", "player": 1, "token": 0, "steps": 21},
        ],
        {"type": "preview", "player": 0, "token_idx": 0, "roll": 1},
    )
    add_record(
        "strict-path-blockade",
        {"blockades": "strict"},
        [
            {"type": "token_steps", "player": 0, "token": 0, "steps": 1},
            {"type": "token_steps", "player": 1, "token": 0, "steps": 18},
            {"type": "token_steps", "player": 1, "token": 1, "steps": 18},
        ],
        {"type": "preview", "player": 0, "token_idx": 0, "roll": 5},
    )
    add_record(
        "safe-pair-immunity",
        {"blockades": "safe_pair"},
        [
            {"type": "token_steps", "player": 0, "token": 0, "steps": 2},
            {"type": "token_steps", "player": 1, "token": 0, "steps": 20},
            {"type": "token_steps", "player": 1, "token": 1, "steps": 20},
        ],
        {"type": "move", "token_idx": 0, "roll": 4},
    )
    add_record(
        "kill-to-enter-wrap",
        {"kill_to_enter": True},
        [{"type": "token_steps", "player": 0, "token": 0, "steps": 26}],
        {"type": "move", "token_idx": 0, "roll": 1},
    )
    add_record(
        "exact-home-overshoot",
        {},
        [{"type": "token_steps", "player": 0, "token": 0, "steps": 29}],
        {"type": "preview", "player": 0, "token_idx": 0, "roll": 3},
    )
    add_record(
        "non-exact-home-clamp",
        {"exact_home_roll": False},
        [{"type": "token_steps", "player": 0, "token": 0, "steps": 29}],
        {"type": "move", "token_idx": 0, "roll": 6},
    )
    add_record(
        "home-on-six-reset",
        {},
        [
            {"type": "token_steps", "player": 0, "token": 0, "steps": 25},
            {"type": "token_steps", "player": 0, "token": 1, "steps": 30},
            {"type": "consecutive_sixes", "value": 1},
        ],
        {"type": "turn", "roll": 6, "token_idx": 0},
    )
    add_record(
        "triple-six-forfeit",
        {},
        [{"type": "consecutive_sixes", "value": 2}],
        {"type": "roll", "roll": 6},
    )
    add_record(
        "no-move-skip",
        {},
        [],
        {"type": "roll", "roll": 1},
    )
    add_record(
        "capture-and-bonus",
        {},
        [
            {"type": "token_steps", "player": 0, "token": 0, "steps": 4},
            {"type": "token_steps", "player": 1, "token": 0, "steps": 22},
        ],
        {"type": "turn", "roll": 4, "token_idx": 0},
    )
    add_record(
        "podium-continuation",
        {"podium_mode": True},
        [
            {"type": "token_steps", "player": 0, "token": 0, "steps": 30},
            {"type": "token_steps", "player": 0, "token": 1, "steps": 31},
        ],
        {"type": "turn", "roll": 1, "token_idx": 0},
        players=3,
    )
    add_record(
        "two-player-win",
        {},
        [
            {"type": "token_steps", "player": 0, "token": 0, "steps": 30},
            {"type": "token_steps", "player": 0, "token": 1, "steps": 31},
        ],
        {"type": "turn", "roll": 1, "token_idx": 0},
    )
    add_record(
        "turn-cap-draw",
        {"max_turns": 1},
        [],
        {"type": "advance"},
    )
    add_record("mutual-draw", {}, [], {"type": "draw"})
    add_record("quit", {}, [], {"type": "quit"})
    add_record(
        "safe-tiles-disabled-capture",
        {"safe_tiles_enabled": False},
        [
            {"type": "token_steps", "player": 0, "token": 0, "steps": 6},
            {"type": "token_steps", "player": 1, "token": 0, "steps": 21},
        ],
        {"type": "move", "token_idx": 0, "roll": 1},
    )
    add_record(
        "non-safe-multi-token-capture",
        {},
        [
            {"type": "token_steps", "player": 0, "token": 0, "steps": 4},
            {"type": "token_steps", "player": 1, "token": 0, "steps": 22},
            {"type": "token_steps", "player": 1, "token": 1, "steps": 22},
        ],
        {"type": "move", "token_idx": 0, "roll": 4},
    )
    add_record(
        "capture-bonus-disabled",
        {"bonus_on_capture": False},
        [
            {"type": "token_steps", "player": 0, "token": 0, "steps": 4},
            {"type": "token_steps", "player": 1, "token": 0, "steps": 22},
        ],
        {"type": "turn", "roll": 4, "token_idx": 0},
    )
    add_record(
        "finished-player-skip",
        {},
        [
            {"type": "token_steps", "player": 1, "token": 0, "steps": 31},
            {"type": "token_steps", "player": 1, "token": 1, "steps": 31},
        ],
        {"type": "advance"},
        players=3,
    )
    add_record(
        "kill-to-enter-unlocked",
        {"kill_to_enter": True},
        [
            {"type": "token_steps", "player": 0, "token": 0, "steps": 26},
            {"type": "captures_made", "player": 0, "value": 1},
        ],
        {"type": "move", "token_idx": 0, "roll": 1},
    )

    payload = {
        "schema": 1,
        "revision": revision,
        "python": platform.python_version(),
        "records": records,
    }
    encoded = canonical_bytes(payload)
    (FIXTURES / "rules.json").write_bytes(encoded)
    return {"sha256": hashlib.sha256(encoded).hexdigest(), "records": len(records)}


def main() -> None:
    """Regenerate all oracle fixtures and their content manifest."""
    FIXTURES.mkdir(parents=True, exist_ok=True)
    revision = source_revision()
    manifest = {
        "schema": 1,
        "revision": revision,
        "python": platform.python_version(),
        "fixtures": {
            "rng.json": export_rng(),
            "geometry.json": export_geometry(),
            "games.jsonl": export_games(revision),
            "rules.json": export_rules(revision),
        },
    }
    (FIXTURES / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Exported Python oracle fixtures to {FIXTURES}")
    print(
        "Python web matrix: games=1080, wins=362, draws=718, "
        "rolls=93403, moves=71678, snapshots=238919"
    )


if __name__ == "__main__":
    main()
