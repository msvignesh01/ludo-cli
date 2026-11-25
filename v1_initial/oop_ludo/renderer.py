"""Object-oriented terminal renderer for canonical Ludo snapshots."""

from __future__ import annotations

from typing import Any

from ..shared.view import render_board, render_moves, terminal_settings


class CLIRenderer:
    """Render OOP game snapshots through the shared presentation contract."""

    def __init__(self, use_color: bool = True, use_unicode: bool | None = None) -> None:
        """Configure platform-safe ANSI and Unicode output."""
        self.use_color, detected_unicode = terminal_settings(use_color)
        self.use_unicode = detected_unicode if use_unicode is None else use_unicode

    def render(self, snapshot: dict[str, Any]) -> str:
        """Render one complete canonical board snapshot."""
        return render_board(snapshot, self.use_color, self.use_unicode)

    def render_moves(self, previews: list[dict[str, Any]]) -> str:
        """Render the legal move choices for the active player."""
        return render_moves(previews, self.use_color, self.use_unicode)
