"""Gameplay and object-oriented call-trace commentary rendering."""

from __future__ import annotations

from typing import Any


class Commentary:
    """Render shared events as audience-friendly or paradigm-specific lines."""

    def __init__(self, player_names: list[str]) -> None:
        """Store display names without owning match state."""
        self.player_names = list(player_names)

    def _name(self, player_index: int | None) -> str:
        """Return a safe player label for an event."""
        if player_index is None or not 0 <= player_index < len(self.player_names):
            return "Game"
        return self.player_names[player_index]

    def gameplay(self, event: dict[str, Any]) -> str:
        """Render one event for a general audience."""
        kind = event["type"]
        player = self._name(event["player"])
        data = event["data"]
        if kind == "GAME_STARTED":
            return "Match started."
        if kind == "DICE_ROLLED":
            return f"{player} rolls {data.get('roll')}."
        if kind == "NO_VALID_MOVES":
            return f"{player} has no legal move and skips."
        if kind == "TRIPLE_SIX_FORFEIT":
            return f"{player} forfeits the third consecutive six."
        if kind == "BOT_DECISION":
            return f"{player} bot chooses {data.get('token')}: {data.get('reason')}."
        if kind == "TOKEN_MOVED":
            return (
                f"{player} moves {data.get('token')} "
                f"from steps {data.get('old_steps')} to {data.get('new_steps')}."
            )
        if kind == "TOKEN_CAPTURED":
            victim = self._name(data.get("victim_player"))
            return f"{player} captures {victim}'s {data.get('victim_token')}."
        if kind == "BLOCKADE_FORMED":
            return f"{player} forms a blockade on T{int(data.get('tile', 0)):02d}."
        if kind == "PLAYER_FINISHED":
            return f"{player} finishes in place {data.get('place')}."
        if kind == "BONUS_TURN":
            return f"{player} earns another roll."
        if kind == "TURN_ADVANCED":
            return f"Next turn: {player}."
        if kind == "GAME_WON":
            return f"{player} wins!"
        if kind == "GAME_DRAW":
            return f"Draw: {data.get('reason')}."
        if kind == "GAME_QUIT":
            return "Game quit."
        return f"{kind}."

    def code(self, event: dict[str, Any]) -> str:
        """Render one event as an object-oriented execution trace."""
        kind = event["type"]
        data = event["data"]
        if kind == "GAME_STARTED":
            return "OOP: LudoGame.__init__()"
        if kind == "DICE_ROLLED":
            return f"OOP: LudoGame.roll_die() -> process_roll(roll={data.get('roll')})"
        if kind == "NO_VALID_MOVES":
            return "OOP: LudoGame.process_roll() -> advance_turn()"
        if kind == "TRIPLE_SIX_FORFEIT":
            return "OOP: LudoGame.process_roll() -> advance_turn()"
        if kind == "BOT_DECISION":
            return "OOP: BotPolicy.choose_move()"
        if kind == "TOKEN_MOVED":
            return f"OOP: LudoGame.apply_move(token_idx={data.get('token_idx')}, roll={data.get('roll')})"
        if kind == "TOKEN_CAPTURED":
            return "OOP: Token.send_to_base()"
        if kind == "BLOCKADE_FORMED":
            return 'OOP: LudoGame._emit("BLOCKADE_FORMED")'
        if kind == "PLAYER_FINISHED":
            return "OOP: Player.all_finished()"
        if kind == "BONUS_TURN":
            return "OOP: LudoGame.apply_move() -> bonus_turn"
        if kind == "TURN_ADVANCED":
            return "OOP: LudoGame.advance_turn()"
        if kind == "GAME_WON":
            return "OOP: LudoGame.apply_move() -> status = WON"
        if kind == "GAME_DRAW":
            return "OOP: LudoGame.declare_mutual_draw() or advance_turn()"
        if kind == "GAME_QUIT":
            return "OOP: LudoGame.quit()"
        return f"OOP: {kind}"
