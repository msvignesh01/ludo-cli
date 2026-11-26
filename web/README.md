# Ludo Showcase Web

[![Next.js](https://img.shields.io/badge/Next.js-16.4.6-000000?logo=nextdotjs)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19.3.0-61DAFB?logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![Three.js](https://img.shields.io/badge/Three.js-0.187.0-000000?logo=threedotjs)](https://threejs.org/)
[![Vitest](https://img.shields.io/badge/Vitest-5.1.1-6E9F18?logo=vitest)](https://vitest.dev/)
[![Playwright](https://img.shields.io/badge/Playwright-1.65.1-2EAD33?logo=playwright)](https://playwright.dev/)

Local-first browser implementation of the CIA1 multiplayer Ludo showcase. The v3
application uses browser storage for local match recovery and does not require a
database or backend.

## Requirements

- Node.js 24 or newer
- npm 12 or newer

## Commands

```bash
npm install
npm run dev
npm run lint
npm run typecheck
npm test
npm run test:parity
npm run test:e2e
npm run test:a11y
npm run build
```

The development server runs at `http://localhost:3000`. Playwright starts its own
server at `http://127.0.0.1:3100`.

## Structure

- `src/game/`: deterministic rules, configuration, RNG, geometry, and view models.
- `src/match/`: turn controller, persistence, and React state provider.
- `src/app/`: Next.js App Router entry points.
- `tests/unit/`: game-core and controller tests.
- `tests/parity/`: Python oracle replay tests.
- `tests/e2e/`: browser and accessibility tests.

The Python implementations under `../v1_initial/` remain the behavioral source of
truth. Online rooms are deferred to a later server-authoritative phase.
