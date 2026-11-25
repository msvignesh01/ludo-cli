# Peer Testing Kit — Multiplayer Ludo Showcase v1

Thank you for independently testing the CIA1 Ludo assignment. Test **both**
implementations:

- OOP: `python v1_initial/ludo_oop.py`
- Functional: `python v1_initial/ludo_func.py`

Requirements: Python 3.11+, standard library only, no `pip install`. Tkinter is
needed only for GUI cases. If Tkinter is unavailable, record that limitation and
complete every CLI case.

Read `docs/USER_MANUAL.md` before testing. Do not edit `v1_initial/`; report
findings so fixes can be made later in `v2_final/`.

## Suggested Team Split

**Team 1 — Rules and CLI**

Focus on core movement, captures, blockades, Kill-to-Enter, Podium Mode, turn
rewards, input handling, draw, quit, and seeded parity.

**Team 2 — Configuration and GUI**

Focus on wizard, JSON, precedence, mixed human/bot seats, four-bot autoplay,
commentary, speed, GUI controls, visual clarity, and cross-platform behavior.

Both teams should run at least one seeded parity comparison and one invalid
input stress test.

## Starting Commands

Run from the repository root.

```text
python v1_initial/ludo_oop.py --mode quick --seed 42 --no-color
python v1_initial/ludo_func.py --mode classic --seed 42 --no-color
python v1_initial/ludo_oop.py --wizard
python v1_initial/ludo_func.py --config configs/showcase.json
python v1_initial/ludo_oop.py --mode quick --players 2 --seat human --seat bot --seed 7 --no-color
python v1_initial/ludo_func.py --mode quick --seed 42 --ui gui
```

For a repeatable automated match:

```text
python v1_initial/ludo_oop.py --mode quick --players 4 --tokens 2 --seat bot --seat bot --seat bot --seat bot --autoplay --speed fast --max-turns 30 --commentary gameplay --no-color
```

Use `--commentary both` to inspect paradigm-specific code traces. Those
`OOP:`/`Functional:` lines are intentionally different; gameplay and canonical
state must still agree.

## Test Checklist

Record Pass/Fail/Blocked separately for both implementations. “Blocked” means
the environment or time limit prevented observation, not that the rule passed.

| # | Scenario | Procedure | Expected behavior |
|---|---|---|---|
| 1 | Quick and Classic geometry | Start each mode; inspect board and help | Quick is 28-tile/9×9 with 2 default tokens; Classic is 52-tile/15×15 with 4 |
| 2 | Base entry and auto-skip | Roll while tokens are in base without a 6 | Turn skips cleanly; a 6 permits entry and earns a bonus after a legal move |
| 3 | Multiple legal choices | Enter a roll with more than one legal token | Choices show destination/consequences; valid selection moves exactly once |
| 4 | Capture | Land on an opponent on a non-safe outer tile | Opponent token returns to base; capture count increases; capture bonus applies if enabled |
| 5 | Safe tile | Land on an opponent on a safe tile | Tokens coexist; no capture and no capture bonus |
| 6 | Friendly stack | Move a friendly token onto another friendly token | No friendly capture; second token can form a blockade |
| 7 | Strict blockade | Run `--blockades strict`; attempt to cross/land on 2+ enemy tokens | Illegal move is absent or rejected; every intermediate tile is respected |
| 8 | Safe-pair blockade | Run `--blockades safe_pair`; cross a pair and attempt single-token capture | Passing is allowed; pair cannot be captured by a single token |
| 9 | Kill-to-Enter loop | Use Showcase rules with a player at zero captures | Tokens cannot enter home and loop at the outer boundary; first capture unlocks all their tokens |
| 10 | Exact and non-exact home | Compare `--exact-home-roll` and `--no-exact-home-roll` near the finish | Exact mode rejects overshoot; non-exact mode clamps an otherwise legal move to home |
| 11 | Bonus non-stacking | Observe a roll that triggers more than one bonus reason | Exactly one extra roll; turn count does not increase |
| 12 | Triple six and reset | Observe three consecutive sixes; compare a non-six reset | Third six is forfeited when enabled; first two moves remain; non-six resets streak |
| 13 | Podium and 2P victory | Run 3P/4P with podium on; compare 2P and `--no-podium-mode` | Finished seats are skipped; 3P/4P continue until one unfinished remains; 2P/first-finisher mode ends immediately |
| 14 | Turn-limit draw | Run bots with `--max-turns 4` | Match ends with maximum-turn draw and exit code 0 |
| 15 | Mutual draw | Type `draw`; first decline, then accept with all other players | Decline resumes same turn; acceptance ends match cleanly |
| 16 | Quit and EOF | Type `quit`, decline then accept; separately close stdin | Confirmation works; clean quit with no traceback and exit code 0 |
| 17 | Invalid input | Try letters, symbols, negative/huge token numbers, whitespace, Unicode, blank token input | Helpful rejection and re-prompt; no crash. Blank at roll prompt means Roll |
| 18 | Seeded parity | Run both with identical mode, players, tokens, seed, and choices | Same rolls, states, outcomes, and gameplay narration; code traces may differ intentionally |
| 19 | Wizard defaults and cancellation | Use `--wizard`; press Enter for defaults; separately send EOF | Defaults are valid; EOF cancels cleanly without partial setup |
| 20 | JSON preset and CLI precedence | Load `configs/showcase.json`, then override `--max-turns`, `--speed`, or `--commentary` | Explicit CLI values win; locked geometry cannot be changed |
| 21 | Mixed seats | Combine `--seat human --seat bot`; repeat for 3P/4P | Correct seat types; bot acts automatically; human waits for input |
| 22 | Autoplay and speed | Run `--autoplay`; change slow/normal/fast | Automation drives all seats; speed changes delay only, never dice or rules |
| 23 | Commentary switching | Cycle `commentary` or set `commentary both/off` | Gameplay/code modes change immediately without altering state |
| 24 | GUI controls | Open `--ui gui`; test Roll, token buttons, Pause, Step, Speed, Commentary, Draw, Quit | Controls match manual; Pause blocks auto scheduling; Step still works; terminal controls disable |
| 25 | No-color and encoding | Run with `--no-color` on your terminal; try Unicode input | No ANSI escapes with no-color; unsupported output uses safe fallback; bad input never crashes |

## How to Record a Useful Finding

For each failure, provide:

1. Team member and date.
2. OS, terminal, and Python version.
3. Exact file and command.
4. Seed and player configuration.
5. Exact input sequence.
6. Expected behavior.
7. Observed behavior, including the last 10–20 output lines.
8. Whether OOP, functional, or both failed.
9. Screenshot for GUI-only issues.

If a scenario did not occur naturally, record “not observed” rather than
claiming a pass. Include the seed and number of turns attempted.

## Reports

Fill the matching template without deleting its headings:

- Team 1: `testing/team1_report.md`.
- Team 2: `testing/team2_report.md`.

Include at least two concrete suggestions if you have them, but do not invent
bugs to satisfy a quota. A genuine “no bugs observed” result is valid when
supported by the scenarios and environment recorded.

## Optional Automated Check

```text
python testing/test_suite.py
python scripts/verify_gates.py --stage v1
```

The complete verifier takes several minutes because it runs 1,080 full games
and subprocess comparisons. Report the exact command and result if you run it.
