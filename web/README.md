# Ludo Showcase Web

![Next.js](https://img.shields.io/badge/Next.js-16.4.6-000000?logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-19.3.0-20232A?logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?logo=typescript&logoColor=white)
![Three.js](https://img.shields.io/badge/Three.js-0.187.0-000000?logo=threedotjs&logoColor=white)
![Vitest](https://img.shields.io/badge/Vitest-5.1.1-6E9F18?logo=vitest&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-1.65.1-2EAD33?logo=playwright&logoColor=white)

The v3 browser release of the CIA1 Multiplayer Ludo Showcase. It provides local
hot-seat play for 2–4 seats, deterministic bots, Quick/Classic boards, every
approved rule toggle, commentary, autoplay, save recovery, and an optional
Three.js board. The complete semantic DOM board remains playable without WebGL.

## Requirements

- Node.js 24 or newer.
- npm 10 or newer.
- A modern browser with JavaScript enabled. WebGL is optional.

Python 3.11 is needed only to regenerate or verify the offline oracle fixtures.
It is not needed to run the web application.

## Run Locally

From this directory:

```bash
npm ci
npm run dev
```

Open `http://localhost:3000`. For a deterministic two-seat Quick match:

```text
http://localhost:3000/?mode=quick&profile=classic&players=2&tokens=1&seed=42&max_turns=120
```

Supported URL aliases include `players`, `tokens`, and `max-turns` as well as
the canonical `player_count`, `tokens_per_player`, and `max_turns` names.
Configuration precedence is URL, imported JSON, wizard, then built-in defaults.

## Available Commands

| Command                | Purpose                                         |
| ---------------------- | ----------------------------------------------- |
| `npm run dev`          | Start the Next.js development server            |
| `npm run build`        | Create the optimized production build           |
| `npm start`            | Serve the production build locally              |
| `npm run lint`         | Run ESLint                                      |
| `npm run typecheck`    | Run strict TypeScript checking                  |
| `npm test`             | Run all Vitest unit and Python-parity tests     |
| `npm run test:parity`  | Run only the Python oracle replay               |
| `npm run test:e2e`     | Run desktop and mobile Playwright flows         |
| `npm run test:a11y`    | Run automated accessibility and keyboard checks |
| `npm run format:check` | Check Prettier formatting                       |

The Playwright configuration starts the app on `http://127.0.0.1:3100` and runs
Desktop Chrome at 1280×720 and Pixel 7 at 412×839.

## Project Structure

```text
src/
  app/                     Next.js layout, page, global styles, error boundary
  components/
    LudoApp.tsx            Setup/match switching and save recovery
    setup/                 Wizard, URL resolution, JSON import
    match/                 HUD, choices, playback, dialogs, result, commentary
    board/                 Semantic DOM board and optional Three.js canvas
  game/                    Framework-independent rules, RNG, geometry, bots
  match/                   Controller, React provider, validated persistence
fixtures/                  Python-generated RNG, geometry, rules, game oracle
scripts/                   Offline fixture export and version checks
tests/
  unit/                    Contracts, RNG, geometry, rules, bots, controller
  parity/                  Full Python oracle replay
  e2e/                     Desktop/mobile functional and accessibility flows
```

`src/game/` does not import React, Next.js, DOM, or Three.js APIs. The controller
owns transitions and exposes cloned canonical snapshots. React components never
mutate tokens directly.

## Determinism and Python Parity

The TypeScript RNG reproduces CPython 3.11 integer-seed MT19937 behavior,
including negative and large seeds. The replay suite checks initial state, every
processed roll, every bot decision, every applied move, and final state.

The observed release replay result is:

```text
Web parity matrix: games=1080, wins=362, draws=718,
rolls=93403, moves=71678, snapshots=238919, mismatches=0
```

The oracle revision and fixture hashes are recorded in `fixtures/manifest.json`.
Python is an offline verification tool; the browser never reads Python source at
runtime.

## Browser Storage and Privacy

A valid match is stored under `ludo-showcase:match:v1` in localStorage. The save
contains the canonical snapshot, RNG cursor, pending legal choices, resolved
configuration, and playback preferences. The entire record is validated before
restore. Invalid saves return a typed error and offer a reset action.

- Browser autosave limit: 1 MiB.
- JSON import/export limit: 64 KiB.
- No account, database, analytics payload, or deployed backend is used in v3.0.
- Player names and match transcripts leave the browser only when the user
  explicitly exports a match.

## Accessibility and Fallback

The release includes automated WCAG 2.1 A/AA axe scans, keyboard-only flows,
dialog focus trapping/restoration, associated form errors, live result and draw
announcements, measured contrast checks, reduced-motion checks, and a forced
WebGL-failure test. Automation is evidence, not a claim of human screen-reader
testing.

The Three.js canvas is presentation-only. If WebGL creation or context recovery
fails, the complete DOM board and controls remain available.

## Deployment

Vercel should use this `web/` directory as the project root, the Next.js
framework preset, `npm run build`, and `main` as the production branch. No
environment secrets are required for local play.

See [the deployment guide](../docs/09_deployment.md) for release, smoke-test,
rollback, and future Render room-service instructions. Online multiplayer is
not active in v3.0.
