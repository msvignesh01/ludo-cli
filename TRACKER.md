# TRACKER.md — Execution Ledger and Verification Evidence

> Record exact commands and observed results. Never mark a gate complete without
> an exit-code-0 result, and never fabricate human peer-testing evidence.

## Current Status

- **Date:** 2026-11-25
- **Runtime observed:** Python 3.11.0
- **Active milestone:** Complete v1 peer-testing handoff
- **v1 automated gate:** PASS, exit code 0, 0 failures, 0 warnings
- **Final submission gate:** NOT RUN/PASSED; genuine peer reports and v2 fixes do
  not exist yet
- **v2 status:** Reserved and unpopulated

## Phase Checklist

### Phase 0 — Design and Contract Lock

- [x] Read `AGENTS.md`, original specs, tests, and verifier.
- [x] Lock Quick/Classic geometry and the unified `steps` coordinate model.
- [x] Resolve blockades, Kill-to-Enter Option A, Podium Mode, bot priority,
  configuration precedence, and v1/v2/v3 scope.
- [x] Record selected and rejected questionnaire options.

### Phase 1 — Shared Foundation

- [x] Implement validated presets, profiles, seating, events, and copying.
- [x] Implement geometry, CLI rendering, GUI drawing, and setup helpers.
- [x] Keep `shared/` zero-class and free of game-rule logic.
- [x] Test invalid values, locked geometry, JSON round trips, and precedence.

### Phase 2 — Independent Engines

- [x] Implement OOP `Token`, `Player`, `Board`, and `LudoGame`.
- [x] Implement functional `create_game_state()` and `rules.py` with zero
  classes.
- [x] Implement capture, safe tiles, all blockade variants, Kill-to-Enter,
  exact/non-exact home, triple six, bonus toggles, podium, turn cap, draw, and
  quit.
- [x] Export identical canonical JSON-serializable state from both engines.
- [x] Add focused rule and boundary tests.

### Phase 3 — Bots and Interfaces

- [x] Implement independent deterministic bot policies.
- [x] Implement gameplay and paradigm-specific code commentary.
- [x] Implement complete CLI flags, wizard, JSON presets, mixed seats, and
  autoplay.
- [x] Implement Tkinter GUI and headless GUI controller with pause, step, speed,
  commentary, draw, and quit.
- [x] Verify controller and drawing behavior through automated tests. Actual
  human visual GUI testing remains part of peer testing.

### Phase 4 — Automated Verification

- [x] Aggregate all modular unit and edge-case tests.
- [x] Implement 12-scenario, 1,080-game parity matrix.
- [x] Compare canonical snapshots initially, after every roll, after every bot
  decision, after every move, and at termination.
- [x] Implement real subprocess CLI comparisons for wins, captures, invalid
  input, draw, quit, wizard, JSON, EOF, and code narration.
- [x] Recursively audit class constraints, standard-library imports, required
  files, and unfinished markers.
- [x] Observe final `python scripts/verify_gates.py --stage v1` exit code 0 with
  0 failures and 0 warnings.

### Phase 5 — Documentation

- [x] Rewrite `README.md` and `docs/USER_MANUAL.md`.
- [x] Rewrite `docs/01_game_design_document.md` and
  `docs/02_flowchart_pseudocode.md`.
- [x] Create `docs/03_comparison_report.md` with measured v1 evidence.
- [x] Create `docs/05_viva_prep.md`.
- [x] Create `docs/06_v3_web_build_plan.md` without creating a web app.
- [x] Update `testing/TEST_MATRIX_AND_GATES.md` and
  `testing/peer_test_kit.md`.
- [x] Keep both peer report templates unfilled.
- [x] Update this tracker and the real AI interaction/debugging log.

### Phase 6 — Human Peer Testing

- [ ] Deliver the v1 handoff to Peer Team 1.
- [ ] Deliver the v1 handoff to Peer Team 2.
- [ ] Receive a completed `testing/team1_report.md` from real testers.
- [ ] Receive a completed `testing/team2_report.md` from real testers.
- [ ] Triage reproducible findings by severity and parity impact.

### Phase 7 — Peer-Driven v2

- [ ] Copy the verified modular v1 structure into `v2_final/` after handoff.
- [ ] Implement accepted peer fixes symmetrically.
- [ ] Add a failing regression test for every accepted defect.
- [ ] Write `v2_final/CHANGELOG.md` mapping peer evidence to code and tests.
- [ ] Pass `python scripts/verify_gates.py --stage v2`.

### Phase 8 — Final Submission

- [ ] Confirm `v1_initial/` is unchanged after handoff.
- [ ] Update comparison and metrics if v2 materially changes the code.
- [ ] Append genuine peer outcomes to the AI interaction log.
- [ ] Pass `python scripts/verify_gates.py --stage final`.

## Verification Evidence Log

| Date | Command | Observed result | Evidence |
|---|---|---|---|
| 2026-11-25 | `python --version` | Python 3.11.0 | Runtime output |
| 2026-11-25 | `python testing/test_suite.py` inside fresh final gate | `Ran 86 tests in 0.126s`, `OK` | Fresh final v1 gate output |
| 2026-11-25 | `python testing/parity_test.py` inside fresh final gate | `Ran 13 tests in 296.485s`, `OK` | Fresh final v1 gate output |
| 2026-11-25 | `python scripts/verify_gates.py --stage v1` | Exit 0; `Failures: 0 \| Warnings: 0` | Post-fix final v1 gate output |
| 2026-11-25 | AST/source measurement script | OOP 9 files/1,520 lines/10 classes/104 functions or methods; functional 9/1,626/0/89; shared 7/1,190/0/38 | Measured AST output |
| 2026-11-25 | Targeted subprocess rerun before final gate | `Ran 5 tests in 1.542s`, `OK` | Corrected narration/input/draw expectations |
| 2026-11-24 | First complete v1 gate | Exit 0; 86 tests; 13 parity tests in 252.222s; 0 failures/warnings | Complete first gate output |

The final rerun followed the narration/input test corrections and a symmetric
engine fix for resetting the consecutive-six streak when a token reaches home.
It is the latest complete code gate.

## Final Gate Metrics

```text
GATE PASSED: Stage 'v1' achieved 100% perfection!
Failures: 0 | Warnings: 0
AST summary: 28 Python files, 10 OOP classes, 0 functional/shared classes
Ran 86 tests in 0.126s
OK
Ran 13 tests in 296.485s
OK
Parity matrix: games=1080, wins=362, draws=718,
rolls=93403, moves=71678, snapshots=238919
```

The parity matrix covers Quick/Classic, 2P/3P/4P, 1–4 tokens, Classic/Showcase
profiles, all blockade modes, and Kill-to-Enter/Podium combinations. The exact
scenario table is in `testing/TEST_MATRIX_AND_GATES.md`.

## Static Audit Results

- Required OOP classes found: `Token`, `Player`, `Board`, `CLIRenderer`,
  `LudoGame`.
- Class definitions in functional/shared/launcher functional code: 0.
- Non-standard-library imports: 0.
- Missing required stage files: 0.
- Unfinished source markers detected by the verifier: 0.
- CLI `--help` and invalid `--max-turns 0` smoke checks: passed for both
  implementations.

## Known Boundaries

- Human peer testing has not occurred.
- GUI widgets, scheduling, drawing, and headless controller behavior are tested;
  no claim of a completed human visual GUI demonstration is made.
- `v2_final/` is intentionally empty.
- The v3 browser application has not been built; only its executable plan exists.
- `--stage final` is not currently eligible to pass and has not been claimed as
  passing.
