"""Presets, validation, seating metadata, and JSON-friendly event helpers."""

from __future__ import annotations

import math
from typing import Any


PRESETS: dict[str, dict[str, Any]] = {
    "quick": {
        "track_len": 28,
        "home_len": 4,
        "tokens_per_player": 2,
        "outer_last_step": 26,
        "home_finish": 31,
        "safe_tiles": [0, 7, 14, 21],
        "start_indices_2p": [0, 14],
        "start_indices_4p": [0, 7, 14, 21],
        "default_max_turns": 100,
    },
    "classic": {
        "track_len": 52,
        "home_len": 5,
        "tokens_per_player": 4,
        "outer_last_step": 50,
        "home_finish": 56,
        "safe_tiles": [0, 8, 13, 21, 26, 34, 39, 47],
        "start_indices_2p": [0, 26],
        "start_indices_4p": [0, 13, 26, 39],
        "default_max_turns": 250,
    },
}

PLAYER_SPECS: tuple[dict[str, str], ...] = (
    {"color": "RED", "hex": "#EF4444", "ansi": "\033[91m", "prefix": "R"},
    {"color": "GREEN", "hex": "#22C55E", "ansi": "\033[92m", "prefix": "G"},
    {"color": "YELLOW", "hex": "#EAB308", "ansi": "\033[93m", "prefix": "Y"},
    {"color": "BLUE", "hex": "#3B82F6", "ansi": "\033[94m", "prefix": "B"},
)

PROFILE_RULES: dict[str, dict[str, Any]] = {
    "showcase": {
        "blockades": "safe_pair",
        "kill_to_enter": True,
        "podium_mode": True,
        "exact_home_roll": True,
        "triple_six_forfeit": True,
        "safe_tiles_enabled": True,
        "bonus_on_capture": True,
        "bonus_on_home": True,
    },
    "classic": {
        "blockades": "none",
        "kill_to_enter": False,
        "podium_mode": False,
        "exact_home_roll": True,
        "triple_six_forfeit": True,
        "safe_tiles_enabled": True,
        "bonus_on_capture": True,
        "bonus_on_home": True,
    },
}

MATCH_DEFAULTS: dict[str, Any] = {
    "auto_delay": 0.35,
    "commentary": "gameplay",
    "ui": "cli",
    "seed": None,
}

EVENT_TYPES: tuple[str, ...] = (
    "GAME_STARTED",
    "DICE_ROLLED",
    "NO_VALID_MOVES",
    "TRIPLE_SIX_FORFEIT",
    "BOT_DECISION",
    "TOKEN_MOVED",
    "TOKEN_CAPTURED",
    "BLOCKADE_FORMED",
    "PLAYER_FINISHED",
    "BONUS_TURN",
    "TURN_ADVANCED",
    "GAME_WON",
    "GAME_DRAW",
    "GAME_QUIT",
)

LOCKED_GEOMETRY_KEYS = frozenset(
    {
        "track_len",
        "home_len",
        "outer_last_step",
        "home_finish",
        "safe_tiles",
        "start_indices_2p",
        "start_indices_4p",
        "default_max_turns",
    }
)

BOOLEAN_RULE_KEYS = frozenset(
    {
        "kill_to_enter",
        "podium_mode",
        "exact_home_roll",
        "triple_six_forfeit",
        "safe_tiles_enabled",
        "bonus_on_capture",
        "bonus_on_home",
    }
)


