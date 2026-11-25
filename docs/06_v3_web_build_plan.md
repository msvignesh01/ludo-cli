# v3 Browser Build Plan — React, Next.js, and Three.js

**Status:** executable future-build plan only; no v3 application is included in
this repository. **Behavioral source of truth:** the verified Python code under
`v1_initial/`. **Prepared:** 2026-11-25.

## 1. Goal and Boundaries

Build a browser-based Ludo showcase that preserves the Python assignment's
rules, configuration, deterministic bot behavior, canonical snapshots, and
event stream while adding a responsive React interface and an interactive
Three.js board.

### In scope

- Local hot-seat play for 2–4 seats, with any seat marked human or bot.
- Quick and Classic fixed geometry, 1–4 tokens per player, and every current
  rule toggle.
- Showcase and Classic profiles, setup wizard, JSON import/export, and URL
  configuration with the documented precedence.
- Gameplay/code/both/off commentary, pause, single-step, speed, and autoplay.
- Exact canonical-state and event parity with the Python implementation.
- Keyboard operation, accessible DOM controls, reduced motion, and mobile layout.
- Deterministic seeded play and a four-bot demonstration.

### Out of scope for v3.0

- Online accounts, matchmaking, server-authoritative networking, payments, and
  persistent player profiles.
- Replacing the Python OOP/functional deliverables or modifying `v1_initial/`.
- Changing locked board geometry or inventing additional rule families.
- Treating client-side randomness as trustworthy for competitive online play.

If online multiplayer is added later, it requires a separate server-authority
design in which the server owns RNG, validates every action, and sends canonical
snapshots/events to clients. The local v3 engine must not be presented as an
anti-cheat boundary.

## 2. Architecture

Use a single Next.js application with a dependency direction that keeps rules
independent of React and rendering:

```text
URL / JSON / wizard
        |
        v
Configuration resolver
        |
        v
Pure TypeScript game core -----> Python oracle fixtures
        |
        +---- canonical snapshot/event stream
        |
        v
React match controller/store
        |
        +---- accessible DOM HUD, setup, controls, commentary
        |
        v
Three.js board view (presentation only)
```

### Required properties

1. `src/game/**` imports no React, Next.js, DOM, or Three.js APIs.
2. Gameplay transitions are pure or explicitly immutable; UI controls never
   mutate tokens directly.
3. Rendering consumes a canonical snapshot plus a display-only view model.
4. Bot scheduling calls the same transition functions as human controls.
5. `applyMove` resolves captures, finish order, victory, bonus, and turn advance
   exactly once. Controllers must not advance the turn again.
6. The browser never reads Python source at runtime. Python is used offline to
   produce versioned fixtures and expected outcomes.

## 3. Proposed Repository Structure

Create v3 in a separate directory or repository after approval; do not place it
inside the frozen Python stage.

```text
ludo-web/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── globals.css
│   └── error.tsx
├── components/
│   ├── setup/SetupWizard.tsx
│   ├── setup/JsonConfigPanel.tsx
│   ├── game/MatchHud.tsx
│   ├── game/TokenChoiceList.tsx
│   ├── game/CommentaryPanel.tsx
│   ├── game/PlaybackControls.tsx
│   ├── game/DrawDialog.tsx
│   └── board/BoardCanvas.tsx
├── game/
│   ├── types.ts
│   ├── presets.ts
│   ├── config.ts
│   ├── rng.ts
│   ├── geometry.ts
│   ├── view-model.ts
│   ├── events.ts
│   ├── commentary.ts
│   ├── bot.ts
│   ├── engine.ts
│   └── store.ts
├── fixtures/
│   ├── configs/
│   ├── geometry/
│   ├── rng/
│   └── parity/
├── scripts/
│   ├── export-python-fixtures.py
│   └── check-fixture-version.py
├── tests/
│   ├── unit/
│   ├── parity/
│   └── e2e/
├── tools/oracle/
│   └── README.md
├── package.json
├── tsconfig.json
├── next.config.ts
├── vitest.config.ts
└── playwright.config.ts
```

