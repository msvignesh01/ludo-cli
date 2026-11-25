"""Creation and export of centralized functional Ludo state."""

from __future__ import annotations

import copy
import random
from typing import Any

from ..shared.contracts import PLAYER_SPECS, clone_event, get_start_indices, make_event


def create_game_state(
    config: dict[str, Any],
    player_names: list[str],
    seed: int | None = None,
    player_kinds: list[str] | None = None,
) -> dict[str, Any]:
    """Create one explicit state dictionary for a functional match."""
    match_config = copy.deepcopy(config)
    starts = get_start_indices(match_config)
    kinds = player_kinds or ["human"] * len(player_names)
    players: list[dict[str, Any]] = []
    for index, name in enumerate(player_names):
        spec = PLAYER_SPECS[index]
        players.append(
            {
                "index": index,
                "name": name,
                "kind": kinds[index],
                "color": spec["color"],
                "color_hex": spec["hex"],
                "color_code": spec["ansi"],
                "prefix": spec["prefix"],
                "start_index": starts[index],
                "captures_made": 0,
                "tokens": [
                    {
                        "token_idx": token_idx,
                        "label": f"{spec['prefix']}{token_idx + 1}",
                        "steps": -1,
                    }
                    for token_idx in range(int(match_config["tokens_per_player"]))
                ],
            }
        )
    state: dict[str, Any] = {
        "config": match_config,
        "max_turns": int(match_config["max_turns"]),
        "rng": random.Random(seed if seed is not None else match_config["seed"]),
        "current_player": 0,
        "turn_count": 0,
        "consecutive_sixes": 0,
        "status": "PLAYING",
        "winner_index": None,
        "draw_reason": None,
        "finish_order": [],
        "last_event": "Game started.",
        "events": [],
        "players": players,
    }
    state["events"].append(
        make_event(
            "GAME_STARTED",
            0,
            None,
            {"mode": match_config["mode"], "profile": match_config["profile"]},
        )
    )
    return state


def export_canonical_state(state: dict[str, Any]) -> dict[str, Any]:
    """Return a JSON-serializable snapshot without RNG internals."""
    return {
        "config": copy.deepcopy(state["config"]),
        "max_turns": state["max_turns"],
        "turn_count": state["turn_count"],
        "current_player": state["current_player"],
        "consecutive_sixes": state["consecutive_sixes"],
        "status": state["status"],
        "winner_index": state["winner_index"],
        "draw_reason": state["draw_reason"],
        "finish_order": list(state["finish_order"]),
        "last_event": state["last_event"],
        "events": [clone_event(event) for event in state["events"]],
        "players": [
            {
                "index": player["index"],
                "name": player["name"],
                "kind": player["kind"],
                "color": player["color"],
                "start_index": player["start_index"],
                "captures_made": player["captures_made"],
                "tokens": [
                    {"label": token["label"], "steps": token["steps"]}
                    for token in player["tokens"]
                ],
            }
            for player in state["players"]
        ],
    }
