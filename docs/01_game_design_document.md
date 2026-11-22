# Game Design Document (GDD) — Multiplayer Ludo CLI

**Project:** CIA1 Python Programming Assignment (OOP vs. Function-Based Implementation)
**Game:** Ludo (Dual-Mode: Quick Mode & Classic Mode)
**Players:** 2 to 4 human players (hot-seat local multiplayer)
**Interface:** Polished ANSI-colored Command-Line Interface (Pure Python 3.11+ Standard Library)

---

## 1. Executive Summary & Design Goals

This game implements authentic multiplayer Ludo with two selectable scale presets at startup:
1. **Quick Mode (Default for Live Demos & Peer Testing):** 28-tile shared track, 4-tile private home stretch, 2 tokens per player (~5–8 minutes per match).
2. **Classic Mode (Full Traditional Scale):** 52-tile shared track, 5-tile private home stretch, 4 tokens per player (~30–45 minutes per match).

Both modes run on the **exact same parameterized engine**, proving clean software design while keeping every classic Ludo rule (unlocking on 6, safe tiles, captures, bonus rolls, triple-6 forfeit, exact home entry, forced moves, auto-skip) 100% intact.

---

## 2. Mode Presets Configuration Table

All game geometry MUST be driven exclusively by these configuration dictionaries—no hardcoded board numbers in engine logic.

| Parameter | Key Name | Quick Mode (`quick`) | Classic Mode (`classic`) |
|---|---|---|---|
| Shared Outer Track Length | `track_len` | `28` (7 tiles / quadrant) | `52` (13 tiles / quadrant) |
| Private Home Stretch Length | `home_len` | `4` (`H1`–`H4`) | `5` (`H1`–`H5`) |
| Tokens per Player | `tokens_per_player` | `2` (e.g., `R1, R2`) | `4` (e.g., `R1–R4`) |
| Outer Steps Before Home Branch | `outer_last_step` | `26` (`track_len - 2`) | `50` (`track_len - 2`) |
| Finish Step Threshold | `home_finish` | `31` (`track_len - 1 + home_len`) | `56` (`track_len - 1 + home_len`) |
| Start Positions (4P / 3P Clockwise) | `start_indices_4p` | `[0, 7, 14, 21]` | `[0, 13, 26, 39]` |
| Start Positions (2P Diagonal) | `start_indices_2p` | `[0, 14]` | `[0, 26]` |
| Safe Tile Global Indices | `safe_tiles` | `{0, 7, 14, 21}` (14.3%) | `{0, 8, 13, 21, 26, 34, 39, 47}` (15.4%) |
| Default Max-Turn Draw Limit | `default_max_turns` | `100` | `250` |

### Player Colors & Token IDs (Fixed Order)
| Seat Index | Color Name | ANSI Code | Token Prefix | 2P Seating | 3P Seating | 4P Seating |
|---|---|---|---|---|---|---|
| 0 | `RED` | Bright Red (`\033[91m`) | `R` (`R1..Rn`) | Start `start_indices_2p[0]` | `start_indices_4p[0]` | `start_indices_4p[0]` |
| 1 | `GREEN` | Bright Green (`\033[92m`) | `G` (`G1..Gn`) | Start `start_indices_2p[1]` | `start_indices_4p[1]` | `start_indices_4p[1]` |
| 2 | `YELLOW` | Bright Yellow (`\033[93m`) | `Y` (`Y1..Yn`) | — | `start_indices_4p[2]` | `start_indices_4p[2]` |
| 3 | `BLUE` | Bright Blue (`\033[94m`) | `B` (`B1..Bn`) | — | — | `start_indices_4p[3]` |

> **Why 2P Diagonal Seating Matters:** Placing 2 players at indices `0` and `14` (Quick) or `0` and `26` (Classic) guarantees symmetric distance to conflict zones rather than giving Player 2 an unfair immediate ambush behind Player 1.

---

## 3. Unified Token Coordinate System (Exact Math)

Every token's position is represented by a single canonical integer **`steps`**:

| `steps` Value | Zone | Global Outer Index | Display Format |
|---|---|---|---|
| `-1` | **Base (Yard)** | `None` | `BASE` |
| `0 <= steps <= track_len - 2` | **Shared Outer Track** | `(player.start_index + steps) % track_len` | `T00` – `T27` (or `T51`) |
| `track_len - 1 <= steps <= home_finish - 1` | **Private Home Stretch** | `None` (private lane, immune) | `H1` – `H4` (or `H5`) |
| `steps == home_finish` | **Home (Finished)** | `None` (completed) | `HOME` |