## 4. Canonical Contract

Mirror the Python `export_canonical_state()` schema in `game/types.ts`:

```text
CanonicalSnapshot
  config, max_turns, turn_count, current_player, consecutive_sixes,
  status, winner_index, draw_reason, finish_order, last_event,
  events[], players[]

Player
  index, name, kind, color, start_index, captures_made, tokens[]

Token
  label, steps

Event
  type, turn, player, data
```

`status` is `PLAYING | WON | DRAW | QUIT`. `steps == -1` means base; outer
steps are `0..outer_last_step`; private-home steps are
`track_len - 1..home_finish - 1`; `home_finish` means finished. RNG internals
are deliberately excluded from snapshots.

Preserve the current event names and payload keys: `GAME_STARTED`, `DICE_ROLLED`,
`NO_VALID_MOVES`, `TRIPLE_SIX_FORFEIT`, `BOT_DECISION`, `TOKEN_MOVED`,
`TOKEN_CAPTURED`, `BLOCKADE_FORMED`, `PLAYER_FINISHED`, `BONUS_TURN`,
`TURN_ADVANCED`, `GAME_WON`, `GAME_DRAW`, and `GAME_QUIT`.

### Engine interface

Implement these named exports in `game/engine.ts`:

```text
createGame(config, playerNames, seed?, playerKinds?) -> InternalGame
rollDie(game) -> { game, roll }
processRoll(game, roll) -> { game, result }
previewMove(game, playerIdx, tokenIdx, roll) -> MovePreview
getValidMoves(game, playerIdx, roll) -> number[]
chooseBotMove(game, roll, validMoves) -> { tokenIdx, reason }
recordBotDecision(game, tokenIdx, roll, reason) -> game
applyMove(game, tokenIdx, roll) -> { game, result }
advanceTurn(game) -> game
declareMutualDraw(game) -> game
quit(game) -> game
exportCanonicalState(game) -> CanonicalSnapshot
```

The internal game may contain an RNG object, but it must not leak into the
canonical snapshot. Keep the event array deterministic and clone config,
players, finish order, and event payloads when exporting.

## 5. Rule Port Checklist

Port each rule as a small tested function; do not create one opaque transition
function. The following semantics are mandatory.

| Rule | Required browser behavior | Python reference |
|---|---|---|
| Base unlock | Only a 6 moves `-1 -> 0` | `oop_ludo/engine.py`, `func_ludo/rules.py` |
| Outer mapping | `(start_index + steps) % track_len` | `Board.get_global_pos`, `get_global_pos` |
| Kill-to-Enter | If enabled and captures are zero, crossing from `outer_last_step` wraps modulo `track_len - 1`; first capture unlocks all tokens | `_compute_target`, `_kill_locked` |
| Exact home | Reject overshoot when enabled; otherwise clamp to `home_finish` | `_compute_target` |
| Strict blockade | Two opponent tokens block landing and every crossed outer tile | `_strict_path_blocked` |
| Safe-pair blockade | Opponents can pass a pair but cannot capture it with one token | `_capturable_tokens` |
| No blockades | Pass-over and multi-token capture are allowed | `PROFILE_RULES.classic` |
| Safe tiles | No capture on configured safe tiles; disabling safe tiles removes start immunity too | `Board.is_safe_tile`, `is_safe_tile` |
| Capture | Reset every capturable opponent token on the landing tile and increment captures per token | `apply_move` / `applyMove` |
| Bonus | One bonus for six, capture, or home according to toggles; reasons never stack | `apply_move` / `applyMove` |
| Triple six | Third consecutive six is voided before movement when enabled | `process_roll` / `processRoll` |
| Auto-skip | Empty legal list resets streak and advances, even after a six | `process_roll` / `processRoll` |
| 2P victory | First finisher wins immediately | `required_finishers` calculation |
| Podium | Continue 3P/4P until `player_count - 1` finish; winner is first finisher; skip finished seats | `finish_order`, `advance_turn` |
| Turn cap | Compare after every advance; bonus turns do not increment the count | `advance_turn` / `advanceTurn` |
| Draw/quit | Preserve canonical reason strings and terminal events | `declare_mutual_draw`, `quit` |

