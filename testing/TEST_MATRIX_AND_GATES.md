# Exhaustive Test Matrix & Perfection Gates

Every test listed below MUST be implemented in `testing/test_suite.py` and `testing/parity_test.py` and executed against **BOTH** `ludo_oop.py` and `ludo_func.py`.

---

## 1. Unit & Rule Edge-Case Matrix (`testing/test_suite.py`)

| ID | Category | Scenario | Exact Assertion |
|---|---|---|---|
| T01 | Presets | Quick Mode config | `track_len=28, home_len=4, tokens=2, home_finish=31, safe_tiles={0,7,14,21}` |
| T02 | Presets | Classic Mode config | `track_len=52, home_len=5, tokens=4, home_finish=56, safe_tiles={0,8,13,21,26,34,39,47}` |
| T03 | Seating | 2P Diagonal Seating | Quick starts `[0, 14]`; Classic starts `[0, 26]` |
| T04 | Seating | 3P & 4P Clockwise Seating | Quick 3P `[0, 7, 14]`, 4P `[0, 7, 14, 21]`; Classic 4P `[0, 13, 26, 39]` |
| T05 | Unlock | Base Exit Blocked on 1–5 | Token at `steps=-1` has `valid_moves == []` for rolls `1,2,3,4,5` |
| T06 | Unlock | Base Exit Allowed on 6 | Token at `steps=-1` unlocks to `steps=0` on roll `6`, awards bonus turn |
| T07 | Wrap | Circular Outer Track Modulo | Player at `start_index=14` (Quick) with `steps=13` -> `T27`; `steps=14` -> `T00` |
| T08 | Home | Private Home Entry | Quick: `steps=26 + roll=1 -> steps=27 (H1)`, `global_pos is None` |
| T09 | Home | Exact Finish & Overshoot | Quick: `steps=29` allows roll `1` (`H4`) and `2` (`HOME`), rejects rolls `3,4,5,6` |
| T10 | Capture | Non-Safe Single Capture | Opponent at same non-safe `global_pos` resets to `-1`, mover gets `bonus_turn=True`, `captures_made += 1` |
| T11 | Capture | Non-Safe Multi-Token Stack Capture | 2 stacked opponent tokens on non-safe tile BOTH reset to `-1`, `captures_made += 2` |
| T12 | Safe | Safe Tile Immunity | Landing on opponent sitting on `★` tile (`0, 7, 14, 21` in Quick; `8, 21, 34, 47` in Classic) triggers NO capture and NO bonus roll (unless rolled 6) |
| T13 | Stacking | Same-Color Friendly Stack | Moving friendly token onto own token does NOT capture own token; opponent can pass over it |
| T14 | Bonus | Home-Finish Bonus Roll | Moving token into `HOME` on roll `2` grants `bonus_turn=True` and resets `consecutive_sixes=0` |
| T15 | Bonus | Non-Stacking Bonus Rule | Rolling `6` AND capturing grants 1 bonus roll; next non-6 non-capture move passes turn immediately |
| T16 | Penalty | Triple Consecutive Sixes | 1st six -> plays; 2nd six -> plays; 3rd six -> `TRIPLE_SIX_FORFEIT`, move skipped, `consecutive_sixes=0`, turn advances |
| T17 | Penalty | Six-Streak Reset on Non-6 Capture | Roll `6` -> Roll `4` (captures -> bonus roll) -> Roll `6` -> Roll `6` -> NOT a triple-6 forfeit because roll `4` reset streak! |
| T18 | Auto-Skip | Roll 6 with No Legal Move | Only remaining token at `steps=30` (needs `1`), rolls `6` -> auto-skips, `consecutive_sixes=0`, turn advances |
| T19 | Win | Immediate Victory | Moving last token to `home_finish` sets `status="WON"`, `winner_index=player_idx`, `bonus_turn=False` |
| T20 | Draw | Max-Turn Cap Trigger | Reaching `turn_count == max_turns` sets `status="DRAW"`, `draw_reason="Maximum turn limit reached"` |
| T21 | Draw | Mutual Draw Accepted & Declined | All `y` -> `status="DRAW"`, `draw_reason="Mutual agreement"`; any `n` -> resumes active player without advancing turn |
| T22 | CLI | Invalid Inputs Resilience | Non-ints, empty strings, out-of-range choices, negative numbers never crash CLI |
| T23 | CLI | `--no-color` Purity | Output contains zero `\033[` escape sequences |
| T24 | CLI | Invalid `--max-turns 0` | Exits non-zero cleanly via argparse error |

---

## 2. Automated Parity Fuzz Suite (`testing/parity_test.py`)

### A. 1,000-Game Headless Engine Parity Fuzzing
Run across all 6 configurations:
- `quick` x 2P (200 games)
- `quick` x 3P (200 games)
- `quick` x 4P (200 games)
- `classic` x 2P (150 games)
- `classic` x 3P (150 games)
- `classic` x 4P (100 games)

For every game `seed`:
1. Initialize both `LudoGame` (OOP) and `create_game_state` (Functional) with the exact same `mode`, `player_names`, `max_turns`, and `seed`.
2. On every roll:
   - Assert `oop_roll == func_roll`.
   - Assert `oop_roll_res == func_roll_res`.
   - If moves are available, pick a deterministic move index using a shared test RNG (`choice_idx`), assert `oop.preview_move(...) == func.preview_move(...)`, then call `apply_move(...)` on both.
   - Assert `oop.export_canonical_state() == func.export_canonical_state(state)` **after every single action**.
3. Assert both games terminate in the exact same status (`WON` or `DRAW`), same `winner_index`, same `draw_reason`, and same `turn_count`.

### B. End-to-End Subprocess CLI Transcript Parity
Run both `ludo_oop.py` and `ludo_func.py` via `subprocess.run([sys.executable, script, "--mode", ..., "--seed", ..., "--no-color"], input=scripted_stdin, text=True, capture_output=True)`:
- **Transcript 1:** Quick 2P full game to win, injecting invalid menu inputs (`abc`, `99`, `-1`, empty space) mid-game.
- **Transcript 2:** Quick 3P max-turn draw (`--max-turns 4`).
- **Transcript 3:** Quick 2P mutual `draw` declined once (`n`), then accepted (`y`).
- **Transcript 4:** Classic 4P multi-turn playthrough + graceful `quit` confirmed (`y`).
- **Assertion:** `oop_proc.returncode == func_proc.returncode == 0` AND `oop_proc.stdout == func_proc.stdout` (100% identical CLI output!).

---

## 3. Static & Structural Gates (`scripts/verify_gates.py`)
1. **Zero-Class AST Gate (`ludo_func.py`):** Count of `ast.ClassDef` nodes MUST equal `0`.
2. **OOP Class Gate (`ludo_oop.py`):** Must define at least `Token`, `Player`, `Board`, `CLIRenderer`, `LudoGame`.
3. **Stdlib-Only Import Gate:** Every imported module across `ludo_oop.py` and `ludo_func.py` MUST be in `sys.stdlib_module_names`.
4. **Submission Completeness Gate (`--stage final`):** Verifies all 8 submission deliverables exist and contain zero `TODO` or `TBD` placeholders.
