"""Shared JSON-snapshot presentation helpers for CLI and GUI adapters."""

from __future__ import annotations

import os
import sys
from typing import Any

from .contracts import PLAYER_SPECS


def terminal_settings(use_color: bool) -> tuple[bool, bool]:
    """Enable Windows VT100 when needed and detect Unicode-safe output."""
    if os.name == "nt" and use_color:
        os.system("")
    encoding = str(getattr(sys.stdout, "encoding", "") or "").lower()
    return use_color, "utf" in encoding


def colorize(text: str, ansi_code: str, use_color: bool) -> str:
    """Apply one ANSI color only when color output is enabled."""
    if not use_color:
        return text
    return f"{ansi_code}{text}\033[0m"


def _position(config: dict[str, Any], start_index: int, steps: int) -> str:
    """Format one token coordinate from canonical state."""
    if steps == -1:
        return "BASE"
    if steps == config["home_finish"]:
        return "HOME"
    if steps >= config["track_len"] - 1:
        return f"H{steps - (config['track_len'] - 1) + 1}"
    return f"T{(start_index + steps) % config['track_len']:02d}"


def render_board(
    snapshot: dict[str, Any],
    use_color: bool = True,
    use_unicode: bool = True,
) -> str:
    """Render a canonical snapshot as a stable cross-platform CLI board."""
    config = snapshot["config"]
    players = snapshot["players"]
    current = snapshot["current_player"]
    current_name = players[current]["name"] if current is not None else "None"
    title = f"LUDO - {config['mode'].upper()} / {config['profile'].upper()}"
    lines = [
        colorize(title, "\033[96m", use_color),
        f"Turn {snapshot['turn_count']}/{snapshot['max_turns']} | Current: {current_name} | {snapshot['status']}",
        (
            f"Rules: blockades={config['blockades']} | kill-to-enter={config['kill_to_enter']} | "
            f"podium={config['podium_mode']} | tokens={config['tokens_per_player']}"
        ),
        "Shared track (* = safe):",
    ]
    tile_tokens: dict[int, list[str]] = {}
    for player in players:
        for token in player["tokens"]:
            steps = int(token["steps"])
            if 0 <= steps <= config["outer_last_step"]:
                tile = (player["start_index"] + steps) % config["track_len"]
                tile_tokens.setdefault(tile, []).append(token["label"])

    safe_tiles = set(config["safe_tiles"]) if config["safe_tiles_enabled"] else set()
    marker = "★" if use_unicode else "*"
    quadrants = int(config["track_len"]) // 4
    for quadrant in range(4):
        cells: list[str] = []
        for tile in range(quadrant * quadrants, (quadrant + 1) * quadrants):
            safe = marker if tile in safe_tiles else " "
            labels = ",".join(tile_tokens.get(tile, []))
            cells.append(f"T{tile:02d}{safe} {labels}".rstrip())
        lines.append(" | ".join(cells))

    lines.append("Private home lanes:")
    for player in players:
        home_tokens = [
            f"{token['label']}:{_position(config, player['start_index'], int(token['steps']))}"
            for token in player["tokens"]
            if int(token["steps"]) >= config["track_len"] - 1
        ]
        home_text = " ".join(home_tokens) if home_tokens else "-"
        name = colorize(player["name"], PLAYER_SPECS[player["index"]]["ansi"], use_color)
        lines.append(f"  {name}: {home_text}")

    lines.append("Players:")
    for player in players:
        kind = "BOT" if player["kind"] == "bot" else "HUMAN"
        token_text = " ".join(
            f"{token['label']}={_position(config, player['start_index'], int(token['steps']))}"
            for token in player["tokens"]
        )
        lines.append(
            f"  {player['name']} [{kind}] captures={player['captures_made']} | {token_text}"
        )
    lines.append(f"Last event: {snapshot['last_event']}")
    return "\n".join(lines)


def render_moves(
    previews: list[dict[str, Any]],
    use_color: bool = True,
    use_unicode: bool = True,
) -> str:
    """Render numbered legal moves with deterministic consequence labels."""
    lines: list[str] = []
    for index, preview in enumerate(previews, start=1):
        notes: list[str] = []
        if preview["old_steps"] == -1:
            notes.append("UNLOCK")
        if preview["captured"]:
            notes.append(f"CAPTURES {', '.join(preview['captured'])}")
        if preview["reached_home"]:
            notes.append("HOME")
        if preview["safe"]:
            notes.append("SAFE")
        if preview["wrapped"]:
            notes.append("LOOP")
        if preview["blockade_formed"]:
            notes.append("BLOCKADE")
        suffix = f" [{'; '.join(notes)}]" if notes else ""
        number = colorize(str(index), "\033[96m", use_color)
        lines.append(
            f"  {number}. {preview['label']}: {preview['old_position']} -> {preview['new_position']}{suffix}"
        )
    return "\n".join(lines)
