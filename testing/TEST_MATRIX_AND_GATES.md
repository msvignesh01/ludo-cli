# Exhaustive Test Matrix & Verification Gates

The current v1 implementation is modular. `testing/test_suite.py` discovers every
`testing/test_*.py` module except itself and `parity_test.py`; the parity suite is
run separately so its long deterministic matrix remains visible. Every behavioral
test exercises the real OOP and functional implementations, not mocked rule logic.

## 1. Automated Unit and Edge-Case Suite

Run from the repository root:

```text
python testing/test_suite.py
```

The aggregate currently collects **86 tests**. The coverage is divided as follows.

| Test module | Count | Required coverage |
|---|---:|---|
| `test_automation.py` | 11 | Deterministic bot priorities and tie-breaking; exact OOP/functional bot-event parity; gameplay/code/both/off commentary safety |
| `test_cli_runtime.py` | 7 | Runtime command switching, four-bot autoplay, mixed human/bot draw, renderer equality, ANSI stripping, quit confirmation |
| `test_cli_setup.py` | 8 | CLI-over-JSON/wizard precedence, JSON geometry validation, names and seats, complete flag surface, safe input helpers |
| `test_contracts.py` | 9 | Quick/Classic/Showcase/Classic profiles, allowed overrides, locked geometry, invalid values, JSON round trip, events, 2P/3P/4P seating |
| `test_gui_drawing.py` | 7 | Board/token drawing, stack offsets, coordinates, colors, move descriptions |
| `test_gui_geometry.py` | 5 | Quick 9×9 and Classic 15×15 geometry, route adjacency, home lanes, diagonal yards, JSON serialization |
| `test_gui_session.py` | 14 | Human roll/select, bot scheduling, autoplay, pause/step, speed, commentary, terminal controls, short controller parity |
| `test_rules.py` | 20 | All movement, capture, blockade, bonus, penalty, draw, win, podium, and snapshot-isolation rules listed below |
| `test_wizard.py` | 5 | Showcase defaults, EOF cancellation, existing-value precedence, mixed seat setup |

### Rule and edge-case assertions

| ID | Scenario | Assertion |
|---|---|---|
| R01 | Preset geometry | Quick has 28 track cells, 4 home cells, finish 31, safe `[0,7,14,21]`; Classic has 52, 5, 56, safe `[0,8,13,21,26,34,39,47]` |
| R02 | Seating | 2P uses diagonal starts; 3P/4P use clockwise starts for both modes |
| R03 | Base unlock | A base token moves only on a 6 and enters at its configured start tile |
| R04 | Exact home | Exact-finish moves are legal; overshoots are rejected |
| R05 | Non-exact home | When disabled, an otherwise legal move clamps to `home_finish` |
| R06 | Outer wrap | Player-relative outer steps map around the configured track correctly |
| R07 | Kill-to-Enter | Before the first capture, a token at `track_len - 2` wraps modulo `track_len - 1`; the first capture unlocks private-home entry |
| R08 | Private home | Home-lane tokens have no shared global position and cannot be captured |
| R09 | Single capture | All opponent tokens on a non-safe landing tile reset to base; captures and bonus follow configuration |
| R10 | Stack capture | With blockades disabled, every opponent token in a non-safe landing stack is captured |
| R11 | Safe tile | Safe landings never capture; disabling safe tiles also removes starting-tile immunity |
| R12 | Friendly stack | Friendly tokens coexist and are never captured by their own player |
| R13 | No blockades | Opponents may pass over and capture a same-color stack |
| R14 | Strict blockade | A two-token opponent stack blocks both landing and every crossed intermediate outer tile |
| R15 | Safe-pair blockade | Opponents may pass over a pair, but a single token cannot capture the pair |
| R16 | Bonus independence | Capture and home bonus toggles work independently; six remains a bonus |
| R17 | Non-stacking bonus | A six plus capture or home grants exactly one extra roll |
| R18 | Six-streak reset | A home bonus resets the consecutive-six streak; a non-six capture also resets it before later sixes |
| R19 | Triple six | The third consecutive six is voided, the streak resets, and the turn advances; disabling the rule permits the move |
| R20 | Auto-skip | No legal move resets the streak and advances, including a six with no legal move |
| R21 | Immediate 2P win | In two-player matches the first player to finish all tokens wins immediately |
| R22 | Podium | In 3P/4P podium matches play continues until only one unfinished player remains; finished players are skipped |
| R23 | Turn-cap draw | Reaching `max_turns` produces the canonical maximum-turn draw state |
| R24 | Mutual draw | Acceptance preserves turn count and records `Mutual agreement`; decline does not advance play |
| R25 | Snapshot isolation | Mutating an exported snapshot cannot change config, tokens, or event history in either engine |
| R26 | Initial parity | Initial canonical states and events match exactly |
| R27 | Bad CLI values | Non-integers, huge values, negatives, blanks, malformed commands, EOF, and interruption do not crash the CLI |
| R28 | ANSI purity | `--no-color` output contains no escape sequence; ANSI stripping removes real sequences cleanly |
| R29 | GUI controls | Human/bot/autoplay ownership, pause, step, speed, commentary, draw, and quit match across controllers |
| R30 | JSON and precedence | JSON settings are validated, geometry is locked, and CLI values override JSON/wizard/defaults |

