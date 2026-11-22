# OOP Architecture Specification (`ludo_oop.py`)

This document defines the exact Object-Oriented structure for `v1_initial/ludo_oop.py` and `v2_final/ludo_oop.py`.

---

## 1. Design Philosophy
- **Encapsulation:** Each domain entity owns its own data and the methods that mutate or query that data.
- **Separation of Concerns:** Game rules (`Token`, `Player`, `Board`, `LudoGame`) are cleanly decoupled from terminal formatting (`CLIRenderer`) so the engine can be unit-tested and parity-fuzzed headlessly at high speed.

---

## 2. Class Hierarchy & Contracts

### Class 1: `Token`
Represents a single movable piece belonging to one player.
- **Attributes:**
  - `token_idx: int` (0-based index, e.g., `0`, `1`)
  - `label: str` (e.g., `"R1"`, `"G2"`)
  - `steps: int` (default `-1`; `-1` = Base, `0..track_len-2` = Outer Track, `track_len-1..home_finish-1` = Home Stretch, `home_finish` = Home)
- **Methods:**
  - `is_in_base() -> bool`
  - `is_finished(home_finish: int) -> bool`
  - `is_in_home_stretch(track_len: int, home_finish: int) -> bool`
  - `can_move(roll: int, home_finish: int) -> bool`
  - `target_steps(roll: int) -> int` (returns `0` if in base and `roll == 6`, else `self.steps + roll`)
  - `move_to(new_steps: int) -> None`
  - `send_to_base() -> None` (`self.steps = -1`)

### Class 2: `Player`
Represents a participant and their collection of `Token` objects.
- **Attributes:**
  - `index: int` (`0..3`)
  - `name: str`
  - `color_name: str` (`"RED"`, `"GREEN"`, `"YELLOW"`, `"BLUE"`)
  - `color_code: str` (ANSI foreground escape code)
  - `prefix: str` (`"R"`, `"G"`, `"Y"`, `"B"`)
  - `start_index: int` (global outer track tile index where `steps == 0` lands)
  - `tokens: list[Token]`
  - `captures_made: int` (stats counter, default `0`)
- **Methods:**
  - `all_finished(home_finish: int) -> bool`
  - `finished_count(home_finish: int) -> int`
  - `get_valid_token_indices(roll: int, home_finish: int) -> list[int]`

### Class 3: `Board`
Encapsulates mode preset geometry, coordinate translation, and safe-zone lookup.
- **Class Constants:** `PRESETS: dict` containing `"quick"` and `"classic"` preset definitions.
- **Attributes:**
  - `mode: str` (`"quick"` or `"classic"`)
  - `track_len: int`
  - `home_len: int`
  - `tokens_per_player: int`
  - `outer_last_step: int` (`track_len - 2`)
  - `home_finish: int` (`track_len - 1 + home_len`)
  - `safe_tiles: frozenset[int]`
  - `default_max_turns: int`
- **Methods:**
  - `get_start_indices(num_players: int) -> list[int]` (2P diagonal vs 3P/4P clockwise)
  - `get_global_pos(start_index: int, steps: int) -> int | None`
  - `is_safe_tile(global_pos: int | None) -> bool`
  - `format_position(start_index: int, steps: int) -> str` (`"BASE"`, `"T00"`..`"T51"`, `"H1"`..`"H5"`, `"HOME"`)

### Class 4: `CLIRenderer`
Handles all ANSI coloring, Windows VT100 activation, ASCII/Unicode safety, board rendering, move option previews, and final scoreboard formatting.
- **Attributes:**
  - `use_color: bool`
  - `use_unicode: bool` (auto-detected from `sys.stdout.encoding`)
- **Methods:**
  - `colorize(text: str, ansi_code: str) -> str`
  - `render_board(game: LudoGame) -> str` (returns formatted string; printed by CLI runner — returning a string makes output cleanly testable!)
  - `format_move_options(game: LudoGame, player: Player, valid_indices: list[int], roll: int) -> str`
  - `render_game_over(game: LudoGame) -> str`

### Class 5: `LudoGame`
Orchestrates the match lifecycle, RNG, turn transitions, capture execution, draw/win state, and canonical state export.
- **Attributes:**
  - `board: Board`
  - `players: list[Player]`
  - `max_turns: int`
  - `rng: random.Random`
  - `current_player_index: int` (default `0`)
  - `turn_count: int` (default `0`)
  - `consecutive_sixes: int` (default `0`)
  - `status: str` (`"PLAYING"`, `"WON"`, `"DRAW"`, `"QUIT"`)
  - `winner_index: int | None`
  - `draw_reason: str | None`
  - `last_event: str`
- **Core Headless Engine Methods (Used by CLI & Automated Tests):**
  - `current_player() -> Player`
  - `roll_die() -> int` (`self.rng.randint(1, 6)`)
  - `process_roll(roll: int) -> dict` (handles triple-6 check, valid moves, auto-skip; returns `{"event": ..., "valid_moves": [...]}`)
  - `preview_move(player_idx: int, token_idx: int, roll: int) -> dict` (computes destination label, whether it lands on safe tile, captures list, or reaches home — without mutating state)
  - `apply_move(token_idx: int, roll: int) -> dict` (mutates state, resolves captures, checks win, decides bonus turn vs `advance_turn()`)
  - `advance_turn() -> None` (resets streak, cycles player, increments `turn_count`, enforces `max_turns` draw)
  - `declare_mutual_draw() -> None`
  - `export_canonical_state() -> dict` (**CRITICAL FOR PARITY TESTING — see schema below**)
- **Interactive Entry Point:**
  - `run_cli(renderer: CLIRenderer) -> None`

---

## 3. Canonical State Export Schema (MUST Match `ludo_func.py` Byte-for-Byte)

Both `LudoGame.export_canonical_state()` and `ludo_func.export_canonical_state(state)` MUST return a plain Python `dict` with these exact keys and primitive types:

```python
{
    "mode": "quick",                  # "quick" | "classic"
    "track_len": 28,                  # int
    "home_len": 4,                    # int
    "home_finish": 31,                # int
    "max_turns": 100,                 # int
    "turn_count": 0,                  # int
    "current_player": 0,              # int
    "consecutive_sixes": 0,           # int
    "status": "PLAYING",              # "PLAYING" | "WON" | "DRAW" | "QUIT"
    "winner_index": None,             # int | None
    "draw_reason": None,              # str | None
    "players": [
        {
            "index": 0,
            "name": "Alice",
            "color": "RED",
            "start_index": 0,
            "captures_made": 0,
            "tokens": [
                {"label": "R1", "steps": -1},
                {"label": "R2", "steps": -1},
            ],
        },
        # ... remaining players
    ],
}
```
