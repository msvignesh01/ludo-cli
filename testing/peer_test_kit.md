# Peer Testing Kit — Multiplayer Ludo CLI (v1)

Thank you for testing our CIA1 Ludo assignment! Please test **BOTH** versions:
- **Version A (Class-Based / OOP):** `python v1_initial/ludo_oop.py`
- **Version B (Function-Based / Zero-Class):** `python v1_initial/ludo_func.py`

> **Setup:** Pure Python 3.11+ Standard Library — no `pip install` needed.

---

## Structured 10-Point Test Checklist

Please run through these scenarios on **both** programs and note any discrepancy, bug, crash, or UX annoyance:

| # | Test Scenario | How to Trigger | Expected Behavior |
|---|---|---|---|
| 1 | **Quick Mode Playthrough** | Run `python ludo_oop.py --mode quick` (2 players) | 28-tile board, 2 tokens each, plays cleanly to a winner. |
| 2 | **Classic Mode Toggle** | Run `python ludo_func.py --mode classic` (4 players) | 52-tile board, 4 tokens each, 8 safe tiles (`★`) displayed cleanly. |
| 3 | **Deterministic Parity Check** | Run both with `--mode quick --seed 42` and pick the same moves | Identical dice rolls, board states, captures, and winner. |
| 4 | **Invalid Inputs Stress Test** | Enter letters (`abc`), symbols (`@#$`), `-5`, `99`, and blank lines at every prompt | Never crashes; displays helpful error message and re-prompts. |
| 5 | **Unlock on 6 & Auto-Skip** | Roll 1–5 while all tokens are in Base | Auto-skips turn with clear explanation; unlocks on 6 with bonus roll. |
| 6 | **Safe Tile & Capture Rules** | Land on opponent on a normal tile vs a `★` safe tile | Normal tile captures opponent to BASE (+bonus roll); `★` tile lets both coexist safely. |
| 7 | **Exact Roll to Home** | Try moving a token near `H4` when die roll overshoots `HOME` | Overshooting move is disallowed; exact roll finishes token (+bonus roll). |
| 8 | **Triple-6 Penalty** | Observe (or test with a seed) 3 consecutive 6s | 3rd roll is forfeited and turn passes cleanly. |
| 9 | **Draw Conditions (Both)** | *(a)* Run with `--max-turns 4`; *(b)* type `draw` mid-game and test both `n` and `y` | *(a)* Auto-draw at turn 4; *(b)* `n` resumes game, all `y` ends in mutual draw. |
| 10 | **Quit & Color Toggle** | Type `quit` (test `n` then `y`); also try `--no-color` | Clean exit without tracebacks; `--no-color` strips all ANSI codes cleanly. |

---

## Submitting Your Report
Please fill out `team_report_template.md` (takes ~5 minutes) with:
- Your team members' names
- Pass/Fail status for both versions
- Any bugs, edge cases, or rule discrepancies found
- At least 2 concrete suggestions for UX or gameplay improvements we can build into `v2_final`!