### Proof of Correctness (Zero Off-by-One Verification)
- **Quick Mode (`track_len = 28`, `home_len = 4`):**
  - `steps = 0`: lands on own `start_index` (e.g., Red at `T00`, Green at `T14`).
  - `steps = 26`: lands on `(start_index + 26) % 28` — exactly 2 tiles behind own `start_index` (or 1 tile before the home-column entry point, matching standard Ludo's 50-step outer lap where `52 - 2 = 50`).
  - `steps = 27`: enters `H1` (`home_slot = steps - (track_len - 2) = 27 - 26 = 1`).
  - `steps = 30`: occupies `H4` (`home_slot = 4`).
  - `steps = 31`: reaches `HOME` (`home_finish = 28 - 1 + 4 = 31`).
- **Classic Mode (`track_len = 52`, `home_len = 5`):**
  - `steps = 0..50`: 51 outer tiles visited (`start_index` through `(start_index + 50) % 52`).
  - `steps = 51..55`: `H1` through `H5`.
  - `steps = 56`: `HOME` (`home_finish = 52 - 1 + 5 = 56`).

---

## 4. Complete Rulebook & Edge-Case Resolution Contract

Every rule below is strictly deterministic and MUST behave identically in both OOP and Functional versions:

1. **Setup & Player Names:**
   - Prompt for game mode (`1` = Quick, `2` = Classic) unless passed via `--mode`.
   - Prompt for number of players (`2`, `3`, or `4`).
   - Prompt for player names (blank input defaults to `Player 1`, `Player 2`, etc.; strip surrounding whitespace; enforce uniqueness or append seat suffix if identical).
2. **Rolling the Die:**
   - Uses an isolated `random.Random(seed)` instance owned by the game (never the global `random` module) so multiple tests or instances never interfere with each other's RNG stream.
   - Generates a uniform integer in `{1, 2, 3, 4, 5, 6}`.
3. **Unlocking from Base:**
   - A token at `steps == -1` can move **only** on a roll of `6`.
   - Moving it sets `steps = 0` (the player's `start_index`).
   - Because every player's `start_index` is in `safe_tiles`, unlocking a token can NEVER capture an opponent sitting on that tile.
4. **Standard Movement & Exact Home Entry:**
   - A token at `steps >= 0` (and `< home_finish`) is legally movable if and only if `steps + roll <= home_finish`.
   - Overshooting (`steps + roll > home_finish`) is **illegal** and that token MUST NOT appear in the valid move list.
   - Already finished tokens (`steps == home_finish`) are never movable.
5. **Captures & Safe Zones:**
   - Captures only occur when the moving token lands on a **shared outer track tile** (`0 <= new_steps <= track_len - 2`) whose `global_pos` is **NOT** in `safe_tiles`.
   - If one or more **opponent** tokens occupy that exact `global_pos`, **ALL** opponent tokens on that tile are captured and immediately reset to `steps = -1` (Base).
   - Friendly tokens on the same tile are unaffected (coexist peacefully).
   - Landing on a `safe_tiles` index NEVER triggers a capture—multiple colors coexist safely.
6. **No Blockades (Simplified Rule):**
   - Two or more same-color tokens on the same tile do **not** block opponents from passing over them.
   - If an opponent lands on a non-safe tile containing stacked enemy tokens, all enemy tokens on that tile are captured.
7. **Bonus Turns (Non-Stacking):**
   - A player earns an **immediate extra roll** if ANY of the following occurs on their move:
     - Rolled a `6`
     - Captured at least one opponent token
     - Moved a token into `HOME` (`new_steps == home_finish`)
   - Bonus rolls **do not stack**: rolling a `6` AND capturing on the same move awards **1** extra roll, not 2.
   - A bonus turn does **NOT** increment `turn_count` (a player's entire streak of rolls counts as 1 turn toward `max_turns`; `turn_count` increments whenever control advances to the next player).
8. **Three Consecutive Sixes Penalty:**
   - Maintain `consecutive_sixes` for the active turn.
   - Rolling a `6` increments `consecutive_sixes` by `1`.
   - Rolling `1–5` resets `consecutive_sixes` to `0` (even if the player gets a capture/home bonus roll afterward, their 6-streak is reset to 0).
   - If `consecutive_sixes == 3`: the third roll is **immediately voided before any move**, `consecutive_sixes` resets to `0`, an explanatory message is logged, and control passes to the next player (incrementing `turn_count`).
   - Note: Previous moves from the 1st and 2nd sixes remain intact (standard digital Ludo rule).
9. **Forced Moves & Auto-Skip:**
   - If 1 or more valid moves exist, the player **must** select one (voluntary pass is disallowed).
   - If 0 valid moves exist for the roll, display the reason clearly, reset `consecutive_sixes = 0`, advance to the next player, and increment `turn_count` (even if the player rolled a `6`, e.g., when their only remaining token needs a `2` to reach Home).
10. **Win Condition:**
    - Immediately after `apply_move`, if ALL of the current player's tokens satisfy `steps == home_finish`, the game ends immediately and declares that player the winner.
11. **Draw Conditions (Explicit Rubric Requirement):**
    - **Automatic Turn-Cap Draw:** When `turn_count >= max_turns`, the match ends immediately in a Draw (`draw_reason = "Maximum turn limit reached"`), showing final token rankings.
    - **Mutual Agreement Draw:** Before rolling, a player may type `draw`. Every other player is prompted `[y/n]` in order. If ALL other players enter `y`, the match ends immediately in a Draw (`draw_reason = "Mutual agreement"`). If ANY player declines (`n`), play resumes immediately with the current player's roll prompt (no turn lost).
12. **Graceful Quit & Signal Handling:**
    - Before rolling, a player may type `quit` (or `q`) -> confirmation `[y/n]` -> exits cleanly with exit code `0`.
    - Pressing `Ctrl+C` (`KeyboardInterrupt`) or hitting `EOF` exits cleanly with a polite message and exit code `0` (no raw Python traceback).

---

## 5. CLI Flags Contract

Both `ludo_oop.py` and `ludo_func.py` MUST expose this exact `argparse` CLI interface:

```text
usage: ludo_oop.py [-h] [--mode {quick,classic}] [--seed SEED]
                   [--max-turns MAX_TURNS] [--no-color]

options:
  -h, --help              Show help message and exit
  --mode {quick,classic}  Game preset mode (prompts interactively if omitted)
  --seed SEED             Integer RNG seed for deterministic play and parity testing
  --max-turns MAX_TURNS   Positive integer turn cap before draw (overrides preset default)
  --no-color              Disable ANSI color codes (plain text output)
```

Validation: If `--max-turns <= 0`, print a clear error via `parser.error("--max-turns must be a positive integer.")` and exit non-zero.
