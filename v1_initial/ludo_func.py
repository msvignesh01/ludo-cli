#!/usr/bin/env python3
"""Launch the modular zero-class functional Ludo application."""

from __future__ import annotations

import sys
from pathlib import Path


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from v1_initial.func_ludo.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
