"""Headless object-oriented Ludo rules and event emission."""

from __future__ import annotations

import copy
import random
from typing import Any

from ..shared.contracts import clone_event, make_event
from .models import Board, Player, Token


class LudoGame:
    """Own match state and apply every configurable Ludo rule."""

    def __init__(
        self,
        config: dict[str, Any],
        player_names: list[str],
        seed: int | None = None,
        player_kinds: list[str] | None = None,
    ) -> None:
        """Initialize a match with isolated RNG and JSON-friendly events."""
        self.config = copy.deepcopy(config)
        self.board = Board(self.config)
        self.max_turns = int(self.config["max_turns"])
        self.rng = random.Random(seed if seed is not None else self.config["seed"])
        self.current_player_index = 0
        self.turn_count = 0
        self.consecutive_sixes = 0
        self.status = "PLAYING"
        self.winner_index: int | None = None
        self.draw_reason: str | None = None
        self.finish_order: list[int] = []
        self.last_event = "Game started."
        self.events: list[dict[str, Any]] = []
        starts = self.board.get_start_indices()
        kinds = player_kinds or ["human"] * len(player_names)
        self.players = [
            Player(
                index,
                name,
                kinds[index],
                starts[index],
                self.board.tokens_per_player,
            )
            for index, name in enumerate(player_names)
        ]
        self._emit(
            "GAME_STARTED",
            None,
            {"mode": self.board.mode, "profile": self.config["profile"]},
        )

    def _emit(
        self,
        event_type: str,
        player_index: int | None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Append one deterministic event to the match stream."""
        self.events.append(make_event(event_type, self.turn_count, player_index, data))

    def current_player(self) -> Player:
        """Return the active player."""
        return self.players[self.current_player_index]

    def roll_die(self) -> int:
        """Roll the isolated six-sided die."""
        return self.rng.randint(1, 6)

    def _kill_locked(self, player: Player) -> bool:
        """Return whether a player still needs a capture to enter home."""
        return bool(self.config["kill_to_enter"]) and player.captures_made == 0

    def _compute_target(
        self,
        player: Player,
        token: Token,
        roll: int,
    ) -> tuple[int, bool, list[int]] | None:
        """Compute target steps, wrap status, and visited personal steps."""
        if token.is_in_base():
            if roll != 6:
                return None
            return 0, False, [0]
        if token.is_finished(self.board.home_finish):
            return None

        old_steps = token.steps
        raw_target = old_steps + roll
        if (
            self._kill_locked(player)
            and token.is_on_outer_track(self.board.outer_last_step)
            and raw_target >= self.board.track_len - 1
        ):
            lap_len = self.board.track_len - 1
            new_steps = raw_target % lap_len
            path = list(range(old_steps + 1, self.board.outer_last_step + 1))
            path.extend(range(0, new_steps + 1))
            return new_steps, True, path

        if raw_target > self.board.home_finish:
            if self.config["exact_home_roll"]:
                return None
            new_steps = self.board.home_finish
        else:
            new_steps = raw_target
        path = [
            steps
            for steps in range(old_steps + 1, new_steps + 1)
            if steps <= self.board.outer_last_step
        ]
        return new_steps, False, path

    def _global_path(self, player: Player, path: list[int]) -> list[int]:
        """Translate visited personal steps into shared tile indices."""
        positions: list[int] = []
        for steps in path:
            global_pos = self.board.get_global_pos(player.start_index, steps)
            if global_pos is not None:
                positions.append(global_pos)
        return positions

    def _strict_path_blocked(self, player: Player, path: list[int]) -> bool:
        """Return whether a strict enemy blockade intersects the move path."""
        if self.config["blockades"] != "strict":
            return False
        for global_pos in self._global_path(player, path):
            for opponent in self.players:
                if opponent.index != player.index and len(opponent.tokens_at(self.board, global_pos)) >= 2:
                    return True
        return False

    def _capturable_tokens(self, player: Player, global_pos: int | None) -> list[tuple[Player, Token]]:
        """Return opponent tokens that a landing would capture."""
        if global_pos is None or self.board.is_safe_tile(global_pos):
            return []
        captured: list[tuple[Player, Token]] = []
        for opponent in self.players:
            if opponent.index == player.index:
                continue
            tokens = opponent.tokens_at(self.board, global_pos)
            if self.config["blockades"] == "safe_pair" and len(tokens) >= 2:
                continue
            captured.extend((opponent, token) for token in tokens)
        return captured

    def preview_move(self, player_idx: int, token_idx: int, roll: int) -> dict[str, Any]:
        """Describe a move and its consequences without changing state."""
        player = self.players[player_idx]
        token = player.tokens[token_idx]
        target = self._compute_target(player, token, roll)
        if target is None:
            return {"legal": False, "reason": "Move is not legal for this roll."}
        new_steps, wrapped, path = target
        if self._strict_path_blocked(player, path):
            return {"legal": False, "reason": "A strict blockade blocks the path."}
        global_pos = self.board.get_global_pos(player.start_index, new_steps)
        captured = self._capturable_tokens(player, global_pos)
        reached_home = new_steps == self.board.home_finish
        friendly_before = len(player.tokens_at(self.board, global_pos)) if global_pos is not None else 0
        blockade_formed = global_pos is not None and friendly_before < 2 and friendly_before + 1 >= 2
        return {
            "legal": True,
            "label": token.label,
            "token_idx": token_idx,
            "old_steps": token.steps,
            "new_steps": new_steps,
            "old_position": self.board.format_position(player.start_index, token.steps),
            "new_position": self.board.format_position(player.start_index, new_steps),
            "global_pos": global_pos,
            "captured": [f"{owner.name}'s {victim.label}" for owner, victim in captured],
            "reached_home": reached_home,
            "safe": self.board.is_safe_tile(global_pos),
            "wrapped": wrapped,
            "blockade_formed": blockade_formed,
        }

    def get_valid_moves(self, roll: int) -> list[int]:
        """Return every legal token index for the active player and roll."""
        player = self.current_player()
        return [
            token.token_idx
            for token in player.tokens
            if self.preview_move(player.index, token.token_idx, roll)["legal"]
        ]

    def process_roll(self, roll: int) -> dict[str, Any]:
        """Resolve the die roll, triple-six penalty, and automatic skips."""
        player_index = self.current_player_index
        self._emit("DICE_ROLLED", player_index, {"roll": roll})
        if roll == 6:
            self.consecutive_sixes += 1
            if self.config["triple_six_forfeit"] and self.consecutive_sixes == 3:
                self.consecutive_sixes = 0
                self.last_event = "Third consecutive six forfeited."
                self._emit("TRIPLE_SIX_FORFEIT", player_index)
                self.advance_turn()
                return {"event": "TRIPLE_SIX_FORFEIT", "valid_moves": []}
        else:
            self.consecutive_sixes = 0

        valid_moves = self.get_valid_moves(roll)
        if not valid_moves:
            self.consecutive_sixes = 0
            self.last_event = f"No legal move for roll {roll}; turn skipped."
            self._emit("NO_VALID_MOVES", player_index, {"roll": roll})
            self.advance_turn()
            return {"event": "NO_VALID_MOVES", "valid_moves": []}
        self.last_event = f"Rolled {roll}; choose a token."
        return {"event": "SELECT_MOVE", "valid_moves": valid_moves}

    def apply_move(self, token_idx: int, roll: int) -> dict[str, Any]:
        """Apply one legal move, captures, finishing, and turn rewards."""
        player_index = self.current_player_index
        player = self.current_player()
        preview = self.preview_move(player_index, token_idx, roll)
        if not preview["legal"]:
            raise ValueError("Illegal move")
        token = player.tokens[token_idx]
        old_steps = token.steps
        new_steps = int(preview["new_steps"])
        token.move_to(new_steps)
        self._emit(
            "TOKEN_MOVED",
            player_index,
            {
                "token": token.label,
                "token_idx": token_idx,
                "roll": roll,
                "old_steps": old_steps,
                "new_steps": new_steps,
                "wrapped": preview["wrapped"],
            },
        )

        captured_labels: list[str] = []
        global_pos = preview["global_pos"]
        for owner, victim in self._capturable_tokens(player, global_pos):
            victim.send_to_base()
            player.captures_made += 1
            captured_labels.append(f"{owner.name}'s {victim.label}")
            self._emit(
                "TOKEN_CAPTURED",
                player_index,
                {
                    "mover": token.label,
                    "victim_player": owner.index,
                    "victim_token": victim.label,
                },
            )

        if preview["blockade_formed"] and global_pos is not None:
            self._emit(
                "BLOCKADE_FORMED",
                player_index,
                {"tile": global_pos, "token": token.label},
            )

        reached_home = bool(preview["reached_home"])
        if reached_home:
            self.consecutive_sixes = 0
        player_finished = player.all_finished(self.board.home_finish)
        if player_finished and player_index not in self.finish_order:
            self.finish_order.append(player_index)
            self._emit("PLAYER_FINISHED", player_index, {"place": len(self.finish_order)})

        required_finishers = self.config["player_count"] - 1 if self.config["podium_mode"] else 1
        won = player_finished and len(self.finish_order) >= required_finishers
        bonus_turn = False
        if won:
            self.status = "WON"
            self.winner_index = self.finish_order[0]
            self.last_event = f"{self.players[self.winner_index].name} wins!"
            self._emit("GAME_WON", self.winner_index, {"finish_order": list(self.finish_order)})
        elif player_finished:
            self.last_event = f"{player.name} finished; advancing to the remaining players."
            self.advance_turn()
        else:
            bonus_turn = bool(
                roll == 6
                or (captured_labels and self.config["bonus_on_capture"])
                or (reached_home and self.config["bonus_on_home"])
            )
            if bonus_turn:
                self.last_event = f"Bonus roll for {player.name}."
                self._emit("BONUS_TURN", player_index, {"roll": roll})
            else:
                self.consecutive_sixes = 0
                self.advance_turn()

        return {
            "old_steps": old_steps,
            "new_steps": new_steps,
            "captured": captured_labels,
            "reached_home": reached_home,
            "wrapped": bool(preview["wrapped"]),
            "player_finished": player_finished,
            "won": won,
            "bonus_turn": bonus_turn,
            "blockade_formed": bool(preview["blockade_formed"]),
        }

    def record_bot_decision(self, token_idx: int, roll: int, reason: str) -> None:
        """Record a deterministic bot choice in the shared event stream."""
        player = self.current_player()
        self._emit(
            "BOT_DECISION",
            player.index,
            {"token": player.tokens[token_idx].label, "token_idx": token_idx, "roll": roll, "reason": reason},
        )

    def advance_turn(self) -> None:
        """Advance to the next unfinished player and enforce the turn cap."""
        if self.status != "PLAYING":
            return
        self.consecutive_sixes = 0
        for offset in range(1, len(self.players) + 1):
            candidate = (self.current_player_index + offset) % len(self.players)
            if not self.players[candidate].all_finished(self.board.home_finish):
                self.current_player_index = candidate
                break
        self.turn_count += 1
        self._emit("TURN_ADVANCED", self.current_player_index)
        if self.turn_count >= self.max_turns:
            self.status = "DRAW"
            self.draw_reason = "Maximum turn limit reached"
            self.last_event = self.draw_reason
            self._emit("GAME_DRAW", None, {"reason": self.draw_reason})

    def declare_mutual_draw(self) -> None:
        """End the match by mutual agreement."""
        self.status = "DRAW"
        self.draw_reason = "Mutual agreement"
        self.last_event = self.draw_reason
        self._emit("GAME_DRAW", None, {"reason": self.draw_reason})

    def quit(self) -> None:
        """End the match with a clean quit status."""
        self.status = "QUIT"
        self.last_event = "Game quit."
        self._emit("GAME_QUIT", None)

    def export_canonical_state(self) -> dict[str, Any]:
        """Return a JSON-serializable snapshot for exact parity checks."""
        return {
            "config": copy.deepcopy(self.config),
            "max_turns": self.max_turns,
            "turn_count": self.turn_count,
            "current_player": self.current_player_index,
            "consecutive_sixes": self.consecutive_sixes,
            "status": self.status,
            "winner_index": self.winner_index,
            "draw_reason": self.draw_reason,
            "finish_order": list(self.finish_order),
            "last_event": self.last_event,
            "events": [clone_event(event) for event in self.events],
            "players": [
                {
                    "index": player.index,
                    "name": player.name,
                    "kind": player.kind,
                    "color": player.color,
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
