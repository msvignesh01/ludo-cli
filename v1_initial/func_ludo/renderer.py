"""Zero-class functional terminal rendering for Ludo state."""

from __future__ import annotations

from typing import Any

from ..shared.view import render_board, render_moves, terminal_settings


def create_renderer_settings(use_color: bool, use_unicode: bool | None = None) -> tuple[bool, bool]:
    """Return platform-safe color and Unicode settings."""
    color, detected_unicode = terminal_settings(use_color)
    return color, detected_unicode if use_unicode is None else use_unicode


__all__ = ["create_renderer_settings", "render_board", "render_moves"]