## 2. Full-Game Deterministic Parity Matrix

Run from the repository root:

```text
python testing/parity_test.py
```

The suite executes **1,080 complete games** with seeds `20001` through `21080`.
For each game it compares canonical state initially, after every roll, after every
bot decision, after every move, and at termination. It also compares dice rolls,
move previews, move results, bot decisions, winner/draw fields, turn counts, and
JSON serialization.

| Mode | Players | Tokens | Profile | Blockades | Kill-to-Enter | Podium | Games | Turn cap |
|---|---:|---:|---|---|---|---|---:|---:|
| Quick | 2 | 2 | Classic | none | off | off | 120 | 60 |
| Quick | 3 | 3 | Showcase | safe_pair | on | on | 120 | 60 |
| Quick | 4 | 4 | Showcase | safe_pair | on | on | 120 | 60 |
| Quick | 2 | 1 | Classic | strict | off | off | 120 | 60 |
| Quick | 3 | 2 | Classic | strict | on | off | 120 | 60 |
| Quick | 4 | 3 | Showcase | safe_pair | off | on | 120 | 60 |
| Classic | 2 | 4 | Classic | none | off | off | 60 | 120 |
| Classic | 3 | 4 | Showcase | safe_pair | on | on | 60 | 120 |
| Classic | 4 | 4 | Showcase | safe_pair | on | on | 60 | 120 |
| Classic | 2 | 1 | Classic | strict | off | off | 60 | 120 |
| Classic | 3 | 2 | Classic | strict | on | off | 60 | 120 |
| Classic | 4 | 3 | Showcase | safe_pair | off | on | 60 | 120 |

The matrix deliberately includes both completed wins and turn-cap draws. A game
that exceeds its safety-loop limit fails rather than being silently discarded.

## 3. Real Subprocess CLI Parity

Each case launches both `v1_initial/ludo_oop.py` and `v1_initial/ludo_func.py`
with `subprocess.run`, scripted standard input, `--no-color`, and zero automation
delay. Unless a case explicitly tests code narration, stdout and stderr must be
byte-for-byte equal and both exit codes must be zero.

| ID | Scenario | Additional assertion |
|---|---|---|
| C01 | Seeded complete Quick 2P win | Terminal winner is B and status is `WON` |
| C02 | Seeded real capture | Transcript contains the capture and confirmed clean quit |
| C03 | Invalid commands and quit confirmation | Three malformed commands are rejected; cancelled and confirmed quit both work |
| C04 | Invalid token choices | Non-integer, huge, negative, blank, and illegal choices are handled without a crash |
| C05 | Mutual draw declined then accepted | Decline resumes without advancing; acceptance records the canonical draw state |
| C06 | Three bot seats to max-turn draw | Seat metadata and terminal `DRAW` status match |
| C07 | Mixed human/bot seats under autoplay | Human/bot metadata is preserved while automation reaches the draw cap |
| C08 | Four-bot JSON Showcase demo | JSON loads; CLI overrides cap, delay, and commentary; gameplay draw message appears |
| C09 | Full setup wizard defaults and quit | Showcase defaults are selected and quit exits cleanly |
| C10 | Mid-match code narration | Each process contains only its own real entry points; masking only those code traces yields identical gameplay output |
| C11 | Closed standard input | EOF produces a polite clean quit and exit code zero |
| C12 | Invalid `--max-turns 0` | Both CLIs reject the value before starting and exit non-zero |

## 4. Static and Structural Gates

Run:

```text
python scripts/verify_gates.py --stage v1
```

The verifier recursively audits every Python file in the selected stage and
requires all of the following:

1. Python source parses and contains no unfinished implementation markers.
2. Every absolute import is from the standard library or the stage's own package.
3. `ludo_func.py`, `func_ludo/`, and `shared/` contain **zero `ast.ClassDef` nodes**.
4. `oop_ludo/` defines the required `Token`, `Player`, `Board`, `CLIRenderer`, and
   `LudoGame` classes.
5. Both launchers expose help and the required core flags.
6. Both launchers reject `--max-turns 0` cleanly.
7. The 86-test aggregate passes.
8. The 1,080-game matrix and all subprocess cases pass.
9. The final command exits zero with zero failures and zero warnings.

`--stage v2` applies the same gates to the peer-feedback stage. `--stage final`
also checks the complete documentation/deliverable set; it cannot honestly pass
until genuine peer reports and the corresponding v2 fixes exist.

## 5. Evidence Policy

Observed command results, timestamps, and metrics belong in `TRACKER.md`. A test is
not marked complete merely because it exists, and peer reports must never be
filled with fabricated outcomes.
