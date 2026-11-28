# CIA1 Multiplayer Ludo Showcase — Project Plan

## Purpose

Build and verify one complete Ludo showcase in two authentic programming
paradigms while preserving exact behavioral parity. Deliver a full-feature
`v1_initial/` for peer testing, reserve `v2_final/` for real peer-driven fixes,
and implement the approved local-first browser release under `web/` with a
future online-room design kept separate.

## Current Status

| Phase | Status |
|---|---|
| Architecture and questionnaire decisions | Complete |
| Shared contracts, presets, geometry, and validation | Complete |
| Independent OOP and functional rule engines | Complete |
| Bots, CLI, wizard, JSON, autoplay, and Tkinter GUI | Complete |
| Unit, parity, subprocess, AST, and import gates | Complete: full v1 gate observed at exit 0, zero warnings |
| Current architecture documentation and v3 plan | Complete |
| v3 local-first web implementation | Complete: 141 Vitest tests and 50 browser tests passed |
| Web Python parity | Complete: 1,080 games, 238,919 snapshots, zero mismatches |
| Web accessibility automation | Complete: axe, keyboard, focus, contrast, reduced motion, fallback |
| GitHub push and Vercel production release | Pending reviewed release step |
| Human peer testing | Pending real external testers |
| Peer-driven v2 changes | Not started; `v2_final/` remains reserved |
| Final submission gate | Pending genuine peer reports and v2 fixes |

## Non-Goals

- No third-party Python dependencies.
- No online accounts, matchmaking, database, analytics payload, or deployed
  backend in v3.0.
- No fabricated peer reports or invented peer-feedback improvements.
- No shared Python rule engine disguised as two implementations.
- No automatic force-push, history rewrite, or deployment claim without
  observed evidence.

## Binding Constraints

1. Python 3.11+ standard library only.
2. Zero `ast.ClassDef` nodes in `ludo_func.py`, `func_ludo/`, and `shared/`.
3. Required OOP classes in `oop_ludo/`: `Token`, `Player`, `Board`,
   `CLIRenderer`, and `LudoGame`.
4. Identical canonical state after every action for identical configuration,
   seed, and decisions.
5. Identical CLI arguments, gameplay narration, board output, outcomes, and exit
   behavior, except intentional paradigm-specific code traces.
6. Locked geometry: Quick 28/4 on 9×9; Classic 52/5 on 15×15.
7. All movement and rendering dimensions derive from validated configuration.
8. Bad input, EOF, and Ctrl+C must not produce an unhandled exception.
9. `v1_initial/` becomes immutable after handoff; accepted peer fixes go to
   `v2_final/` with a changelog.
10. Every success claim requires an observed command result.
11. `web/src/game/` must not import React, Next.js, DOM, or Three.js APIs.
12. Web geometry stays locked and every movement/rendering value derives from
    validated configuration.
13. Web seeded dice must match CPython 3.11 integer-seed MT19937 output.
14. Canonical web snapshots and event payloads must match Python; RNG internals
    remain outside canonical snapshots.
15. Browser storage is local-only in v3.0; no credentials or match data are sent
    to a backend.
16. Every gameplay action remains available through semantic DOM controls;
    Three.js is optional presentation.
17. No emojis; use technology badges and Mermaid diagrams where useful.

## Approved Rule Decisions

- Showcase defaults: safe-pair blockades, Kill-to-Enter, Podium Mode, exact home,
  triple-six forfeit, safe tiles, capture bonus, and home bonus.
- Classic profile: no blockades, normal home entry, first-finisher victory.
- Kill-to-Enter uses Option A: tokens loop on the outer route until the owner's
  first capture unlocks the home stretch.
- Gate Hold was rejected because it permits passive waiting and stalemates.
- Strict blockades prevent passing and landing on 2+ same-color enemy tokens.
- Safe-pair blockades permit passing but prevent single-token capture of a pair.
- Podium play continues in 3P/4P until one unfinished player remains; 2P ends at
  the first finisher.
- Six, capture, and home bonus reasons grant one extra roll and never stack.
- Bonus rolls do not increment the turn count.
- Bot priority: home, capture, unlock, safety, escape, progress, lowest index.

## Architecture

### Shared contracts, not shared rules

`shared/` owns:

- Mode presets and configuration validation.
- Player seating and display specifications.
- Event schemas and independent event copies.
- Board geometry and coordinate drawing.
- CLI rendering and GUI view-model helpers.

It contains no Ludo rule decisions.

### OOP package

`oop_ludo/` owns:

- `Token`, `Player`, and `Board` domain models.
- `LudoGame` orchestration and configurable rule logic.
- `BotPolicy` deterministic choice logic.
- `Commentary` and `CLIRenderer` presentation.
- `CliApplication`, `GuiSession`, and `LudoGUI` interaction.

### Functional package

`func_ludo/` owns:

- `create_game_state()` and `export_canonical_state()`.
- `rules.py` functions for preview, roll, move, turn, draw, and quit.
- Function-based bot, commentary, renderer, CLI, and GUI session modules.
- Explicit dictionaries/lists instead of classes or class aliases.

