#!/usr/bin/env python3
"""Class-based multiplayer Ludo command-line game."""

from __future__ import annotations

import argparse
import os
import random
import sys
from typing import Any


class Token:
    """A single movable token owned by a player."""

    def __init__(self, token_idx: int, label: str) -> None:
        """Initialize a token in the base."""
        self.token_idx = token_idx
        self.label = label
        self.steps = -1

    def is_in_base(self) -> bool:
        """Return whether the token is in the base."""
        return self.steps == -1

    def is_finished(self, home_finish: int) -> bool:
        """Return whether the token has reached home."""
        return self.steps == home_finish

    def is_in_home_stretch(self, track_len: int, home_finish: int) -> bool:
        """Return whether the token is in its private home stretch."""
        return track_len - 1 <= self.steps < home_finish

    def can_move(self, roll: int, home_finish: int) -> bool:
        """Return whether this roll can legally move the token."""
        if self.steps == -1:
            return roll == 6
        if self.steps == home_finish:
            return False
        return self.steps + roll <= home_finish

    def target_steps(self, roll: int) -> int:
        """Return the resulting steps for a roll."""
        if self.steps == -1 and roll == 6:
            return 0
        return self.steps + roll

    def move_to(self, new_steps: int) -> None:
        """Move the token to a new coordinate."""
        self.steps = new_steps

    def send_to_base(self) -> None:
        """Reset the token to base."""
        self.steps = -1


class Player:
    """A player and all tokens belonging to that seat."""

    def __init__(self, index: int, name: str, color_name: str, color_code: str,
                 prefix: str, start_index: int, tokens_per_player: int) -> None:
        """Initialize a player and its tokens."""
        self.index = index
        self.name = name
        self.color_name = color_name
        self.color_code = color_code
        self.prefix = prefix
        self.start_index = start_index
        self.captures_made = 0
        self.tokens = [Token(i, f"{prefix}{i + 1}") for i in range(tokens_per_player)]

    def all_finished(self, home_finish: int) -> bool:
        """Return whether every token is home."""
        return all(token.is_finished(home_finish) for token in self.tokens)

    def finished_count(self, home_finish: int) -> int:
        """Return the number of tokens at home."""
        return sum(token.is_finished(home_finish) for token in self.tokens)

    def get_valid_token_indices(self, roll: int, home_finish: int) -> list[int]:
        """Return all token indices that can legally move."""
        return [token.token_idx for token in self.tokens if token.can_move(roll, home_finish)]


class Board:
    """Board geometry and coordinate translation for a game preset."""

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

    def __init__(self, mode: str) -> None:
        """Initialize board geometry from a preset."""
        if mode not in self.PRESETS:
            raise ValueError("Unknown game mode")
        preset = self.PRESETS[mode]
        self.mode = mode
        self.track_len = int(preset["track_len"])
        self.home_len = int(preset["home_len"])
        self.tokens_per_player = int(preset["tokens_per_player"])
        self.outer_last_step = int(preset["outer_last_step"])
        self.home_finish = int(preset["home_finish"])
        self.safe_tiles = preset["safe_tiles"]
        self.default_max_turns = int(preset["default_max_turns"])

    def get_start_indices(self, num_players: int) -> list[int]:
        """Return clockwise or diagonal starts for the player count."""
        preset = self.PRESETS[self.mode]
        if num_players == 2:
            return list(preset["start_indices_2p"])
        return list(preset["start_indices_4p"][:num_players])

    def get_global_pos(self, start_index: int, steps: int) -> int | None:
        """Translate personal steps to a shared outer-track index."""
        if steps < 0 or steps > self.outer_last_step:
            return None
        return (start_index + steps) % self.track_len

    def is_safe_tile(self, global_pos: int | None) -> bool:
        """Return whether a global tile is safe from capture."""
        return global_pos is not None and global_pos in self.safe_tiles

    def format_position(self, start_index: int, steps: int) -> str:
        """Return a compact human-readable token position."""
        if steps == -1:
            return "BASE"
        if steps == self.home_finish:
            return "HOME"
        if steps >= self.track_len - 1:
            return f"H{steps - (self.track_len - 1) + 1}"
        global_pos = self.get_global_pos(start_index, steps)
        return f"T{global_pos:02d}" if global_pos is not None else "BASE"


