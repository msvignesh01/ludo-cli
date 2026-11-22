# CLI UI & ANSI Rendering Specification

This document ensures a crisp, readable, color-coded terminal experience across Windows PowerShell/CMD, Windows Terminal, VS Code integrated terminal, macOS, and Linux.

---

## 1. ANSI Color Palette & Terminal Compatibility

| Role | ANSI Escape Code | Usage |
|---|---|---|
| Reset | `\033[0m` | Close every styled segment |
| Bold | `\033[1m` | Headers, player turn banner, winner banner |
| Dim | `\033[2m` | Empty track slots, divider borders |
| Cyan | `\033[96m` | Mode title, turn counter, safe star `★` |
| Red Player | `\033[91m` | `RED` tag, `R1..Rn` tokens |
| Green Player | `\033[92m` | `GREEN` tag, `G1..Gn` tokens |
| Yellow Player | `\033[93m` | `YELLOW` tag, `Y1..Yn` tokens |
| Blue Player | `\033[94m` | `BLUE` tag, `B1..Bn` tokens |
| Magenta | `\033[95m` | Capture / Bonus Roll highlight tags |

### Windows & Encoding Safety
1. When `use_color` is `True` and `os.name == "nt"`, run `os.system("")` once at startup to enable Windows VT100 ANSI escape processing.
2. When `--no-color` is passed, `colorize()` MUST return raw text untouched—zero `\033[` sequences anywhere in stdout.
3. Detect Unicode safety via `(sys.stdout.encoding or "").lower().startswith("utf")`:
   - If UTF-8: safe tile marker is `★` (or `*` fallback if non-UTF8).
   - Never crash with `UnicodeEncodeError` on Windows `cp1252` terminals! Prefer safe icons (`*` or `★` with fallback, `[6]` die badge instead of emoji dice that can fail on legacy CMD).

---

## 2. Board Layout Specification (Both Modes)

### Outer Track Quadrant Grid
- **Quick Mode (28 tiles):** 4 rows of 7 tiles (`Q1: 00–06`, `Q2: 07–13`, `Q3: 14–20`, `Q4: 21–27`).
- **Classic Mode (52 tiles):** 4 quadrants of 13 tiles; to fit cleanly inside standard 80–100 column terminals without wrapping awkwardly, render each quadrant in **2 clean sub-rows** (7 tiles + 6 tiles) or a compact tile format `[★00:R1]` (max width <= 95 chars).
- **Stacked Tokens Display:** If 1 token is on a tile, show `[★00:R1 ]`. If 2+ tokens share a tile, show comma-joined labels (e.g., `[★00:R1,G1]`) or compact stack badge so NO token is ever visually hidden!

### Player Status & Private Home Stretch Panel
Display one clean aligned row per player:
- Active player marked with `>` (highlighted bold).
- Player color tag + name.
- Every token's exact position (`BASE`, `T04`, `H2`, `HOME`).
- Visual Private Home Stretch bar: `[ . R . . ]` showing which home slots (`H1..H4` or `H1..H5`) contain tokens + `(finished/total)`.

### Move Selection Menu with Live Previews
Before asking the player to pick a move, display numbered choices `1..K` with smart annotations computed by `preview_move`:
- `[1] Move R1: BASE -> T00 [UNLOCKS onto Safe *]`
- `[2] Move R2: T04 -> T08 [CAPTURES Bob's G1! +Bonus Roll]`
- `[3] Move R1: H3 -> HOME [REACHES HOME! +Bonus Roll]`
- `[4] Move R2: T12 -> T16`

---

## 3. Bulletproof Input Validation Contract

Every `input()` prompt MUST run inside a retry loop that:
1. Strips leading/trailing whitespace (`raw.strip()`).
2. Handles `KeyboardInterrupt` and `EOFError` cleanly (graceful exit without stack trace).
3. Rejects invalid inputs with a **specific, helpful error message** and re-prompts without losing game state:
   - Mode selection: accepts `1`, `2`, `quick`, `classic` (case-insensitive).
   - Player count: accepts integers `2`, `3`, `4` only.
   - Roll prompt: accepts empty Enter (roll), `roll`/`r`, `draw`, `quit`/`q` (case-insensitive). Anything else prints: `Invalid command. Press ENTER to roll, or type 'draw' or 'quit'.`
   - Move selection: accepts integers `1` through `len(valid_moves)` only. Rejects `0`, negative numbers, out-of-range numbers, floats, and letters cleanly.
   - Yes/No confirmations (`draw`, `quit`): accepts `y`/`yes` or `n`/`no` (case-insensitive).
