"""Shared argument parsing, setup merging, and safe terminal input helpers."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any, Callable

from .contracts import LOCKED_GEOMETRY_KEYS, PRESETS, build_config, config_from_dict


InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]


def create_parser() -> argparse.ArgumentParser:
    """Create the identical full-featured parser used by both paradigms."""
    parser = argparse.ArgumentParser(description="Configurable multiplayer Ludo showcase.")
    parser.add_argument("--config", type=Path, help="Load match settings from a JSON preset.")
    parser.add_argument("--wizard", action="store_true", help="Interactively configure every match setting.")
    parser.add_argument("--mode", choices=("quick", "classic"), default=None)
    parser.add_argument("--profile", choices=("showcase", "classic"), default=None)
    parser.add_argument("--players", dest="player_count", type=int, choices=(2, 3, 4), default=None)
    parser.add_argument("--tokens", dest="tokens_per_player", type=int, choices=(1, 2, 3, 4), default=None)
    parser.add_argument("--name", dest="names", action="append", default=None)
    parser.add_argument("--seat", dest="seat", action="append", choices=("human", "bot"), default=None)
    parser.add_argument("--blockades", choices=("none", "strict", "safe_pair"), default=None)
    parser.add_argument("--kill-to-enter", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--podium-mode", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--exact-home-roll", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--triple-six-forfeit", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--safe-tiles", dest="safe_tiles_enabled", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--bonus-on-capture", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--bonus-on-home", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--max-turns", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--auto-delay", type=float, default=None)
    parser.add_argument("--speed", choices=("slow", "normal", "fast"), default=None)
    parser.add_argument("--commentary", choices=("gameplay", "code", "both", "off"), default=None)
    parser.add_argument("--ui", choices=("cli", "gui"), default=None)
    parser.add_argument("--autoplay", action="store_true", default=None)
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color codes.")
    return parser


def load_json_setup(path: Path) -> dict[str, Any]:
    """Load and validate a JSON setup while preserving seat metadata."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not load configuration: {exc}") from exc
    config_data = {
        key: value
        for key, value in data.items()
        if key not in {"names", "kinds", "autoplay", "config"}
    }
    config = config_from_dict(config_data)
    settings = dict(config_data)
    settings["mode"] = config["mode"]
    settings["profile"] = config["profile"]
    settings["player_count"] = config["player_count"]
    return {
        **settings,
        "config": config,
        "names": data.get("names"),
        "kinds": data.get("kinds"),
        "autoplay": data.get("autoplay"),
    }


def merge_setup(*sources: dict[str, Any] | None) -> dict[str, Any]:
    """Merge defaults, JSON, wizard, and CLI values in ascending precedence."""
    settings: dict[str, Any] = {}
    names: list[str] | None = None
    kinds: list[str] | None = None
    autoplay: bool | None = None
    for source in sources:
        if not source:
            continue
        for key, value in source.items():
            if key in {"config", "names", "kinds", "seat", "autoplay", "no_color", "speed"}:
                continue
            if key in LOCKED_GEOMETRY_KEYS or value is None:
                continue
            settings[key] = value
        if source.get("names") is not None:
            names = list(source["names"])
        if source.get("kinds") is not None:
            kinds = list(source["kinds"])
        if source.get("seat") is not None:
            kinds = list(source["seat"])
        if source.get("autoplay") is not None:
            autoplay = bool(source["autoplay"])

    mode = settings.pop("mode", "quick")
    profile = settings.pop("profile", "showcase")
    player_count = settings.pop("player_count", 2)
    config = build_config(mode, profile, int(player_count), settings)
    normalized_names = normalize_player_names(names or [], int(player_count))
    default_kind = "bot" if autoplay else "human"
    normalized_kinds = normalize_player_kinds(kinds or [], int(player_count), default_kind)
    return {
        "config": config,
        "names": normalized_names,
        "kinds": normalized_kinds,
        "autoplay": bool(autoplay),
    }