class CLIRenderer:
    """Terminal rendering for the Ludo CLI."""

    def __init__(self, use_color: bool = True) -> None:
        """Initialize renderer with platform-safe ANSI settings."""
        self.use_color, self.use_unicode = init_terminal_colors(use_color)

    def colorize(self, text: str, ansi_code: str) -> str:
        """Apply ANSI styling unless color is disabled."""
        if not self.use_color:
            return text
        return f"{ansi_code}{text}\033[0m"

    def render_board(self, game: LudoGame) -> str:
        """Render the outer track and player status panel."""
        lines: list[str] = []
        lines.append(self.colorize(f"LUDO - {game.board.mode.upper()} MODE", "\033[96m"))
        lines.append(f"Turn {game.turn_count}/{game.max_turns} | {game.last_event}")
        quadrants = game.board.track_len // 4
        tile_to_tokens: dict[int, list[str]] = {}
        for player in game.players:
            for token in player.tokens:
                global_pos = game.board.get_global_pos(player.start_index, token.steps)
                if global_pos is not None:
                    tile_to_tokens.setdefault(global_pos, []).append(token.label)
        for q in range(4):
            start = q * quadrants
            stop = start + quadrants
            chunks: list[str] = []
            for tile in range(start, stop):
                labels = ",".join(tile_to_tokens.get(tile, []))
                marker = "*" if tile in game.board.safe_tiles else " "
                if labels:
                    chunks.append(f"[{marker}{tile:02d}:{labels}]")
                else:
                    chunks.append(f"[{marker}{tile:02d}]")
            lines.append(" ".join(chunks))
        lines.append("Player Status:")
        for player in game.players:
            active = ">" if player.index == game.current_player_index and game.status == "PLAYING" else " "
            positions = ", ".join(
                f"{token.label}:{game.board.format_position(player.start_index, token.steps)}"
                for token in player.tokens
            )
            home_slots = ["." for _ in range(game.board.home_len)]
            for token in player.tokens:
                if game.board.track_len - 1 <= token.steps < game.board.home_finish:
                    slot = token.steps - (game.board.track_len - 1)
                    home_slots[slot] = player.prefix
            finished = player.finished_count(game.board.home_finish)
            bar = "[" + " ".join(home_slots) + "]"
            tag = self.colorize(f"{player.color_name}", player.color_code)
            lines.append(f"{active} {tag} {player.name}: {positions} {bar} ({finished}/{len(player.tokens)})")
        return "\n".join(lines)

    def format_move_options(self, game: LudoGame, player: Player,
                            valid_indices: list[int], roll: int) -> str:
        """Render numbered move choices with live previews."""
        lines: list[str] = [f"Choose a move for [die {roll}]:"]
        for number, token_idx in enumerate(valid_indices, 1):
            preview = game.preview_move(player.index, token_idx, roll)
            annotation = preview["annotation"]
            lines.append(f"[{number}] Move {preview['label']}: {preview['old_position']} -> "
                         f"{preview['new_position']} {annotation}")
        return "\n".join(lines)

    def render_game_over(self, game: LudoGame) -> str:
        """Render a winner, draw, or quit scoreboard."""
        lines = [self.render_board(game)]
        if game.status == "WON" and game.winner_index is not None:
            winner = game.players[game.winner_index]
            lines.append(self.colorize(f"WINNER: {winner.name} ({winner.color_name})", "\033[1m"))
        elif game.status == "DRAW":
            lines.append(self.colorize(f"DRAW: {game.draw_reason}", "\033[1m"))
        elif game.status == "QUIT":
            lines.append("Game quit. Goodbye!")
        return "\n".join(lines)


def init_terminal_colors(use_color: bool) -> tuple[bool, bool]:
    """Enable ANSI where supported and select a safe character set."""
    if use_color and os.name == "nt":
        os.system("")
    color_enabled = bool(use_color)
    encoding = (sys.stdout.encoding or "").lower()
    unicode_enabled = encoding.startswith("utf")
    return color_enabled, unicode_enabled