`BLOCKADE_FORMED` is an event/preview fact even when blockades are disabled; it
reports that the mover created a friendly pair. Do not use that event as proof
that movement is blocked.

## 6. Deterministic RNG Compatibility

A seed must reproduce the Python dice stream, not merely produce repeatable
browser dice. Implement CPython 3.11-compatible integer-seed MT19937 behavior in
`game/rng.ts`:

1. Convert the integer seed to the absolute bigint and then to little-endian
   32-bit key words, matching Python's integer seed conversion.
2. Implement `init_by_array`, `init_genrand`, MT19937 state generation, tempering,
   and `nextUint32`.
3. Implement `getrandbits(k)` by consuming enough 32-bit words in little-endian
   order.
4. Implement `_randbelow(n)` with `k = n.bit_length()` and rejection sampling.
5. Implement `randint(1, 6)` through that path.

Generate `fixtures/rng/python-rolls.json` from Python for seeds `-1`, `0`, `1`,
`42`, `2**32`, `2**64 + 7`, and at least twenty fixed assignment seeds. Compare
the first 10,000 rolls per seed in Vitest. A mismatch blocks all parity work
until the RNG implementation is corrected.

For UI-only nondeterministic matches, `seed = null` may initialize from browser
entropy. Tests and shared demos must always provide an integer seed.

## 7. Configuration Resolution

Implement `game/config.ts` with immutable presets copied from
`v1_initial/shared/contracts.py`. Lock `track_len`, `home_len`, `outer_last_step`,
`home_finish`, safe-tile indices, start indices, and default turn limits.

Browser precedence is:

1. URL query parameters — the browser equivalent of CLI flags.
2. Imported JSON preset.
3. Wizard values.
4. Built-in defaults.

Validate every boundary: unknown keys, wrong types, booleans masquerading as
integers, player/token counts, non-finite delays, invalid rule enums, negative
turn caps, and geometry overrides. Show errors next to the relevant control and
do not start a partial match.

`configs/showcase.json` and `configs/classic.json` must import without changes.
JSON import is limited to a documented size, parsed as data, and never executed.
Player names are rendered as text, not HTML.

## 8. React Controller and Playback

Use a reducer/store with separate gameplay and presentation actions:

```text
NEW_GAME, ROLL, SELECT_MOVE, BOT_DECIDE, DECLARE_DRAW, QUIT
SET_PAUSED, STEP, SET_SPEED, SET_COMMENTARY, SET_AUTOPLAY
```

Required behavior:

- A human turn waits for Roll; a pending roll exposes only legal token buttons.
- A bot turn schedules one deterministic action at the configured delay.
- Autoplay may drive human seats but preserves their `kind: "human"` metadata.
- Pause stops timers; Step still performs exactly one logical action.
- Slow/normal/fast use 800/350/50 ms, matching the Python GUI.
- Switching commentary never changes canonical game state or events.
- Terminal states disable roll, token, bot, and timer controls.
- Timers are cancelled on unmount, terminal state, pause, and config changes.

The accessible `TokenChoiceList` must expose destination, capture, safe, loop,
home, and blockade preview information without requiring the canvas.

## 9. Three.js Board and Responsive UI

### Geometry

Port `shared/geometry.py` exactly. Quick is a 9×9 cross with 28 route cells;
Classic is a 15×15 cross with 52 route cells. Home lanes, diagonal 2P yards,
clockwise 3P/4P yards, and center finish must match Python JSON fixtures.

Port `shared/gui_support.py:build_gui_view_model` semantics into
`game/view-model.ts`. Markers contain player/token indices, steps, location,
global position, cell, color, and label.

### Rendering

- One instanced or reusable mesh system for cells; one token group per marker.
- Tokens use both color and visible labels/shapes so color is not the only cue.
- Stacked tokens receive deterministic offsets and remain individually selectable
  through the DOM choice list.
