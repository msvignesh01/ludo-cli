# Game Design Document — CIA1 Multiplayer Ludo Showcase

**Project:** CIA1 Python Programming Assignment
**Implementations:** object-oriented and strictly zero-class functional Python
**Runtime:** Python 3.11+ standard library only
**Interfaces:** ANSI CLI and Tkinter GUI
**Players:** 2–4 local hot-seat seats, each human or bot
**Modes:** Quick and Classic
**Rule profiles:** Showcase and Classic, with individual rule overrides

## 1. Design Goal

Deliver a demonstration-ready Ludo game that is enjoyable to play, easy to
explain in a viva, and rigorously testable. The same game is implemented in two
authentic paradigms. They share configuration contracts and presentation
geometry, but each owns its rule logic and state transitions.

The design has four priorities:

1. **Correct rules:** every move is derived from validated preset geometry.
2. **Exact parity:** canonical state and events match after every action.
3. **Clear code:** small modules, concise docstrings, type hints, and no external
   dependencies.
4. **Useful demonstration:** bots, autoplay, GUI controls, JSON presets, and
   commentary make the full feature set easy to show.

## 2. Game Modes and Locked Geometry

Mode controls board scale. These values cannot be overridden by JSON, wizard, or
CLI settings.

| Parameter | Quick | Classic |
|---|---:|---:|
| Shared outer track length | 28 | 52 |
| Board grid | 9×9 cross | 15×15 cross |
| Private home length | 4 | 5 |
| Default tokens per player | 2 | 4 |
| Last outer personal step | 26 | 50 |
| Finished step (`home_finish`) | 31 | 56 |
| 4P/3P clockwise starts | `[0, 7, 14, 21]` | `[0, 13, 26, 39]` |
| 2P diagonal starts | `[0, 14]` | `[0, 26]` |
| Safe global tiles | `[0, 7, 14, 21]` | `[0, 8, 13, 21, 26, 34, 39, 47]` |
| Default turn cap | 100 | 250 |

Tokens per player remain configurable from 1 to 4 in either mode. Changing token
count does not change the board or route.

Seat order is Red, Green, Yellow, Blue, with prefixes `R`, `G`, `Y`, and `B`.
Two players sit diagonally. Three or four players use clockwise seating.

## 3. Rule Profiles

A profile supplies defaults; every non-geometry rule can then be overridden.

| Setting | Showcase default | Classic profile |
|---|---|---|
| Blockades | `safe_pair` | `none` |
| Kill-to-Enter | enabled | disabled |
| Podium Mode | enabled | disabled |
| Exact home roll | enabled | enabled |
| Triple-six forfeit | enabled | enabled |
| Safe tiles | enabled | enabled |
| Capture bonus | enabled | enabled |
| Home bonus | enabled | enabled |

The **mode** and **profile** are separate. For example, Classic geometry can run
with Showcase rules, and Quick geometry can run with Classic rules.

## 4. Match Configuration

### Configuration sources

The resolver applies this precedence, from lowest to highest:

```text
defaults < JSON preset < interactive wizard < explicit CLI flags
```

The wizard asks only for values not already supplied by a higher-priority
source. If no mode is supplied by any source, the user is prompted for Quick or
Classic.

### Configurable settings

- Quick/Classic mode and Showcase/Classic profile.
- 2–4 players and 1–4 tokens per player.
- Player names and human/bot seat type per player.
- Blockade variant: `none`, `strict`, or `safe_pair`.
- Kill-to-Enter, Podium Mode, exact home, triple-six forfeit, safe tiles,
  capture bonus, and home bonus toggles.
- Positive turn cap and integer seed.
- CLI/GUI interface, autoplay, delay/speed, and commentary mode.

Names are trimmed, blank names receive defaults, and duplicates are made unique.
Seat lists are validated and padded with the appropriate human/bot default.

## 5. Token Coordinate System

Each token stores one integer `steps` value.

| `steps` | Location | Shared global position |
|---:|---|---|
| `-1` | Base/yard | none |
| `0..outer_last_step` | Shared outer track | `(start_index + steps) % track_len` |
| `track_len - 1..home_finish - 1` | Private home lane | none |
| `home_finish` | Finished home | none |

