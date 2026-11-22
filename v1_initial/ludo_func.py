#!/usr/bin/env python3
"""Function-based multiplayer Ludo command-line game with zero classes."""

from __future__ import annotations

import argparse
import os
import random
import sys
from typing import Any


PRESETS: dict[str, dict[str, Any]] = {
    "quick": {
        "track_len": 28, "home_len": 4, "tokens_per_player": 2,
        "outer_last_step": 26, "home_finish": 31,
        "safe_tiles": frozenset({0, 7, 14, 21}),
        "start_indices_2p": [0, 14],
        "start_indices_4p": [0, 7, 14, 21],
        "default_max_turns": 100,
    },
    "classic": {
        "track_len": 52, "home_len": 5, "tokens_per_player": 4,
        "outer_last_step": 50, "home_finish": 56,
        "safe_tiles": frozenset({0, 8, 13, 21, 26, 34, 39, 47}),
        "start_indices_2p": [0, 26],
        "start_indices_4p": [0, 13, 26, 39],
        "default_max_turns": 250,
    },
}

PLAYER_SPECS: tuple[tuple[str, str, str], ...] = (
    ("RED", "\033[91m", "R"),
    ("GREEN", "\033[92m", "G"),
    ("YELLOW", "\033[93m", "Y"),
    ("BLUE", "\033[94m", "B"),
)


def get_start_indices(mode: str, num_players: int) -> list[int]:
    """Return diagonal starts for two players or clockwise starts otherwise."""
    preset = PRESETS[mode]
    if num_players == 2:
        return list(preset["start_indices_2p"])
    return list(preset["start_indices_4p"][:num_players])


def create_game_state(mode: str, player_names: list[str], max_turns: int | None = None,
                      seed: int | None = None) -> dict[str, Any]:
    """Create one centralized state dictionary for a match."""
    if mode not in PRESETS:
        raise ValueError("Unknown game mode")
    preset = PRESETS[mode]
    config = dict(preset)
    config["mode"] = mode
    starts = get_start_indices(mode, len(player_names))
    players: list[dict[str, Any]] = []
    for i, name in enumerate(player_names):
        color_name, color_code, prefix = PLAYER_SPECS[i]
        tokens = [
            {"token_idx": j, "label": f"{prefix}{j + 1}", "steps": -1}
            for j in range(int(config["tokens_per_player"]))
        ]
        players.append({
            "index": i,
            "name": name,
            "color_name": color_name,
            "color_code": color_code,
            "prefix": prefix,
            "start_index": starts[i],
            "captures_made": 0,
            "tokens": tokens,
        })
    return {
        "config": config,
        "max_turns": max_turns if max_turns is not None else int(config["default_max_turns"]),
        "rng": random.Random(seed),
        "current_player": 0,
        "turn_count": 0,
        "consecutive_sixes": 0,
        "status": "PLAYING",
        "winner_index": None,
        "draw_reason": None,
        "last_event": "Game started! Roll the die to begin.",
        "players": players,
    }


def get_global_pos(start_index: int, steps: int, track_len: int) -> int | None:
    """Translate personal steps to a shared outer-track position."""
    if steps < 0 or steps > track_len - 2:
        return None
    return (start_index + steps) % track_len


def is_safe_tile(global_pos: int | None, safe_tiles: frozenset[int]) -> bool:
    """Return whether a global tile prevents captures."""
    return global_pos is not None and global_pos in safe_tiles


def format_position(start_index: int, steps: int, track_len: int, home_finish: int) -> str:
    """Return a compact human-readable token position."""
    if steps == -1:
        return "BASE"
    if steps == home_finish:
        return "HOME"
    if steps >= track_len - 1:
        return f"H{steps - (track_len - 1) + 1}"
    global_pos = get_global_pos(start_index, steps, track_len)
    return f"T{global_pos:02d}" if global_pos is not None else "BASE"


def can_token_move(steps: int, roll: int, home_finish: int) -> bool:
    """Return whether a token may take the requested roll."""
    if steps == -1:
        return roll == 6
    if steps == home_finish:
        return False
    return steps + roll <= home_finish


def compute_target_steps(steps: int, roll: int) -> int:
    """Return the target steps, unlocking a base token on six."""
    if steps == -1 and roll == 6:
        return 0
    return steps + roll


