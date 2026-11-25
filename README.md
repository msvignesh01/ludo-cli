# CIA1 Multiplayer Ludo Showcase

A complete, deterministic Ludo assignment implemented twice with Python's
standard library:

- **OOP:** `Token`, `Player`, `Board`, `LudoGame`, `BotPolicy`, renderers, CLI,
  and Tkinter GUI.
- **Functional:** zero classes anywhere in the functional/shared packages; the
  same behavior uses functions and explicit dictionaries/lists.

Both implementations support Quick/Classic boards, human and bot seats,
configurable blockades, Kill-to-Enter, Podium Mode, JSON presets, an interactive
wizard, two commentary styles, and exact canonical-state parity.

## Requirements

- Python 3.11 or newer.
- No third-party packages.
- Tkinter only for the optional GUI; the CLI works without it.

## Quick Start

From the repository root:

```text
python play_ludo.py
```

Choose object-oriented or function-based, then choose Quick or Classic.

Skip the prompts and run a seeded match:

```text
python play_ludo.py --engine oop --mode quick --seed 42 --no-color
python play_ludo.py --engine functional --mode classic --seed 42
```

Run either implementation directly:

```text
python v1_initial/ludo_oop.py
python v1_initial/ludo_func.py
```

### Useful Demonstrations

Full wizard:

```text
python v1_initial/ludo_oop.py --wizard
```

Four-bot Showcase preset:

```text
python v1_initial/ludo_func.py --config configs/showcase.json
```

Two-human Classic preset:

```text
python v1_initial/ludo_oop.py --config configs/classic.json
```

Tkinter GUI:

```text
python v1_initial/ludo_func.py --mode quick --seed 42 --ui gui
```

Fast autoplay:

```text
python v1_initial/ludo_oop.py --mode quick --players 4 --seat bot --seat bot --seat bot --seat bot --autoplay --speed fast --commentary gameplay --no-color
```

See [the user manual](docs/USER_MANUAL.md) for every flag, rule, prompt, and GUI
control.

## What Is Configurable?

- Quick: 28-tile route, 9×9 board, 2 default tokens per seat.
- Classic: 52-tile route, 15×15 board, 4 default tokens per seat.
- 2–4 players and 1–4 tokens per player.
- Human or bot seat independently for every player.
- Blockades: none, strict/international, or safe-pair/Ludo King.
- Kill-to-Enter, Podium Mode, exact-home roll, triple-six forfeit, and safe tiles.
- Capture and home bonus independently.
- Turn cap, seed, commentary, interface, and autoplay speed.

Configuration precedence is:

```text
defaults < JSON preset < wizard answers < explicit CLI flags
```

Quick/Classic geometry is locked and validated.

## Rule Highlights

### Kill-to-Enter

A player with no captures cannot enter their private home stretch. Tokens keep
looping around the outer route until that player's first capture unlocks home
entry for all their tokens. This avoids the passive waiting behavior of the
rejected gate-hold design.

### Blockades

| Mode | Passing | Single-token capture of a pair |
|---|---|---|
| `none` | Allowed | Allowed |
| `strict` | Blocked by 2+ enemy tokens | Move is blocked |
| `safe_pair` | Allowed | Disallowed |

Strict mode checks every intermediate tile, not only the destination.

### Podium Mode

In 3P/4P matches, play continues until only one player remains unfinished.
Finished seats are skipped. In 2P, or with Podium Mode disabled, the first
finisher wins.

### Deterministic Bots

Bots prioritize finishing home, capturing, unlocking home entry, safety,
escaping danger, furthest progress, and then the lowest token index. They do not
use a second random stream, so seeded bot matches are repeatable.

## Architecture

```text
play_ludo.py                     Runtime check and engine launcher
v1_initial/
  ludo_oop.py                    17-line OOP package launcher
  ludo_func.py                   17-line functional package launcher
  oop_ludo/                      Classes and OOP rule engine
  func_ludo/                     Functions, state dictionaries, zero classes
  shared/                        Presets, validation, events, geometry, rendering
configs/
  showcase.json                  Four-bot Quick demonstration
  classic.json                   Two-human Classic demonstration
testing/
  test_suite.py                  Aggregate unit/edge-case suite
  parity_test.py                 1,080-game matrix and subprocess CLI tests
  TEST_MATRIX_AND_GATES.md        Coverage and gate definitions
scripts/
  verify_gates.py                Recursive AST/import/runtime gates
docs/
  01_game_design_document.md
  02_flowchart_pseudocode.md
  03_comparison_report.md
  04_ai_interaction_log.md
  05_viva_prep.md
  06_v3_web_build_plan.md
v2_final/                        Reserved for genuine peer-feedback fixes
```

Shared modules contain no game-rule engine. OOP and functional rules are written
independently and compared through canonical JSON-serializable snapshots.

## Verification

Fast unit suite:

```text
python testing/test_suite.py
```

Complete v1 gate, including the multi-minute parity matrix:

```text
python scripts/verify_gates.py --stage v1
```

The observed complete v1 gate passed with exit code 0 and zero warnings:

- 86 unit/edge-case tests.
- 13 parity and subprocess tests.
- 1,080 full games across modes, player counts, token counts, and rule families.
- 362 wins and 718 draws.
- 238,919 canonical snapshots compared with zero mismatches.
- 28 audited Python files: 10 OOP classes and 0 functional/shared classes.

Current evidence is recorded in [TRACKER.md](TRACKER.md). Test coverage is
specified in [testing/TEST_MATRIX_AND_GATES.md](testing/TEST_MATRIX_AND_GATES.md).

## Documentation

- [Game Design Document](docs/01_game_design_document.md)
- [Flowcharts and Pseudocode](docs/02_flowchart_pseudocode.md)
- [OOP vs Functional Comparison](docs/03_comparison_report.md)
- [AI Interaction and Debugging Log](docs/04_ai_interaction_log.md)
- [Viva Preparation](docs/05_viva_prep.md)
- [v3 React/Three.js Build Plan](docs/06_v3_web_build_plan.md)

## Delivery Lifecycle

- **v1_initial:** complete feature showcase and current peer-testing handoff.
- **v2_final:** reserved for fixes supported by real peer reports; currently
  empty. Peer report templates must remain unfilled until humans test the game.
- **v3:** plan only. No React, Next.js, or Three.js application has been built.
  The executable plan defines a pure TypeScript rules core, React controller,
  Three.js presentation layer, Python fixtures, and acceptance gates.