def resolve_cli_setup(
    args: argparse.Namespace,
    input_func: InputFunction = input,
    output_func: OutputFunction = print,
) -> dict[str, Any] | None:
    """Resolve JSON, wizard, and CLI settings using the documented precedence."""
    json_setup = load_json_setup(args.config) if args.config else {}
    combined = dict(json_setup)
    for key, value in vars(args).items():
        if key in {"config", "no_color", "speed", "wizard"} or value is None:
            continue
        combined[key] = value
    if args.auto_delay is None and args.speed is not None:
        combined["auto_delay"] = {"slow": 0.8, "normal": 0.35, "fast": 0.05}[args.speed]
    if args.wizard:
        wizard = run_wizard(combined, input_func, output_func)
        return merge_setup(wizard) if wizard is not None else None
    if combined.get("mode") is None:
        mode = read_choice("Mode", {"1": "quick", "2": "classic"}, "quick", input_func, output_func)
        if mode is None:
            return None
        combined["mode"] = mode
    return merge_setup(combined)


def normalize_player_names(names: list[str], count: int) -> list[str]:
    """Strip names, fill blanks, and make duplicate display names unique."""
    normalized: list[str] = []
    for index in range(count):
        raw = names[index].strip() if index < len(names) else ""
        candidate = raw or f"Player {index + 1}"
        if candidate in normalized:
            suffix = index + 1
            candidate = f"{raw or f'Player {index + 1}'} ({suffix})"
            while candidate in normalized:
                suffix += 1
                candidate = f"{raw or f'Player {index + 1}'} ({suffix})"
        normalized.append(candidate)
    return normalized


def normalize_player_kinds(
    kinds: list[str],
    count: int,
    default: str = "human",
) -> list[str]:
    """Validate human/bot seats and pad omitted seats with the default."""
    if len(kinds) > count:
        raise ValueError("too many seat kinds for the player count")
    normalized = list(kinds)
    if any(kind not in {"human", "bot"} for kind in normalized):
        raise ValueError("seat kinds must be 'human' or 'bot'")
    normalized.extend([default] * (count - len(normalized)))
    return normalized


def read_int(
    prompt: str,
    minimum: int,
    maximum: int,
    current: int,
    input_func: InputFunction = input,
    output_func: OutputFunction = print,
) -> int | None:
    """Read an integer in range, returning None on EOF or interruption."""
    while True:
        try:
            raw = input_func(f"{prompt} [{minimum}-{maximum}] (default {current}): ").strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if not raw:
            return current
        try:
            value = int(raw)
        except ValueError:
            output_func("Please enter a whole number.")
            continue
        if minimum <= value <= maximum:
            return value
        output_func(f"Please enter a number from {minimum} to {maximum}.")