def get_valid_moves(state: dict[str, Any], player_idx: int, roll: int) -> list[int]:
    """Return all valid token indices for a player and roll."""
    config = state["config"]
    player = state["players"][player_idx]
    result: list[int] = []
    for token in player["tokens"]:
        if can_token_move(token["steps"], roll, int(config["home_finish"])):
            result.append(int(token["token_idx"]))
    return result


def preview_move(state: dict[str, Any], player_idx: int, token_idx: int,
                 roll: int) -> dict[str, Any]:
    """Compute a move description without mutating game state."""
    config = state["config"]
    track_len = int(config["track_len"])
    home_finish = int(config["home_finish"])
    safe_tiles = config["safe_tiles"]
    player = state["players"][player_idx]
    token = player["tokens"][token_idx]
    old_steps = int(token["steps"])
    new_steps = compute_target_steps(old_steps, roll)
    old_position = format_position(player["start_index"], old_steps, track_len, home_finish)
    new_position = format_position(player["start_index"], new_steps, track_len, home_finish)
    captured: list[str] = []
    global_pos = get_global_pos(player["start_index"], new_steps, track_len)
    if global_pos is not None and not is_safe_tile(global_pos, safe_tiles):
        for opponent in state["players"]:
            if opponent["index"] == player_idx:
                continue
            for enemy in opponent["tokens"]:
                enemy_pos = get_global_pos(opponent["start_index"], enemy["steps"], track_len)
                if enemy_pos == global_pos:
                    captured.append(f"{opponent['name']}'s {enemy['label']}")
    reached_home = new_steps == home_finish
    safe = is_safe_tile(global_pos, safe_tiles)
    annotation = ""
    if old_steps == -1:
        annotation = "[UNLOCKS"
    if captured:
        annotation += (" " if annotation else "[") + f"CAPTURES {', '.join(captured)}!"
    if reached_home:
        annotation += (" " if annotation else "[") + "REACHES HOME!"
    if safe:
        annotation += (" " if annotation else "[") + "Safe *"
    if annotation:
        annotation += "]"
    return {
        "label": token["label"],
        "old_position": old_position,
        "new_position": new_position,
        "captured": captured,
        "reached_home": reached_home,
        "safe": safe,
        "annotation": annotation,
    }


def all_tokens_finished(player: dict[str, Any], home_finish: int) -> bool:
    """Return whether every token in a player is at home."""
    return all(int(token["steps"]) == home_finish for token in player["tokens"])