The private home lane is immune to captures. The finished value is derived from
`track_len - 1 + home_len`; movement and rendering never hardcode 28, 52, 31,
or 56.

### Kill-to-Enter exception

When Kill-to-Enter is enabled and a player has made zero captures, tokens cannot
enter the private lane. If a move would cross the outer boundary from
`outer_last_step`, it continues around an outer loop of length `track_len - 1`:

```text
new_steps = raw_target % (track_len - 1)
```

The first capture unlocks home entry for every token owned by that player. This
is **Option A**, chosen because it creates active pressure to capture. The
rejected Gate Hold option could allow players to wait passively at the gate.

## 6. Core Turn Rules

### Rolling and base entry

- Each match owns an isolated `random.Random(seed)` instance.
- Rolls are uniform integers from 1 to 6.
- A base token can leave only on a 6 and lands on its owner's start tile.
- If safe tiles are enabled, start tiles are safe and entry cannot capture.
- Disabling safe tiles also removes start-tile immunity.

### Movement and home

- Active tokens move forward by the rolled amount.
- With exact-home enabled, overshooting `home_finish` is illegal.
- With exact-home disabled, an otherwise legal overshoot clamps to
  `home_finish`.
- Finished tokens never move.
- If no legal move exists, the turn is skipped automatically.

### Bonus turns

One extra roll is granted when any enabled condition occurs:

- the roll is 6;
- at least one opponent token is captured and capture bonus is enabled;
- a token reaches home and home bonus is enabled.

Reasons do not stack. A six plus capture still grants exactly one extra roll.
Bonus rolls do not increment `turn_count`.

### Consecutive sixes

- A non-six resets the streak, even when it earns a capture bonus.
- Reaching home resets the streak.
- With triple-six forfeit enabled, the third consecutive six is voided before
  movement, the streak resets, and the turn advances.
- Moves made on the first and second sixes remain valid.
- An automatic no-move skip also resets the streak.

## 7. Captures, Safe Tiles, and Blockades

A capture is considered only when the mover lands on a shared outer tile.
Private-home and finished positions never capture.

### Safe tiles

If the landing tile is configured as safe, opponents may coexist there and no
capture or capture bonus occurs.

### Friendly stacks

A player's own tokens may share a tile. They are never captured by that player.

### Blockade variants

| Variant | Opponent pass-over | Single-token landing on enemy pair | Landing on enemy single |
|---|---|---|---|
| `none` | allowed | captures the whole stack | captures |
| `strict` | blocked | blocked | captures if path is clear |
| `safe_pair` | allowed | pair is immune | captures |

Strict blockades check **every intermediate outer tile crossed by the move**, not
only the destination. Safe-pair blockades do not block movement; they only make a
two-token enemy stack immune to a single-token capture.

When a non-safe landing captures a stack with no blockade protection, every
opponent token on that tile returns to base. `captures_made` increases once per
captured token.

## 8. Finishing, Victory, and Podium Mode

A player finishes when all of their tokens reach `home_finish`.

- **Two players:** the first finisher wins immediately.
- **Podium disabled:** the first finisher wins in any match.
- **Podium enabled with 3/4 players:** play continues until `player_count - 1`
  players have finished. Finished seats are skipped. The first finisher is the
  canonical winner, and `finish_order` records the podium.

When a player finishes but the match must continue, control advances to the next
unfinished player. No bonus is granted for that finishing move.

## 9. Draws and Quitting

### Turn-cap draw

Whenever control advances and `turn_count >= max_turns`, the match ends with:

```text
status = "DRAW"
draw_reason = "Maximum turn limit reached"
```

### Mutual draw

Before rolling, the active player may request `draw`. Every other player is
asked in seat order. All must accept. A decline resumes the same active player
without advancing the turn.

```text
status = "DRAW"
draw_reason = "Mutual agreement"
```

### Quit

`quit` or `q` asks for confirmation. EOF and Ctrl+C also end cleanly. The CLI
returns exit code 0 for a normal quit and prints no traceback.

