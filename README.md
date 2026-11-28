# CIA1 Multiplayer Ludo Showcase

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16.4.6-000000?logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-19.3.0-20232A?logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?logo=typescript&logoColor=white)
![Three.js](https://img.shields.io/badge/Three.js-0.187.0-000000?logo=threedotjs&logoColor=white)
![Vitest](https://img.shields.io/badge/Vitest-5.1.1-6E9F18?logo=vitest&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-1.65.1-2EAD33?logo=playwright&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-frontend-000000?logo=vercel&logoColor=white)

A complete deterministic Ludo assignment with two independent Python
implementations and a local-first browser release:

- **Python OOP:** `Token`, `Player`, `Board`, `LudoGame`, `BotPolicy`, renderers,
  CLI, and Tkinter GUI.
- **Python functional:** zero classes anywhere in the functional/shared packages;
  the same behavior uses functions and explicit dictionaries/lists.
- **Web v3:** Next.js, React, strict TypeScript, an optional Three.js board, and
  a complete semantic DOM fallback.

All three implementations support Quick/Classic boards, human and bot seats,
configurable blockades, Kill-to-Enter, Podium Mode, deterministic seeded play,
and canonical-state parity.

## Requirements

Python deliverables:

- Python 3.11 or newer.
- No third-party packages.
- Tkinter only for the optional GUI; the CLI works without it.

Web deliverable:

- Node.js 24 or newer and npm.
- A modern browser. WebGL is optional.
- Python 3.11 only for offline fixture regeneration and parity verification.

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

## Browser Quick Start

From `web/`:

```text
npm ci
npm run dev
```

Open `http://localhost:3000`. Start a deterministic two-seat Quick match with:

```text
http://localhost:3000/?mode=quick&profile=classic&players=2&tokens=1&seed=42&max_turns=120
```

The browser app supports the full setup wizard, JSON import/export, URL
overrides, hot-seat and bot seats, autoplay, pause/step, commentary, save
recovery, mutual draw, confirmed quit, and a complete DOM board when WebGL is
unavailable. Match data stays in localStorage unless the user exports it.

See [the web README](web/README.md) for scripts, URL aliases, storage limits,
and testing details.

### Useful Python Demonstrations

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
play_ludo.py                     Runtime check and Python engine launcher
v1_initial/
  ludo_oop.py                    17-line OOP package launcher
  ludo_func.py                   17-line functional package launcher
  oop_ludo/                      Classes and OOP rule engine
  func_ludo/                     Functions, state dictionaries, zero classes
  shared/                        Presets, validation, events, geometry, rendering
configs/
  showcase.json                  Four-bot Quick demonstration
  classic.json                   Two-human Classic demonstration
web/
  src/app/                       Next.js App Router entry points
  src/components/                Setup, match, board, and result components
  src/game/                      Framework-independent TypeScript rules core
  src/match/                     Controller, provider, and persistence
  fixtures/                      Python-generated offline oracle data
  tests/                         Vitest parity and Playwright browser suites
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
  07_web_architecture.md
  08_web_user_flow.md
  09_deployment.md
v2_final/                        Reserved for genuine peer-feedback fixes
```

Shared Python modules contain no game-rule engine. OOP and functional rules are
written independently and compared through canonical JSON-serializable
snapshots. The browser core follows the same canonical contract and is verified
against Python-generated fixtures rather than importing Python at runtime.

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

The observed web release checks also passed:

- 141 Vitest unit, RNG, geometry, controller, persistence, and parity tests.
- 1,080 Python oracle games with 238,919 compared snapshots and zero
  mismatches.
- 50 Playwright tests across Desktop Chrome and Pixel 7.
- Automated WCAG 2.1 A/AA scans, keyboard focus, dialog focus, contrast,
  reduced-motion, and forced WebGL-fallback checks.
- Formatting, lint, strict typecheck, and optimized production build.

Current evidence is recorded in [TRACKER.md](TRACKER.md). Test coverage is
specified in [testing/TEST_MATRIX_AND_GATES.md](testing/TEST_MATRIX_AND_GATES.md).

## Documentation

- [Game Design Document](docs/01_game_design_document.md)
- [Flowcharts and Pseudocode](docs/02_flowchart_pseudocode.md)
- [OOP vs Functional Comparison](docs/03_comparison_report.md)
- [AI Interaction and Debugging Log](docs/04_ai_interaction_log.md)
- [Viva Preparation](docs/05_viva_prep.md)
- [v3 Browser Release Status](docs/06_v3_web_build_plan.md)
- [Web Architecture](docs/07_web_architecture.md)
- [Web User Flow](docs/08_web_user_flow.md)
- [Deployment and Operations](docs/09_deployment.md)
- [Web Developer README](web/README.md)

## Delivery Lifecycle

- **v1_initial:** complete Python feature showcase and current peer-testing
  handoff.
- **v2_final:** reserved for fixes supported by real peer reports; currently
  empty. Peer report templates must remain unfilled until humans test the game.
- **v3:** implemented local-first browser release under `web/`, with Vercel as
  the approved frontend host. Online rooms and a Render room service are
  documented future work, not active features.
