# Function-Based Architecture Specification (`ludo_func.py`)

This document defines the exact Function-Based structure for `v1_initial/ludo_func.py` and `v2_final/ludo_func.py`.

---

## 1. Non-Negotiable Constraint: ZERO Classes
- **Zero `class` keywords anywhere in `ludo_func.py`.**
- Verified automatically by `scripts/verify_gates.py` using Python's `ast.walk()` checking `isinstance(node, ast.ClassDef)`.
- Do NOT define dataclasses, Enums, NamedTuple classes, or custom Exception classes.
- Use **only** module-level constants, functions, and built-in data structures (`dict`, `list`, `tuple`, `set`, `frozenset`, `int`, `str`, `bool`, `None`, plus `random.Random` instance stored inside the `state` dictionary).

---

## 2. Centralized `game_state` Dictionary Schema

All mutable and configuration state lives in a single dictionary created by `create_game_state(...)` and passed explicitly as the first argument to game operations (no hidden global mutable variables):

```python
state = {
    "config": {
        "mode": "quick",                        # "quick" | "classic"
        "track_len": 28,
        "home_len": 4,
        "tokens_per_player": 2,
        "outer_last_step": 26,
        "home_finish": 31,
        "safe_tiles": frozenset({0, 7, 14, 21}),
        "default_max_turns": 100,
    },
    "max_turns": 100,
    "rng": random.Random(seed),                 # isolated RNG instance
    "current_player": 0,
    "turn_count": 0,
    "consecutive_sixes": 0,
    "status": "PLAYING",                        # "PLAYING" | "WON" | "DRAW" | "QUIT"
    "winner_index": None,
    "draw_reason": None,
    "last_event": "Game started! Roll the die to begin.",
    "players": [
        {
            "index": 0,
            "name": "Alice",
            "color_name": "RED",
            "color_code": "\033[91m",
            "prefix": "R",
            "start_index": 0,
            "captures_made": 0,
            "tokens": [
                {"token_idx": 0, "label": "R1", "steps": -1},
                {"token_idx": 1, "label": "R2", "steps": -1},
            ],
        },
        # ...
    ],
}
```

---

## 3. Modular Function Catalog

Organize `ludo_func.py` into four clearly commented sections so readers and viva evaluators can trace every layer effortlessly:

### Section A: Constants & Initialization
- `PRESETS: dict` (module-level constant identical to `Board.PRESETS`)
- `PLAYER_SPECS: tuple` (Red, Green, Yellow, Blue metadata)
- `get_start_indices(mode: str, num_players: int) -> list[int]`
- `create_game_state(mode: str, player_names: list[str], max_turns: int | None = None, seed: int | None = None) -> dict`

### Section B: Pure Coordinate & Query Helpers (Zero Side Effects)
- `get_global_pos(start_index: int, steps: int, track_len: int) -> int | None`
- `is_safe_tile(global_pos: int | None, safe_tiles: frozenset[int]) -> bool`
- `format_position(start_index: int, steps: int, track_len: int, home_finish: int) -> str`
- `can_token_move(steps: int, roll: int, home_finish: int) -> bool`
- `compute_target_steps(steps: int, roll: int) -> int`
- `get_valid_moves(state: dict, player_idx: int, roll: int) -> list[int]`
- `preview_move(state: dict, player_idx: int, token_idx: int, roll: int) -> dict`
- `all_tokens_finished(player: dict, home_finish: int) -> bool`
- `export_canonical_state(state: dict) -> dict` (MUST match `LudoGame.export_canonical_state()` schema identically)

### Section C: State Transition Functions
- `roll_die(state: dict) -> int`
- `advance_turn(state: dict) -> None`
- `process_roll(state: dict, roll: int) -> dict`
- `apply_move(state: dict, token_idx: int, roll: int) -> dict`
- `declare_mutual_draw(state: dict) -> None`

### Section D: ANSI CLI Rendering & Input Loop
- `init_terminal_colors(use_color: bool) -> tuple[bool, bool]` (returns `(color_enabled, unicode_enabled)`)
- `colorize(text: str, ansi_code: str, use_color: bool) -> str`
- `render_board(state: dict, use_color: bool, use_unicode: bool) -> str`
- `format_move_options(state: dict, valid_indices: list[int], roll: int, use_color: bool, use_unicode: bool) -> str`
- `render_game_over(state: dict, use_color: bool) -> str`
- `prompt_setup(cli_mode: str | None) -> tuple[str, list[str]]`
- `prompt_mutual_draw(state: dict, proposer_idx: int) -> bool`
- `prompt_move_choice(valid_indices: list[int]) -> int`
- `run_cli(state: dict, use_color: bool, use_unicode: bool) -> None`
- `parse_args(argv: list[str] | None = None) -> argparse.Namespace`
- `main(argv: list[str] | None = None) -> int`

---

## 4. Parity Alignment Checkpoints
- Both `ludo_oop.py` and `ludo_func.py` must emit the **exact same text prompts, event logs, board layout, and winner/draw banners** so subprocess CLI comparison produces a 0-line diff under `--no-color --seed <N>`.