- The current player, legal destinations, safe tiles, and last event are visible
  in the HUD, not encoded only by 3D lighting.
- Camera controls are optional; provide Reset View and a fixed top-down view.
- No infinite decorative animation. Respect `prefers-reduced-motion`.
- If WebGL is unavailable, show the complete DOM board and controls rather than
  blocking play.

### Layout

- Desktop: board left, HUD/commentary right.
- Tablet: board above collapsible HUD.
- Mobile: compact board, sticky roll/action area, scrollable token choices.
- Minimum interactive target 44×44 CSS pixels; visible keyboard focus; semantic
  headings and live regions for turn changes and errors.

## 10. Commentary

Port gameplay wording from both Python commentary modules. Code mode names real
TypeScript entry points, for example:

```text
Web: rollDie(game) -> processRoll(game, roll)
Web: applyMove(game, tokenIdx, roll)
```

`both` emits one gameplay line and one code line; `off` emits neither. Code
narration may differ from Python by paradigm label and function names, but
gameplay text and canonical events must match. Tests must mask only the code
lines when comparing user-visible gameplay.

## 11. Python Oracle and Parity Strategy

### Fixture generation

Add `scripts/export-python-fixtures.py` to the future web repository. It imports
the verified Python packages through an explicit path supplied by the user and
writes:

- validated configs and locked geometry;
- RNG roll streams;
- initial snapshots;
- action scripts with rolls, bot choices, and expected previews;
- canonical snapshots after every roll, decision, move, and terminal transition.

Each fixture file records the Python source revision and a schema version.
`check-fixture-version.ts` fails when the oracle revision or schema changes.

### Test layers

1. **Unit:** port all 86 Python test intents to Vitest.
2. **Geometry:** deep-compare Quick/Classic geometry and view models.
3. **RNG:** compare 10,000 rolls for every fixed seed.
4. **Scenario parity:** replay the twelve Python fuzz configurations, initially
   with 10 games each, then all 1,080 before release.
5. **CLI-equivalent parity:** run the web engine in Node against seeded scripted
   actions; compare canonical snapshots, not screenshots.
6. **UI E2E:** Playwright covers wizard defaults, JSON override, URL override,
   full win, capture, invalid inputs, draw, quit, bots, pause/step, commentary,
   keyboard-only play, mobile viewport, and WebGL fallback.
7. **Accessibility:** automated checks plus manual keyboard/focus/screen-reader
   review; no critical or serious violations at release.

## 12. Implementation Phases and Acceptance Gates

### Phase 0 — Freeze the contract

- Record the verified Python revision and fixture schema.
- Create the Next.js/TypeScript project and the folder structure above.
- Copy no Python rule logic into a shared runtime package; use fixtures instead.
- **Accept:** clean install, lint, typecheck, and build; fixture version check
  passes; no application UI is claimed complete.

### Phase 1 — Configuration and RNG

- Implement types, presets, validation, precedence, JSON import, and URL parsing.
- Implement Python-compatible RNG and generate roll fixtures.
- **Accept:** config tests and all RNG fixtures pass; invalid geometry cannot
  produce a game.

### Phase 2 — Pure rules engine

- Implement coordinate mapping, previews, roll processing, captures, blockades,
  Kill-to-Enter, home rules, bonus, triple six, podium, draw, and quit.
- Implement canonical export and event cloning.
- **Accept:** all rule unit tests pass; exported state contains no RNG object.

### Phase 3 — Bots and commentary

- Implement lexicographic bot scoring: finish home, capture, unlock, safe tile,
  escape danger, furthest progress, lowest token index.
- Implement event-driven gameplay and code commentary.
- **Accept:** bot decision and commentary fixtures match Python semantics.

### Phase 4 — Python parity

- Build fixture exporter and replay harness.
- Run twelve configurations and all 1,080 games.
- **Accept:** zero snapshot, preview, result, event, winner, draw, or turn-count
  mismatches; test output records game/roll/move/snapshot totals.