def export_canonical_state(state: dict[str, Any]) -> dict[str, Any]:
    """Return the exact JSON-serializable canonical snapshot used by parity tests."""
    config = state["config"]
    return {
        "mode": config["mode"] if "mode" in config else (
            "quick" if int(config["track_len"]) == 28 else "classic"
        ),
        "track_len": int(config["track_len"]),
        "home_len": int(config["home_len"]),
        "home_finish": int(config["home_finish"]),
        "max_turns": state["max_turns"],
        "turn_count": state["turn_count"],
        "current_player": state["current_player"],
        "consecutive_sixes": state["consecutive_sixes"],
        "status": state["status"],
        "winner_index": state["winner_index"],
        "draw_reason": state["draw_reason"],
        "players": [
            {
                "index": player["index"],
                "name": player["name"],
                "color": player["color_name"],
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


def roll_die(state: dict[str, Any]) -> int:
    """Roll the isolated six-sided die."""
    return state["rng"].randint(1, 6)


def advance_turn(state: dict[str, Any]) -> None:
    """Advance control and enforce the maximum-turn draw."""
    state["consecutive_sixes"] = 0
    state["current_player"] = (state["current_player"] + 1) % len(state["players"])
    state["turn_count"] += 1
    if state["turn_count"] >= state["max_turns"] and state["status"] == "PLAYING":
        state["status"] = "DRAW"
        state["draw_reason"] = "Maximum turn limit reached"
        state["last_event"] = state["draw_reason"]


def process_roll(state: dict[str, Any], roll: int) -> dict[str, Any]:
    """Resolve triple-sixes, valid moves, and auto-skip."""
    if roll == 6:
        state["consecutive_sixes"] += 1
        if state["consecutive_sixes"] == 3:
            state["consecutive_sixes"] = 0
            state["last_event"] = "TRIPLE_SIX_FORFEIT: Third consecutive six voided."
            advance_turn(state)
            return {"event": "TRIPLE_SIX_FORFEIT", "valid_moves": []}
    else:
        state["consecutive_sixes"] = 0
    valid_moves = get_valid_moves(state, state["current_player"], roll)
    if not valid_moves:
        state["consecutive_sixes"] = 0
        state["last_event"] = f"No valid moves for roll {roll}. Turn automatically skipped."
        advance_turn(state)
        return {"event": "NO_VALID_MOVES", "valid_moves": []}
    state["last_event"] = f"Rolled {roll}. Select a move."
    return {"event": "SELECT_MOVE", "valid_moves": valid_moves}


def apply_move(state: dict[str, Any], token_idx: int, roll: int) -> dict[str, Any]:
    """Apply a move, captures, win, and non-stacking bonus."""
    config = state["config"]
    track_len = int(config["track_len"])
    home_finish = int(config["home_finish"])
    safe_tiles = config["safe_tiles"]
    player = state["players"][state["current_player"]]
    token = player["tokens"][token_idx]
    if not can_token_move(int(token["steps"]), roll, home_finish):
        raise ValueError("Illegal move")
    old_steps = int(token["steps"])
    new_steps = compute_target_steps(old_steps, roll)
    token["steps"] = new_steps
    captured: list[str] = []
    global_pos = get_global_pos(player["start_index"], new_steps, track_len)
    if global_pos is not None and not is_safe_tile(global_pos, safe_tiles):
        for opponent in state["players"]:
            if opponent["index"] == player["index"]:
                continue
            for enemy in opponent["tokens"]:
                enemy_pos = get_global_pos(opponent["start_index"], enemy["steps"], track_len)
                if enemy_pos == global_pos:
                    enemy["steps"] = -1
                    player["captures_made"] += 1
                    captured.append(f"{opponent['name']}'s {enemy['label']}")
    reached_home = new_steps == home_finish
    won = all_tokens_finished(player, home_finish)
    if won:
        state["status"] = "WON"
        state["winner_index"] = player["index"]
        state["last_event"] = f"{player['name']} wins!"
    bonus_turn = not won and (roll == 6 or bool(captured) or reached_home)
    if not won and bonus_turn:
        state["last_event"] = f"Bonus roll for {player['name']}: 6, capture, or reached Home."
    elif not won:
        state["consecutive_sixes"] = 0
    return {
        "old_steps": old_steps,
        "new_steps": new_steps,
        "captured": captured,
        "reached_home": reached_home,
        "won": won,
        "bonus_turn": bonus_turn,
    }


def declare_mutual_draw(state: dict[str, Any]) -> None:
    """Declare a mutual-agreement draw."""
    state["status"] = "DRAW"
    state["draw_reason"] = "Mutual agreement"
    state["last_event"] = state["draw_reason"]


def init_terminal_colors(use_color: bool) -> tuple[bool, bool]:
    """Enable ANSI where supported and select a safe character set."""
    if use_color and os.name == "nt":
        os.system("")
    encoding = (sys.stdout.encoding or "").lower()
    return bool(use_color), encoding.startswith("utf")


def colorize(text: str, ansi_code: str, use_color: bool) -> str:
    """Apply ANSI styling only when enabled."""
    if not use_color:
        return text
    return f"{ansi_code}{text}\033[0m"


def render_board(state: dict[str, Any], use_color: bool, use_unicode: bool) -> str:
    """Render the outer track and player status panel."""
    config = state["config"]
    lines: list[str] = []
    lines.append(colorize(f"LUDO - {config['mode'].upper()} MODE", "\033[96m", use_color))
    lines.append(f"Turn {state['turn_count']}/{state['max_turns']} | {state['last_event']}")
    track_len = int(config["track_len"])
    quadrants = track_len // 4
    tile_to_tokens: dict[int, list[str]] = {}
    for player in state["players"]:
        for token in player["tokens"]:
            global_pos = get_global_pos(player["start_index"], token["steps"], track_len)
            if global_pos is not None:
                tile_to_tokens.setdefault(global_pos, []).append(token["label"])
    for quadrant in range(4):
        start = quadrant * quadrants
        chunks: list[str] = []
        for tile in range(start, start + quadrants):
            labels = ",".join(tile_to_tokens.get(tile, []))
            marker = "*" if tile in config["safe_tiles"] else " "
            chunks.append(f"[{marker}{tile:02d}:{labels}]" if labels else f"[{marker}{tile:02d}]")
        lines.append(" ".join(chunks))
    lines.append("Player Status:")
    for player in state["players"]:
        active = ">" if player["index"] == state["current_player"] and state["status"] == "PLAYING" else " "
        positions = ", ".join(
            f"{token['label']}:{format_position(player['start_index'], token['steps'], track_len, int(config['home_finish']))}"
            for token in player["tokens"]
        )
        home_slots = ["." for _ in range(int(config["home_len"]))]
        for token in player["tokens"]:
            if track_len - 1 <= token["steps"] < int(config["home_finish"]):
                slot = token["steps"] - (track_len - 1)
                home_slots[slot] = player["prefix"]
        finished = sum(token["steps"] == int(config["home_finish"]) for token in player["tokens"])
        tag = colorize(player["color_name"], player["color_code"], use_color)
        lines.append(f"{active} {tag} {player['name']}: {positions} "
                     f"[{' '.join(home_slots)}] ({finished}/{len(player['tokens'])})")
    return "\n".join(lines)


def format_move_options(state: dict[str, Any], valid_indices: list[int], roll: int,
                        use_color: bool, use_unicode: bool) -> str:
    """Render numbered move choices with live previews."""
    lines: list[str] = [f"Choose a move for [die {roll}]:"]
    player_idx = state["current_player"]
    for number, token_idx in enumerate(valid_indices, 1):
        preview = preview_move(state, player_idx, token_idx, roll)
        lines.append(f"[{number}] Move {preview['label']}: {preview['old_position']} -> "
                     f"{preview['new_position']} {preview['annotation']}")
    return "\n".join(lines)


def render_game_over(state: dict[str, Any], use_color: bool) -> str:
    """Render winner, draw, or quit scoreboard."""
    lines = [render_board(state, use_color, True)]
    if state["status"] == "WON" and state["winner_index"] is not None:
        winner = state["players"][state["winner_index"]]
        lines.append(colorize(f"WINNER: {winner['name']} ({winner['color_name']})", "\033[1m", use_color))
    elif state["status"] == "DRAW":
        lines.append(colorize(f"DRAW: {state['draw_reason']}", "\033[1m", use_color))
    elif state["status"] == "QUIT":
        lines.append("Game quit. Goodbye!")
    return "\n".join(lines)


def prompt_yes_no(prompt: str, error: str) -> bool:
    """Prompt until a valid yes/no answer is entered."""
    while True:
        try:
            answer = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nInput ended. Exiting gracefully.")
            return False
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print(error)


def prompt_mutual_draw(state: dict[str, Any], proposer_idx: int) -> bool:
    """Ask every other player to accept or decline a draw."""
    for player in state["players"]:
        if player["index"] == proposer_idx:
            continue
        if not prompt_yes_no(f"{player['name']}, accept draw? (y/n): ",
                             "Invalid confirmation. Enter y or n."):
            return False
    return True


def prompt_move_choice(valid_indices: list[int]) -> int:
    """Prompt for a valid numbered token choice."""
    while True:
        try:
            raw = input("Enter move number: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nInput ended. Exiting gracefully.")
            return valid_indices[0]
        try:
            choice = int(raw)
        except (TypeError, ValueError):
            print("Invalid move. Enter a number from the menu.")
            continue
        if 1 <= choice <= len(valid_indices):
            return valid_indices[choice - 1]
        print("Invalid move. Enter a number from the menu.")


def prompt_setup(cli_mode: str | None) -> tuple[str, list[str]]:
    """Prompt for mode, player count, and unique player names."""
    mode = cli_mode
    if mode is None:
        while True:
            try:
                raw = input("Select mode (1=Quick, 2=Classic): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nInput ended. Exiting gracefully.")
                return "quick", ["Player 1", "Player 2"]
            if raw in ("1", "quick"):
                mode = "quick"
                break
            if raw in ("2", "classic"):
                mode = "classic"
                break
            print("Invalid mode. Enter 1, 2, quick, or classic.")
    while True:
        try:
            raw = input("Enter number of players (2-4): ").strip()
            count = int(raw)
        except (EOFError, KeyboardInterrupt):
            print("\nInput ended. Exiting gracefully.")
            return mode, ["Player 1", "Player 2"]
        except ValueError:
            print("Invalid player count. Enter 2, 3, or 4.")
            continue
        if 2 <= count <= 4:
            break
        print("Invalid player count. Enter 2, 3, or 4.")
    names: list[str] = []
    used: set[str] = set()
    for i in range(count):
        try:
            raw = input(f"Enter name for Player {i + 1} (blank=Player {i + 1}): ").strip()
        except (EOFError, KeyboardInterrupt):
            raw = ""
        name = raw if raw else f"Player {i + 1}"
        base = name
        suffix = 2
        while name.lower() in used:
            name = f"{base} {suffix}"
            suffix += 1
        used.add(name.lower())
        names.append(name)
    return mode, names


def run_cli(state: dict[str, Any], use_color: bool, use_unicode: bool) -> None:
    """Run the interactive functional turn loop."""
    while state["status"] == "PLAYING":
        if state["turn_count"] >= state["max_turns"]:
            state["status"] = "DRAW"
            state["draw_reason"] = "Maximum turn limit reached"
            break
        print()
        print(render_board(state, use_color, use_unicode))
        player = state["players"][state["current_player"]]
        while True:
            try:
                raw = input(f"{player['name']}, press ENTER to roll ('draw'/'quit'): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nInput ended. Exiting gracefully.")
                state["status"] = "QUIT"
                return
            command = raw.lower()
            if command in ("", "r", "roll"):
                break
            if command == "draw":
                if prompt_mutual_draw(state, player["index"]):
                    declare_mutual_draw(state)
                    break
                print("Draw declined. Turn continues.")
                continue
            if command in ("q", "quit"):
                if prompt_yes_no("Confirm quit? (y/n): ", "Invalid confirmation. Enter y or n."):
                    state["status"] = "QUIT"
                    break
                print("Quit cancelled.")
                continue
            print("Invalid command. Press ENTER to roll, or type 'draw' or 'quit'.")
        if state["status"] != "PLAYING":
            break
        roll = roll_die(state)
        print(f"{player['name']} rolled [{roll}]")
        result = process_roll(state, roll)
        if result["valid_moves"]:
            valid = result["valid_moves"]
            print(format_move_options(state, valid, roll, use_color, use_unicode))
            token_idx = prompt_move_choice(valid)
            move = apply_move(state, token_idx, roll)
            if move["captured"]:
                state["last_event"] = f"Captured: {', '.join(move['captured'])}"
            elif move["reached_home"]:
                state["last_event"] = f"{player['name']}'s token reached HOME."
            elif move["bonus_turn"]:
                state["last_event"] = f"Bonus roll for {player['name']}."
            if not move["bonus_turn"] and state["status"] == "PLAYING":
                advance_turn(state)
    print()
    print(render_game_over(state, use_color))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Multiplayer Ludo CLI",
        usage="%(prog)s [-h] [--mode {quick,classic}] [--seed SEED] [--max-turns MAX_TURNS] [--no-color]",
    )
    parser.add_argument("--mode", choices=["quick", "classic"], help="Game preset mode")
    parser.add_argument("--seed", type=int, help="Integer RNG seed")
    parser.add_argument("--max-turns", type=int, help="Positive integer turn cap")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color codes")
    args = parser.parse_args(argv)
    if args.max_turns is not None and args.max_turns <= 0:
        parser.error("--max-turns must be a positive integer.")
    return args


def main(argv: list[str] | None = None) -> int:
    """Run the function-based Ludo application."""
    args = parse_args(argv)
    mode, names = prompt_setup(args.mode)
    state = create_game_state(mode, names, args.max_turns, args.seed)
    use_color, use_unicode = init_terminal_colors(not args.no_color)
    try:
        run_cli(state, use_color, use_unicode)
    except (EOFError, KeyboardInterrupt):
        print("\nInput ended. Exiting gracefully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