## 10. Deterministic Bot Policy

Bots use only public legal-move previews and choose the lexicographic maximum of:

1. Finish Home.
2. Capture.
3. Unlock Kill-to-Enter with the first capture.
4. Land on a safe tile.
5. Escape a tile currently threatened by an opponent.
6. Advance furthest around the route.
7. Lowest token index as the final tie-break.

The selected token and reason are recorded as a `BOT_DECISION` event. The same
policy is implemented independently in both paradigms.

## 11. Interfaces

### CLI

The CLI shows the board, players, rules summary, last event, legal move previews,
and selected commentary. Commands at the roll prompt are:

| Input | Action |
|---|---|
| Enter, `r`, `roll` | Roll |
| `draw` | Request mutual draw |
| `quit`, `q` | Confirmed quit |
| `commentary` | Cycle gameplay → code → both → off |
| `commentary MODE` | Set `gameplay`, `code`, `both`, or `off` |
| `speed SPEED` | Set `slow`, `normal`, or `fast` |

Both implementations expose identical setup and gameplay flags. Colors use ANSI
with Windows VT100 initialization and a clean `--no-color` path.

### Tkinter GUI

The GUI provides:

- Quick 9×9 or Classic 15×15 cross-shaped board.
- Token markers for base, track, home lane, and finished center.
- Human Roll and legal token buttons.
- Bot/autoplay scheduling with Pause, Step, and speed controls.
- Commentary mode switching.
- Mutual-draw and quit confirmation.
- Player home/capture status and last-event display.

The GUI controller is headless-testable. Tkinter `after()` only schedules an
action; it does not own game rules.

## 12. Canonical State and Events

Both engines export the same JSON-serializable snapshot containing config,
turn counters, status, winner/draw fields, finish order, last event, events, and
players/tokens. RNG internals are excluded.

Exports are independent copies. Tests mutate returned config, token, and event
data to prove that the live match cannot be changed through a snapshot.

The event stream is the shared source for commentary, GUI updates, tests, and a
future browser adapter. Gameplay narration is identical. Code narration names
real entry points and therefore differs by paradigm.

## 13. Architecture and Paradigm Separation

```text
v1_initial/
├── ludo_oop.py / ludo_func.py       thin launchers
├── shared/                          presets, validation, CLI setup, geometry, view helpers
├── oop_ludo/                        Token, Player, Board, LudoGame, CLI/GUI adapters
└── func_ludo/                       explicit state dictionaries and modular functions
```

- `shared/` contains contracts and presentation helpers, not a shared rules
  engine.
- `oop_ludo/` owns behavior on `Token`, `Player`, `Board`, and `LudoGame`.
- `func_ludo/` passes an explicit `state` dictionary through pure queries and
  transitions.
- `func_ludo/`, `shared/`, and the functional launcher contain zero class
  definitions, enforced by AST audit.
- All Python imports are standard library or internal package imports.

## 14. Verification and Acceptance

The v1 gate runs:

```text
python testing/test_suite.py
python testing/parity_test.py
python scripts/verify_gates.py --stage v1
```

Acceptance requires:

- 86 modular unit/edge-case tests passing.
- 1,080 complete deterministic games matching after every roll, bot decision,
  move, and terminal state.
- Real subprocess CLI parity for wins, captures, invalid input, draw, quit, EOF,
  wizard, JSON, bots, mixed seats, and code narration.
- Zero classes in functional/shared code and all required OOP classes present.
- Standard-library-only imports and no unfinished implementation markers.
- Zero gate failures and zero warnings.

The authoritative observed results are recorded in `TRACKER.md`.

## 15. Delivery Lifecycle

- **`v1_initial/`:** complete pre-handoff feature set. Freeze after peer handoff.
- **`v2_final/`:** only genuine peer-reported fixes and UX improvements, applied
  symmetrically with regression tests and a changelog.
- **Peer reports:** human-completed evidence only; never fabricated.
- **v3:** a future React/Next.js/Three.js browser adaptation. This repository
  contains its executable build plan, not a web application.