### Phase 5 — React match controller

- Implement reducer/store, setup flow, HUD, token choices, draw/quit dialogs,
  playback controls, and bot timers.
- **Accept:** controller tests pass without a browser; no timer survives pause,
  unmount, or terminal state.

### Phase 6 — DOM board fallback and accessibility

- Implement semantic board/status/token controls before relying on WebGL.
- Complete keyboard, focus, live-region, error, and responsive behavior.
- **Accept:** complete matches are playable with WebGL disabled and by keyboard.

### Phase 7 — Three.js presentation

- Implement geometry, board meshes, markers, stack offsets, selection highlights,
  camera reset, reduced motion, and WebGL error fallback.
- **Accept:** visual markers match view-model fixtures; fallback remains usable.

### Phase 8 — End-to-end hardening

- Run Playwright desktop/mobile suites and accessibility checks.
- Exercise JSON size/type errors, oversized names, invalid URL values, EOF-like
  navigation, terminal controls, and timer cleanup.
- **Accept:** zero critical/serious accessibility findings and zero flaky tests
  across three consecutive full runs.

### Phase 9 — Release

- Run all commands in Section 13.
- Record bundle/performance checks, browser support, fixture revision, and known
  limitations.
- Deploy a preview, run the demo script, then promote only after review.
- **Accept:** production build and preview pass; rollback target is documented.

## 13. Required Commands

The future project must provide and pass:

```text
npm run lint
npm run typecheck
npm test
npm run test:parity
npm run test:e2e
npm run test:a11y
npm run build
```

`test:parity` must print totals for games, wins, draws, rolls, moves, and
snapshots. It fails on any mismatch or skipped scenario. `test:e2e` runs the
same deterministic seed and scripted choices on every run.

## 14. Security, Privacy, and Operations

- No secrets or API keys are needed for local v3. Never place secrets in
  `NEXT_PUBLIC_*` variables.
- Validate URL/JSON input as untrusted data; cap lengths, counts, and import size.
- Render names and commentary as text; do not use `dangerouslySetInnerHTML`.
- Keep game state client-side unless the user explicitly exports it.
- Add a restrictive Content Security Policy compatible with Next.js and WebGL.
- Serve over HTTPS, disable unnecessary permissions, and document browser/WebGL
  requirements.
- Log only anonymized operational errors; do not upload player names or match
  transcripts by default.

## 15. Deployment and Rollback

1. Build and test from a clean checkout with the locked dependency version.
2. Deploy a preview environment and run the full demo/accessibility smoke suite.
3. Promote the reviewed build; do not deploy directly from an unreviewed branch.
4. Monitor client errors, WebGL fallback rate, and failed match initialization.
5. Roll back to the previous immutable deployment if canonical parity, input
   handling, or accessibility regresses. Preserve fixture and source revision
   with every release.

No deployment is performed by this plan.

## 16. Traceability to the Python Deliverable

| Approved requirement | v3 implementation | Proof |
|---|---|---|
| Quick/Classic fixed boards | `presets.ts`, `geometry.ts`, `BoardCanvas` | Geometry fixtures, visual tests |
| Three rule families | `engine.ts` rule helpers | Ported R04–R16 tests |
| Human/bot seats and autoplay | `store.ts`, playback controls | Controller and E2E tests |
| Deterministic bots | `bot.ts` | Decision fixtures |
| Commentary switching | `commentary.ts`, panel | Unit and E2E tests |
| CLI/GUI parity | URL config, DOM fallback, Three view | Full match E2E |
| JSON/wizard/default precedence | `config.ts`, setup components | Boundary tests |
| Seed and canonical parity | `rng.ts`, `engine.ts`, fixtures | 1,080-game replay |
| Frozen v1 and peer-fix v2 | Separate future repository | Release checklist |

The web version is a new delivery target. It does not replace the requirement to
keep `v1_initial/` frozen after handoff or to place genuine peer-feedback changes
in `v2_final/` with regression evidence.