def _is_int(value: Any) -> bool:
    """Return whether a value is an integer but not a boolean."""
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_config(config: dict[str, Any]) -> None:
    """Reject unsupported or unsafe match settings."""
    if config["mode"] not in PRESETS:
        raise ValueError("mode must be 'quick' or 'classic'")
    if config["profile"] not in PROFILE_RULES:
        raise ValueError("profile must be 'showcase' or 'classic'")
    if not _is_int(config["player_count"]) or not 2 <= config["player_count"] <= 4:
        raise ValueError("player_count must be 2, 3, or 4")
    if not _is_int(config["tokens_per_player"]) or not 1 <= config["tokens_per_player"] <= 4:
        raise ValueError("tokens_per_player must be an integer from 1 to 4")
    if not _is_int(config["max_turns"]) or config["max_turns"] <= 0:
        raise ValueError("max_turns must be a positive integer")
    delay = config["auto_delay"]
    if isinstance(delay, bool) or not isinstance(delay, (int, float)):
        raise ValueError("auto_delay must be a non-negative number")
    if not math.isfinite(float(delay)) or delay < 0:
        raise ValueError("auto_delay must be a finite non-negative number")
    if config["seed"] is not None and not _is_int(config["seed"]):
        raise ValueError("seed must be an integer or null")
    if config["blockades"] not in {"none", "strict", "safe_pair"}:
        raise ValueError("blockades must be 'none', 'strict', or 'safe_pair'")
    if config["commentary"] not in {"gameplay", "code", "both", "off"}:
        raise ValueError("commentary must be 'gameplay', 'code', 'both', or 'off'")
    if config["ui"] not in {"cli", "gui"}:
        raise ValueError("ui must be 'cli' or 'gui'")
    for key in BOOLEAN_RULE_KEYS:
        if not isinstance(config[key], bool):
            raise ValueError(f"{key} must be true or false")


def build_config(
    mode: str,
    profile: str = "showcase",
    player_count: int = 2,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a validated match configuration while locking board geometry."""
    if mode not in PRESETS:
        raise ValueError("mode must be 'quick' or 'classic'")
    if profile not in PROFILE_RULES:
        raise ValueError("profile must be 'showcase' or 'classic'")
    if not _is_int(player_count) or not 2 <= player_count <= 4:
        raise ValueError("player_count must be 2, 3, or 4")
    if overrides is None:
        overrides = {}
    if not isinstance(overrides, dict):
        raise ValueError("overrides must be a dictionary")
    locked = LOCKED_GEOMETRY_KEYS.intersection(overrides)
    if locked:
        raise ValueError(f"board geometry cannot be overridden: {sorted(locked)}")

    config: dict[str, Any] = {
        "mode": mode,
        "profile": profile,
        "player_count": player_count,
    }
    for key, value in PRESETS[mode].items():
        config[key] = list(value) if isinstance(value, list) else value
    config.update(MATCH_DEFAULTS)
    config.update(PROFILE_RULES[profile])
    config["max_turns"] = config["default_max_turns"]

    allowed_keys = set(config)
    unknown = set(overrides) - allowed_keys
    if unknown:
        raise ValueError(f"unknown configuration keys: {sorted(unknown)}")
    config.update(overrides)
    _validate_config(config)
    return config


def config_from_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Restore a validated configuration from a JSON-style dictionary."""
    if not isinstance(data, dict):
        raise ValueError("configuration must be a dictionary")
    if "mode" not in data:
        raise ValueError("configuration requires a mode")
    mode = data["mode"]
    if mode not in PRESETS:
        raise ValueError("mode must be 'quick' or 'classic'")
    profile = data.get("profile", "showcase")
    player_count = data.get("player_count", 2)
    for key in LOCKED_GEOMETRY_KEYS:
        if key in data and data[key] != PRESETS[mode][key]:
            raise ValueError(f"board geometry cannot be overridden: {key}")
    overrides = {
        key: value
        for key, value in data.items()
        if key not in {"mode", "profile", "player_count"} and key not in LOCKED_GEOMETRY_KEYS
    }
    return build_config(mode, profile, player_count, overrides)


def get_start_indices(config: dict[str, Any]) -> list[int]:
    """Return diagonal two-player starts or clockwise starts otherwise."""
    key = "start_indices_2p" if config["player_count"] == 2 else "start_indices_4p"
    return list(config[key][: config["player_count"]])


def clone_json_value(value: Any) -> Any:
    """Copy JSON-style containers without generic deepcopy overhead."""
    if isinstance(value, dict):
        return {key: clone_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clone_json_value(item) for item in value]
    return value


def clone_event(event: dict[str, Any]) -> dict[str, Any]:
    """Return an independent copy of one canonical game event."""
    return {
        "type": event["type"],
        "turn": event["turn"],
        "player": event["player"],
        "data": clone_json_value(event["data"]),
    }


def make_event(
    event_type: str,
    turn: int,
    player: int | None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create one JSON-serializable game event."""
    if event_type not in EVENT_TYPES:
        raise ValueError(f"unknown event type: {event_type}")
    return {
        "type": event_type,
        "turn": turn,
        "player": player,
        "data": dict(data or {}),
    }