### Canonical contract

Both engines export:

- Configuration and maximum turns.
- Turn count, current player, and six streak.
- Status, winner, draw reason, finish order, and last event.
- Complete ordered event history.
- Player seat metadata, capture counts, token labels, and token steps.

RNG internals are excluded. Exported containers are independent and
JSON-serializable.

### Configuration precedence

```text
defaults < JSON preset < wizard answers < explicit CLI flags
```

The wizard asks only unresolved values. Locked geometry is never overridden.

### UI and scheduling

The Tkinter GUI calls a headless GUI controller. Automated timing uses Tkinter
`after()` scheduling only. Pause blocks scheduling; Step remains available.
Canonical rules never depend on widgets or wall-clock timing.

### Web v3 architecture

`web/src/game/` is a framework-independent TypeScript port of the canonical
rules contract. `MatchController` owns gameplay transitions, pending choices,
playback state, and revisions. `MatchProvider` subscribes React, persists each
revision, and schedules at most one automated action.

The semantic DOM board is always mounted. Three.js adds an optional
presentation layer and cannot become the only way to play. Versioned
localStorage stores canonical state, RNG state, pending choices, configuration,
and preferences after whole-record validation.

Python remains an offline oracle. Committed fixtures reproduce CPython-compatible
dice streams and 1,080 complete games. Vercel is the approved frontend host;
Render is reserved for a future server-authoritative WebSocket room service.

## Requirement-to-Evidence Map

| Requirement | Implementation | Verification |
|---|---|---|
| Quick/Classic geometry | `shared/contracts.py`, `shared/geometry.py` | Geometry tests and contract tests |
| 2–4 players, 1–4 tokens | Shared builder, both engines | Contract/rule tests and parity scenarios |
| Human/bot seats | Both CLI modules and bot policies | Automation and GUI-session tests |
| Blockade variants | Both rule engines | Strict path, safe-pair, and stack tests |
| Kill-to-Enter Option A | Both target calculators | Wrap/unlock tests and parity matrix |
| Podium Mode | Both move/turn engines | Finish-order and 2P victory tests |
| Exact home and triple six | Both target/roll engines | Focused boundary tests |
| Safe tiles and bonuses | Both capture/turn engines | Toggle and non-stacking tests |
| JSON and wizard | `shared/cli_support.py` | Precedence and subprocess tests |
| CLI/GUI parity | Shared rendering plus independent controllers | Snapshot and subprocess comparisons |
| Commentary switching | Both commentary modules | Event and mid-match tests |
| Deterministic seed | Isolated `random.Random(seed)` | 1,080-game seeded matrix |
| Draw/quit/bad input | Both engines and CLIs | Rule, GUI, and subprocess tests |
| Zero-class functional design | `func_ludo/` and `shared/` | Recursive AST gate |
| Stdlib only | All stage Python files | Recursive import gate |

## Phase Checklist

### Phase 0 — Design and Contract Lock

- [x] Read repository governance and original assignment artifacts.
- [x] Resolve questionnaire choices and rejected alternatives.
- [x] Lock geometry, coordinate model, canonical schema, and lifecycle.
- [x] Record architecture in `docs/01_game_design_document.md` and
  `docs/02_flowchart_pseudocode.md`.

### Phase 1 — Shared Foundation

- [x] Implement validated Quick/Classic and Showcase/Classic configuration.
- [x] Implement seating, events, copying, geometry, rendering, and setup input.
- [x] Keep all shared modules zero-class and rules-free.
- [x] Test locked geometry, invalid values, JSON round trips, and precedence.

### Phase 2 — Independent Rule Engines

- [x] Implement OOP models and `LudoGame`.
- [x] Implement functional state creation and `rules.py`.
- [x] Implement base entry, movement, home, capture, safe tiles, blockades,
  Kill-to-Enter, bonus turns, triple six, podium, turn cap, draw, and quit.
- [x] Keep `apply_move()` solely responsible for post-move turn resolution.
- [x] Add focused rule and canonical-state tests for both paradigms.

### Phase 3 — Bots and Interfaces

- [x] Implement identical deterministic bot priorities with independent code.
- [x] Implement gameplay and code commentary.
- [x] Implement full CLI flags, wizard, JSON presets, commands, and autoplay.
- [x] Implement Tkinter GUI, headless GUI controller, pause/step/speed, token
  buttons, draw, and quit.
- [x] Test automation, input handling, rendering parity, and controller parity.

### Phase 4 — Verification Gates

- [x] Aggregate modular unit tests.
- [x] Build a 12-scenario, 1,080-game full-game matrix.
- [x] Compare canonical state initially, after every roll, after every bot
  decision, after every move, and at termination.
- [x] Add real subprocess CLI tests for wins, captures, invalid input, draw,
  quit, wizard, JSON, EOF, and code narration.
- [x] Recursively audit AST class constraints, standard-library imports,
  required files, and unfinished markers.