def read_bool(
    prompt: str,
    current: bool,
    input_func: InputFunction = input,
    output_func: OutputFunction = print,
) -> bool | None:
    """Read a yes/no setting, returning None on EOF or interruption."""
    default = "y" if current else "n"
    while True:
        try:
            raw = input_func(f"{prompt} [y/n] (default {default}): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None
        if not raw:
            return current
        if raw in {"y", "yes", "1", "true"}:
            return True
        if raw in {"n", "no", "0", "false"}:
            return False
        output_func("Please enter y or n.")


def read_choice(
    prompt: str,
    choices: dict[str, str],
    current: str,
    input_func: InputFunction = input,
    output_func: OutputFunction = print,
) -> str | None:
    """Read one value from a labeled choice map."""
    labels = "/".join(choices)
    while True:
        try:
            raw = input_func(f"{prompt} ({labels}, default {current}): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None
        if not raw:
            return current
        if raw in choices:
            return choices[raw]
        if raw in choices.values():
            return raw
        output_func(f"Please choose {labels}.")


def run_wizard(
    base: dict[str, Any],
    input_func: InputFunction = input,
    output_func: OutputFunction = print,
) -> dict[str, Any] | None:
    """Prompt only for settings not already supplied by higher-priority sources."""
    settings = dict(base)
    output_func("Ludo setup wizard (press Enter to keep a default).")

    mode = settings.get("mode")
    if mode is None:
        mode = read_choice("Mode", {"1": "quick", "2": "classic"}, "quick", input_func, output_func)
        if mode is None:
            return None
        settings["mode"] = mode

    profile = settings.get("profile")
    if profile is None:
        profile = read_choice(
            "Rule profile",
            {"1": "showcase", "2": "classic"},
            "showcase",
            input_func,
            output_func,
        )
        if profile is None:
            return None
        settings["profile"] = profile

    player_count = settings.get("player_count")
    if player_count is None:
        player_count = read_int("Players", 2, 4, 2, input_func, output_func)
        if player_count is None:
            return None
        settings["player_count"] = player_count

    preset = PRESETS[mode]
    if settings.get("tokens_per_player") is None:
        tokens = read_int(
            "Tokens per player",
            1,
            4,
            int(preset["tokens_per_player"]),
            input_func,
            output_func,
        )
        if tokens is None:
            return None
        settings["tokens_per_player"] = tokens

    showcase = profile == "showcase"
    choice_defaults = (
        ("blockades", "Blockade rule", {"1": "none", "2": "strict", "3": "safe_pair"}, "safe_pair" if showcase else "none"),
        ("commentary", "Commentary", {"1": "gameplay", "2": "code", "3": "both", "4": "off"}, "gameplay"),
        ("ui", "Interface", {"1": "cli", "2": "gui"}, "cli"),
    )
    for key, label, choices, default in choice_defaults:
        if settings.get(key) is None:
            value = read_choice(label, choices, default, input_func, output_func)
            if value is None:
                return None
            settings[key] = value

    boolean_defaults = (
        ("kill_to_enter", "Kill-to-Enter", showcase),
        ("podium_mode", "Podium mode", showcase),
        ("exact_home_roll", "Exact home roll", True),
        ("triple_six_forfeit", "Triple-six forfeit", True),
        ("safe_tiles_enabled", "Safe tiles", True),
        ("bonus_on_capture", "Capture bonus", True),
        ("bonus_on_home", "Home bonus", True),
    )
    for key, label, default in boolean_defaults:
        if settings.get(key) is None:
            value = read_bool(label, default, input_func, output_func)
            if value is None:
                return None
            settings[key] = value

    if settings.get("max_turns") is None:
        max_turns = read_int(
            "Maximum turns",
            1,
            1_000_000,
            int(preset["default_max_turns"]),
            input_func,
            output_func,
        )
        if max_turns is None:
            return None
        settings["max_turns"] = max_turns

    if settings.get("auto_delay") is None:
        while True:
            try:
                raw = input_func(f"Auto-play delay in seconds (default 0.35): ").strip()
            except (EOFError, KeyboardInterrupt):
                return None
            if not raw:
                settings["auto_delay"] = 0.35
                break
            try:
                delay = float(raw)
            except ValueError:
                output_func("Please enter a non-negative number.")
                continue
            if math.isfinite(delay) and delay >= 0:
                settings["auto_delay"] = delay
                break
            output_func("Please enter a finite non-negative number.")

    if settings.get("autoplay") is None:
        autoplay = read_bool("Auto-play every seat", False, input_func, output_func)
        if autoplay is None:
            return None
        settings["autoplay"] = autoplay

    count = int(settings["player_count"])
    if not settings.get("names"):
        names: list[str] = []
        for index in range(count):
            try:
                name = input_func(f"Player {index + 1} name (default Player {index + 1}): ").strip()
            except (EOFError, KeyboardInterrupt):
                return None
            names.append(name)
        settings["names"] = names

    settings["names"] = normalize_player_names(list(settings.get("names") or []), count)
    if not settings.get("kinds") and not settings.get("seat"):
        kinds: list[str] = []
        default_kind = "bot" if settings["autoplay"] else "human"
        for index in range(count):
            kind = read_choice(
                f"Player {index + 1} type",
                {"1": "human", "2": "bot"},
                default_kind,
                input_func,
                output_func,
            )
            if kind is None:
                return None
            kinds.append(kind)
        settings["kinds"] = kinds

    return settings


_ANSI_PATTERN = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from terminal text."""
    return _ANSI_PATTERN.sub("", text)