class LudoGame:
    """Orchestrates Ludo state transitions and interactive play."""

    def __init__(self, mode: str, player_names: list[str], max_turns: int | None = None,
                 seed: int | None = None) -> None:
        """Initialize a game with isolated RNG state."""
        self.board = Board(mode)
        self.max_turns = max_turns if max_turns is not None else self.board.default_max_turns
        self.rng = random.Random(seed)
        self.current_player_index = 0
        self.turn_count = 0
        self.consecutive_sixes = 0
        self.status = "PLAYING"
        self.winner_index: int | None = None
        self.draw_reason: str | None = None
        self.last_event = "Game started! Roll the die to begin."
        starts = self.board.get_start_indices(len(player_names))
        specs = (
            ("RED", "\033[91m", "R"),
            ("GREEN", "\033[92m", "G"),
            ("YELLOW", "\033[93m", "Y"),
            ("BLUE", "\033[94m", "B"),
        )
        self.players = [
            Player(i, name, specs[i][0], specs[i][1], specs[i][2],
                   starts[i], self.board.tokens_per_player)
            for i, name in enumerate(player_names)
        ]

    def current_player(self) -> Player:
        """Return the active player."""
        return self.players[self.current_player_index]

    def roll_die(self) -> int:
        """Roll an isolated six-sided die."""
        return self.rng.randint(1, 6)

    def get_valid_moves(self, roll: int) -> list[int]:
        """Return valid token indices for the active player."""
        return self.current_player().get_valid_token_indices(roll, self.board.home_finish)

    def preview_move(self, player_idx: int, token_idx: int, roll: int) -> dict[str, Any]:
        """Compute a move description without changing state."""
        player = self.players[player_idx]
        token = player.tokens[token_idx]
        old_steps = token.steps
        new_steps = token.target_steps(roll)
        old_position = self.board.format_position(player.start_index, old_steps)
        new_position = self.board.format_position(player.start_index, new_steps)
        captured: list[str] = []
        global_pos = self.board.get_global_pos(player.start_index, new_steps)
        if global_pos is not None and not self.board.is_safe_tile(global_pos):
            for opponent in self.players:
                if opponent.index == player_idx:
                    continue
                for enemy in opponent.tokens:
                    if self.board.get_global_pos(opponent.start_index, enemy.steps) == global_pos:
                        captured.append(f"{opponent.name}'s {enemy.label}")
        reached_home = new_steps == self.board.home_finish
        safe = self.board.is_safe_tile(global_pos)
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
        if not annotation:
            annotation = ""
        return {
            "label": token.label,
            "old_position": old_position,
            "new_position": new_position,
            "captured": captured,
            "reached_home": reached_home,
            "safe": safe,
            "annotation": annotation,
        }

    def process_roll(self, roll: int) -> dict[str, Any]:
        """Resolve triple-sixes, valid moves, and auto-skip."""
        if roll == 6:
            self.consecutive_sixes += 1
            if self.consecutive_sixes == 3:
                self.consecutive_sixes = 0
                self.last_event = "TRIPLE_SIX_FORFEIT: Third consecutive six voided."
                self.advance_turn()
                return {"event": "TRIPLE_SIX_FORFEIT", "valid_moves": []}
        else:
            self.consecutive_sixes = 0
        valid_moves = self.get_valid_moves(roll)
        if not valid_moves:
            self.consecutive_sixes = 0
            self.last_event = f"No valid moves for roll {roll}. Turn automatically skipped."
            self.advance_turn()
            return {"event": "NO_VALID_MOVES", "valid_moves": []}
        self.last_event = f"Rolled {roll}. Select a move."
        return {"event": "SELECT_MOVE", "valid_moves": valid_moves}

    def apply_move(self, token_idx: int, roll: int) -> dict[str, Any]:
        """Apply a move, captures, win, and bonus-turn rules."""
        player = self.current_player()
        token = player.tokens[token_idx]
        if not token.can_move(roll, self.board.home_finish):
            raise ValueError("Illegal move")
        old_steps = token.steps
        new_steps = token.target_steps(roll)
        token.move_to(new_steps)
        captured: list[str] = []
        global_pos = self.board.get_global_pos(player.start_index, new_steps)
        if global_pos is not None and not self.board.is_safe_tile(global_pos):
            for opponent in self.players:
                if opponent.index == player.index:
                    continue
                for enemy in opponent.tokens:
                    enemy_pos = self.board.get_global_pos(opponent.start_index, enemy.steps)
                    if enemy_pos == global_pos:
                        enemy.send_to_base()
                        player.captures_made += 1
                        captured.append(f"{opponent.name}'s {enemy.label}")
        reached_home = new_steps == self.board.home_finish
        won = player.all_finished(self.board.home_finish)
        if won:
            self.status = "WON"
            self.winner_index = player.index
            self.last_event = f"{player.name} wins!"
        bonus_turn = not won and (roll == 6 or bool(captured) or reached_home)
        if won:
            pass
        elif bonus_turn:
            self.last_event = f"Bonus roll for {player.name}: 6, capture, or reached Home."
        else:
            self.consecutive_sixes = 0
        return {
            "old_steps": old_steps,
            "new_steps": new_steps,
            "captured": captured,
            "reached_home": reached_home,
            "won": won,
            "bonus_turn": bonus_turn,
        }

    def advance_turn(self) -> None:
        """Advance to the next player and enforce the turn cap."""
        self.consecutive_sixes = 0
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.turn_count += 1
        if self.turn_count >= self.max_turns and self.status == "PLAYING":
            self.status = "DRAW"
            self.draw_reason = "Maximum turn limit reached"
            self.last_event = self.draw_reason

    def declare_mutual_draw(self) -> None:
        """Declare a mutual-agreement draw."""
        self.status = "DRAW"
        self.draw_reason = "Mutual agreement"
        self.last_event = self.draw_reason

    def export_canonical_state(self) -> dict[str, Any]:
        """Return a JSON-serializable canonical snapshot."""
        return {
            "mode": self.board.mode,
            "track_len": self.board.track_len,
            "home_len": self.board.home_len,
            "home_finish": self.board.home_finish,
            "max_turns": self.max_turns,
            "turn_count": self.turn_count,
            "current_player": self.current_player_index,
            "consecutive_sixes": self.consecutive_sixes,
            "status": self.status,
            "winner_index": self.winner_index,
            "draw_reason": self.draw_reason,
            "players": [
                {
                    "index": player.index,
                    "name": player.name,
                    "color": player.color_name,
                    "start_index": player.start_index,
                    "captures_made": player.captures_made,
                    "tokens": [
                        {"label": token.label, "steps": token.steps}
                        for token in player.tokens
                    ],
                }
                for player in self.players
            ],
        }

    def run_cli(self, renderer: CLIRenderer) -> None:
        """Run the interactive command-line turn loop."""
        if self.status != "PLAYING":
            print(renderer.render_game_over(self))
            return
        while self.status == "PLAYING":
            if self.turn_count >= self.max_turns:
                self.status = "DRAW"
                self.draw_reason = "Maximum turn limit reached"
                break
            print()
            print(renderer.render_board(self))
            player = self.current_player()
            while True:
                try:
                    raw = input(f"{player.name}, press ENTER to roll ('draw'/'quit'): ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nInput ended. Exiting gracefully.")
                    self.status = "QUIT"
                    return
                command = raw.lower()
                if command == "":
                    break
                if command in ("r", "roll"):
                    break
                if command in ("draw",):
                    accepted = prompt_mutual_draw(self, player.index)
                    if accepted:
                        self.declare_mutual_draw()
                        break
                    print("Draw declined. Turn continues.")
                    continue
                if command in ("q", "quit"):
                    if prompt_yes_no("Confirm quit? (y/n): ", "Invalid confirmation. Enter y or n."):
                        self.status = "QUIT"
                        break
                    print("Quit cancelled.")
                    continue
                print("Invalid command. Press ENTER to roll, or type 'draw' or 'quit'.")
            if self.status != "PLAYING":
                break
            roll = self.roll_die()
            print(f"{player.name} rolled [{roll}]")
            result = self.process_roll(roll)
            if result["valid_moves"]:
                valid = result["valid_moves"]
                print(renderer.format_move_options(self, player, valid, roll))
                token_idx = prompt_move_choice(valid)
                move = self.apply_move(token_idx, roll)
                if move["captured"]:
                    self.last_event = f"Captured: {', '.join(move['captured'])}"
                elif move["reached_home"]:
                    self.last_event = f"{player.name}'s token reached HOME."
                elif move["bonus_turn"]:
                    self.last_event = f"Bonus roll for {player.name}."
                if not move["bonus_turn"] and self.status == "PLAYING":
                    self.advance_turn()
        print()
        print(renderer.render_game_over(self))


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


def prompt_mutual_draw(game: LudoGame, proposer_idx: int) -> bool:
    """Ask every other player to accept or decline a draw."""
    for player in game.players:
        if player.index == proposer_idx:
            continue
        if not prompt_yes_no(f"{player.name}, accept draw? (y/n): ",
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
    """Run the class-based Ludo application."""
    args = parse_args(argv)
    mode, names = prompt_setup(args.mode)
    game = LudoGame(mode, names, args.max_turns, args.seed)
    renderer = CLIRenderer(use_color=not args.no_color)
    try:
        game.run_cli(renderer)
    except (EOFError, KeyboardInterrupt):
        print("\nInput ended. Exiting gracefully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