- [x] Observe `python scripts/verify_gates.py --stage v1` exit 0 with zero
  failures and zero warnings.
- [x] Record actual counts and metrics in `TRACKER.md`.

### Phase 5 — Documentation

- [x] Rewrite root README and user manual for the complete Showcase.
- [x] Rewrite GDD and flowchart/pseudocode for current code.
- [x] Create the seven-question comparison report from measured v1 evidence.
- [x] Create viva preparation guide and v3 executable build plan.
- [x] Update AI interaction log with real prompts, decisions, and failures.
- [x] Finalize peer-test kit and clean report templates.
- [x] Re-run documentation checks after all edits.

### Phase 6 — Human Peer Testing

- [ ] Hand off `v1_initial/`, presets, user manual, and peer-test kit.
- [ ] Peer Team 1 executes its assigned scenarios and fills its real report.
- [ ] Peer Team 2 independently executes its assigned scenarios and fills its
  real report.
- [ ] Preserve both reports as evidence; do not rewrite tester conclusions.
- [ ] Triage findings by severity, reproducibility, and parity impact.

### Phase 7 — Peer-Driven v2

- [ ] Copy the verified v1 modular structure into `v2_final/` without modifying
  `v1_initial/`.
- [ ] Update v2 package-relative launcher imports for the new stage.
- [ ] Implement each accepted finding symmetrically in both paradigms.
- [ ] Add a regression test that fails for the original peer defect.
- [ ] Record peer report reference, code change, and proof in
  `v2_final/CHANGELOG.md`.
- [ ] Run `python scripts/verify_gates.py --stage v2` and require exit 0 with
  zero warnings.

### Phase 8 — Final Submission

- [ ] Confirm v1 remained unchanged after handoff.
- [ ] Update comparison metrics if v2 materially changes the code.
- [ ] Append real peer outcomes and fixes to the AI interaction log.
- [ ] Ensure peer reports contain genuine results rather than template text.
- [ ] Run `python scripts/verify_gates.py --stage final`.
- [ ] Require exit 0 and zero warnings before claiming final completion.

### Phase 9 — v3 Local-First Web Release

- [x] Approve the local-first architecture and Vercel/future-Render boundary.
- [x] Implement strict TypeScript contracts, CPython-compatible RNG, geometry,
  rules, bots, and commentary.
- [x] Replay all 1,080 Python oracle games with zero mismatches.
- [x] Implement controller, timer scheduling, persistence, setup, match, result,
  draw, quit, import/export, and recovery flows.
- [x] Implement the semantic DOM board and optional Three.js presentation.
- [x] Pass desktop/mobile functional and accessibility browser suites.
- [x] Add technology badges, Mermaid diagrams, architecture, user-flow, and
  deployment documentation.
- [ ] Review and commit the complete release source.
- [ ] Push the reviewed commit to `msvignesh01/ludo-cli` without force-push.
- [ ] Deploy to Vercel with root directory `web/` and smoke-test production.
- [x] Keep online rooms and Render deployment explicitly deferred.

## Verification Protocol

For every implementation change:

1. Read the governing requirement and affected code.
2. Add or update a focused regression test.
3. Observe the failure when the behavior is missing or broken.
4. Fix the smallest root cause in both paradigms.
5. Run the aggregate unit suite.
6. Run the complete v1 or v2 verifier.
7. Inspect every failure; never weaken an assertion to obtain a pass.
8. Record command, result, counts, and notes in `TRACKER.md`.

The complete parity suite is intentionally multi-minute. Fast tests do not
replace it for rule, state, or engine changes.

## Peer-Feedback Triage Rules

- **Rules/parity defect:** highest priority; reproduce in both engines.
- **Crash or invalid-input failure:** high priority; add subprocess coverage.
- **Incorrect turn/bonus/podium transition:** high priority; compare events.
- **Presentation-only defect:** fix shared rendering where appropriate, then
  verify both CLIs.
- **Enhancement request:** accept only if it preserves approved scope and
  paradigm separation.
- **Unreproducible report:** keep the original report and request concrete steps;
  do not invent a fix or outcome.

## v3 Boundary

The approved browser application is implemented under `web/`. Its pure
TypeScript rules core, React controller, optional Three.js board, semantic DOM
fallback, Python-generated fixtures, and Vercel deployment path are documented
in `docs/06_v3_web_build_plan.md` through `docs/09_deployment.md`.

v3.0 is local hot-seat play only. Online rooms require a separate approved,
server-authoritative phase with RNG and action validation on the server. The
current local client is not an anti-cheat boundary and no Render backend is
deployed.

## Definition of Done

A stage is done only when:

- Required files exist and contain no unfinished markers.
- Recursive AST and standard-library import audits pass.
- Unit and edge-case tests pass completely.
- The full parity matrix and subprocess CLI suite pass.
- The selected verifier exits 0 with zero warnings.
- Documentation matches the actual stage and observed metrics.
- No peer evidence has been fabricated.

The current v1 gate satisfies the automated portion. Human peer testing, v2
fixes, and final-stage completion remain honestly pending.
