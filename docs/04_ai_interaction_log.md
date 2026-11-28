# AI Interaction Log — Multiplayer Ludo Showcase

This log records real user prompts, approved design decisions, generated
implementation choices, test failures, root causes, fixes, and observed
verification results. It does not fabricate peer feedback.

## 1. Original Expansion Request

The user supplied a detailed proposal and answered its embedded questions. The
following excerpts are verbatim from the actual request:

> “let's have both and user select it obviously with explanation so they know
> what they are getting into”

This selected both blockade variants rather than forcing one rule family.

> “Option A** (authentic, and our `max_turns` draw cap prevents infinite
> deadlocks), but is option B really problematic explain”

This selected Kill-to-Enter Option A and requested an explanation of why Gate
Hold was rejected.

> “lock board geometry to **Quick (28 tiles)** and **Classic (52 tiles)** while
> making every other parameter (token count `1–4`, every rule toggle, turn cap,
> speed, seating) fully customizable?”

The user answered “yes follow this,” locking geometry while retaining granular
rule configuration.

> “Let's have both and should be able to seamlessly toggle between match too”

This selected gameplay and code/paradigm commentary with mid-match switching.

> “Option A”

This selected a modular folder per paradigm instead of oversized single files.

> “Yes”

This confirmed that v1 should contain the full feature set and v2 should be
reserved for real peer-testing fixes.

> “Option B”

This selected a complete executable v3 build plan rather than only a short
roadmap. The later v3 request expanded that plan into a working browser release.

The same request specified mixed human/bot seats, four-bot autoplay,
Podium Mode, deterministic heuristic bots, GUI playback controls, JSON/wizard/
CLI configuration, and JSON-serializable events.

## 2. Follow-Up Questionnaire Decisions

The design questionnaire resolved the remaining architectural choices:

- Expand the current pre-handoff v1 instead of freezing the older basic CLI.
- Use Showcase defaults rather than Classic baseline defaults.
- Deliver the initial executable v3 plan; a later request expanded this into a
  working local-first browser release.
- Share contracts and presentation helpers rather than duplicate every package.
- Reject one shared rules engine with two thin wrappers because it would make
  the functional implementation inauthentic.

These choices produced two independent rule engines with a common canonical
state/event contract.

## 3. Implementation Approval

The user's actual approval message was:

> “proceed with implementation and explain everything we planned together till
> now in easy to understand way including my original ask and the now proposed
> plan and how and why both different and the questionaire that you asked me
> explain the selected options and the rejected ones too”

Implementation proceeded after that approval. The explanation distinguished
the original basic assignment from the expanded Showcase and documented both
selected and rejected alternatives.

## 4. Generated Architecture

AI generated the modular implementation and tests. Important decisions were:

### Independent paradigms, shared contracts

- OOP state lives on `Token`, `Player`, `Board`, and `LudoGame`.
- Functional state lives in explicit dictionaries created by
  `create_game_state()`.
- Shared modules contain presets, validation, seating, event creation, geometry,
  and rendering only.
- Both engines independently implement movement, capture, turn, draw, and win
  logic.

### Canonical parity

Both engines export the same configuration, counters, status, finish order,
players, tokens, and event stream. RNG internals are excluded. Event copies use
schema-aware recursive copying so snapshots are independent without copying
arbitrary object graphs.

### Configuration precedence

```text
defaults < JSON preset < wizard answers < explicit CLI flags
```

The wizard asks only unresolved questions. Locked geometry cannot be overridden.

### Kill-to-Enter Option A

At the outer boundary, a capture-locked token loops:

```python
# OOP — v1_initial/oop_ludo/engine.py:92
if (
    self._kill_locked(player)
    and token.is_on_outer_track(self.board.outer_last_step)
    and raw_target >= self.board.track_len - 1
):
    lap_len = self.board.track_len - 1
    new_steps = raw_target % lap_len
```

```python
# Functional — v1_initial/func_ludo/rules.py:104
if (
    _kill_locked(state, player)
    and 0 <= old_steps <= config["outer_last_step"]
    and raw_target >= config["track_len"] - 1
):
    lap_len = int(config["track_len"]) - 1
    new_steps = raw_target % lap_len
```

Gate Hold was rejected because tokens could wait outside the home stretch,
encouraging passive stalemates instead of active competition.

### Turn ownership

`apply_move()` owns bonus, advance, finish, and terminal resolution. This
invariant prevented callers from advancing twice after one legal move.

### Deterministic bots

Both policies score home, capture, unlock, safety, escape, progress, and lowest
token index. They consume no separate random stream.

### GUI separation

Tkinter widgets call a headless GUI session controller. `after()` is used only
for automated scheduling, not rule decisions. This made pause, step, and speed
testable without opening a display.

## 5. Real Debugging Traces

### Trace 1 — Obsolete Tests Imported Retired APIs

- **Symptom:** The old test suite produced 26 import/API errors after the
  modular migration.
- **Root cause:** Tests imported launcher wrappers and constructors that no
  longer represented the modular packages.
- **Fix:** Replaced obsolete imports with a standard-library test aggregator and
  adapters for the actual OOP and functional APIs.
- **Verification:** The aggregate suite reached 86 passing tests; final gate
  reported `Ran 86 tests in 0.098s` and `OK`.

### Trace 2 — Direct Parity Script Could Not Import Packages

- **Symptom:** Running `python testing/parity_test.py` directly failed before
  test execution.
- **Root cause:** Python placed `testing/`, not the repository root, on the
  import path.
- **Fix:** Insert the repository root into `sys.path` before package imports.
- **Verification:** The parity script ran independently and inside the verifier.

### Trace 3 — Test Harness Advanced Twice After a Move

- **Symptom:** Engine parity drifted at turn boundaries even though the two
  engines implemented the same move result.
- **Root cause:** The parity harness called `advance_turn()` after `apply_move()`,
  but `apply_move()` already resolves bonus, advance, finish, or win.
- **Fix:** Remove the extra test-side advance and compare state immediately after
  the real move.
- **Verification:** The corrected engine matrix passed with 1,080 games. The
  latest complete run compared 238,919 snapshots after the subsequent home-on-six
  rule fix. No game-rule assertion was weakened.

### Trace 4 — Full Event Copies Made Parity Unnecessarily Slow

- **Symptom:** Representative Classic games took roughly 4–5 seconds because
  every action deep-copied the complete event history.
- **Root cause:** Generic deepcopy traversed every event and nested payload after
  every roll, decision, and move.
- **Fix:** Add `clone_json_value()` and schema-aware `clone_event()` in
  `v1_initial/shared/contracts.py`, then use them in both canonical exports.
- **Verification:** Representative Classic games dropped to about 0.7–0.8
  seconds, and snapshot independence tests still passed. The historical recorded
  matrix finished in 296.485 seconds; the latest observed release-preparation
  rerun took 183.240 seconds after the home-on-six rule correction. The earlier
  `32023.840` value was a recording typo, not a measured runtime.

### Trace 5 — Rule Fixtures Used the Wrong Board Type

- **Symptom:** Focused rule tests failed while constructing a Quick board.
- **Root cause:** `Board` expects a validated configuration dictionary, not the
  string `"quick"`.
- **Fix:** Construct fixtures with `Board(make_config(...))`.
- **Verification:** The affected rule tests passed in the aggregate suite.

### Trace 6 — Friendly Pass-Over Fixture Had the Wrong Active Player

- **Symptom:** A test intended to prove friendly pass-over did not model the
  intended mover.
- **Root cause:** The fixture left the wrong player active when evaluating the
  move.
- **Fix:** Use the test adapter's `set_current()` and activate the intended
  player before evaluating the move.
- **Verification:** The friendly-stack and blockade tests passed.

### Trace 7 — Home-Bonus Fixture Accidentally Finished the Player

- **Symptom:** A home-bonus test entered terminal/finish logic instead of the
  intended ordinary home-token bonus.
- **Root cause:** The fixture already had every other token finished.
- **Fix:** Keep another token unfinished so the move tests the bonus path rather
  than player completion.
- **Verification:** Home-bonus reset and non-stacking tests passed.

### Trace 8 — Code Narration Normalization Missed Same-Line Traces

- **Symptom:** One subprocess parity test failed although gameplay output was
  identical.
- **Root cause:** The normalizer masked only lines beginning with `OOP:` or
  `Functional:`. A prompt and code trace could share a line.
- **Fix:** Replace line-prefix logic with occurrence-based regex normalization of
  the paradigm-specific trace through the next newline.
- **Verification:** The code-narration subprocess test passed, while separate
  assertions still prove OOP and functional traces are intentionally distinct.

### Trace 9 — Whitespace-Only Roll Input Was Counted as Invalid

- **Symptom:** The invalid-command subprocess expectation was off by one.
- **Root cause:** The CLI intentionally treats whitespace-only roll input as
  Enter/Roll, not as an unknown command.
- **Fix:** Expect three unknown commands in that scripted sequence.
- **Verification:** The invalid-command and quit-confirmation test passed.

### Trace 10 — Draw Tests Expected Commentary That Was Disabled

- **Symptom:** Three draw-related subprocess tests failed on missing `Draw: ...`
  text.
- **Root cause:** Those tests used `--commentary off`; draw narration was
  intentionally absent. Canonical status and last-event text were still
  present.
- **Fix:** Assert `Last event: ...` and the `| DRAW` status line instead of
  disabled commentary.
- **Verification:** All five affected subprocess tests passed together:
  `Ran 5 tests in 1.542s`, `OK`.

### Trace 11 — Unused Normalizer Local Removed Before Final Gate

- **Symptom:** A redundant empty list remained after the regex rewrite.
- **Root cause:** Mechanical cleanup missed during the narration fix.
- **Fix:** Remove the unused local without changing behavior.
- **Verification:** Included in the final complete v1 gate after Trace 12; exit 0,
  0 failures, 0 warnings.

### Trace 12 — Home-on-Six Move Did Not Reset the Six Streak

- **Symptom:** The strengthened `test_home_bonus_resets_six_streak` test failed
  in both engines with an actual consecutive-six count of 2 instead of 0.
- **Root cause:** The test originally finished a token on a non-six, so
  `process_roll()` reset the streak before movement and masked a missing reset in
  `apply_move()`. Reaching home on a six left the streak at 2 in both engines.
- **Investigation:** The first revised fixture also offered a base token a legal
  six-roll entry. Moving that second token to step 30 left only the finishing
  token legal, proving the failure was the home-move reset rather than fixture
  ambiguity.
- **Fix:** Reset `consecutive_sixes` immediately after detecting
  `preview["reached_home"]` in `v1_initial/oop_ludo/engine.py` and the functional
  equivalent in `v1_initial/func_ludo/rules.py`.
- **Verification:** The targeted regression passed, all 86 modular tests passed,
  and the complete 1,080-game parity matrix and v1 gate passed with zero failures
  and warnings.

## 6. What Testing Did Not Prove

- The engine matrix proved canonical rule/state parity, not human visual GUI
  quality. GUI controller and drawing tests passed; real visual peer testing is
  still pending.
- The project has no genuine peer reports, so no v2 peer-fix claim is made.
- The v3 browser release has unit, parity, browser, and automated accessibility
  evidence, but it has not yet been pushed, deployed, or smoke-tested in
  production. Human screen-reader and visual usability reviews remain pending.
- A seed repeats dice, not arbitrary human choices; exact transcript reproduction
  also requires the same decisions.

## 7. Final Observed Verification

Latest complete command:

```text
python scripts/verify_gates.py --stage v1
```

Observed result:

```text
Ran 86 tests in 0.126s
OK
Ran 13 tests in 296.485s
OK
Parity matrix: games=1080, wins=362, draws=718,
rolls=93403, moves=71678, snapshots=238919
AST summary: 28 Python files, 10 OOP classes, 0 functional/shared classes
GATE PASSED: Stage 'v1' achieved 100% perfection!
Failures: 0 | Warnings: 0
```

Exit code: 0.

## 8. Reflection

AI accelerated package scaffolding, parallel engine implementation, rendering,
GUI construction, and test generation. Verification was still necessary because
plausible code failed at import boundaries, fixture setup, event-copy cost,
narration normalization, turn-transition assumptions, and a home-on-six streak
reset that a non-six fixture had masked.

The strongest safeguard was not visual similarity between two programs. It was
an explicit canonical contract, independent rule implementations, and tests
that compared behavior after every action. Human review remains necessary for
rule intent, viva explanation, usability, and genuine peer feedback.

## 9. v3 Browser Request and Approved Scope

After the verified Python work, the user requested:

> “start with v3 after thoroughly testing everything and figure out where to
> host it; maybe vercel for frontend and render for backend no database needed i
> guess we can use browser memory itself; create all necessary documentations
> and update stuff if needed which are already present and then push to github
> using credentials of msvignesh01; use tech stack badges where necessary, no
> emojis and add flowcharts, mermaid diagrams, architecture, user flow among
> other stuff when and where needed”

The user selected:

> “option 3 but host on vercel atleast”

The user then approved the local-first architecture with “Approve
(Recommended)” and the written specification with “Approve and build
(Recommended).” Subsequent instructions were “continue exactly from where we
left.”

The implemented v3.0 boundary is:

- Next.js frontend hosted on Vercel when release deployment succeeds;
- local hot-seat human/bot play in the browser;
- match and preference persistence in versioned localStorage;
- no accounts, database, analytics payload, or deployed backend;
- a pure TypeScript rules core verified against Python fixtures;
- an always-mounted semantic DOM board with optional Three.js presentation;
- a separate future Render/Node WebSocket room-service design that is not
  implemented or deployed;
- no emojis, with technology badges and Mermaid diagrams in documentation.

This expanded the earlier plan-only v3 decision into a working application
without changing the verified Python baseline.

## 10. v3 Engineering Decisions

### Framework-independent rules

`web/src/game/` contains configuration, CPython-compatible MT19937 RNG, geometry,
rules, canonical snapshots, events, bot policy, and commentary. It does not
import React, Next.js, browser DOM, or Three.js APIs. This keeps gameplay
testable in Node and prevents rendering or timer behavior from changing rules.

### Exact seeded randomness

The web RNG implements CPython integer-seed conversion, `init_by_array`, MT19937
regeneration, `getrandbits`, and `_randbelow` rejection sampling. Match seeds stay
safe JavaScript integers while the RNG API accepts arbitrary `BigInt` values.
Committed fixtures include 26 RNG streams.

### Controller-owned transitions

`MatchController` owns mutable internal state and publishes cloned canonical
snapshots through revisions. `applyMove` resolves post-move turn transitions
once. The React provider schedules at most one automated action and clears the
timer on pause, terminal state, unmount, or replacement. Persistence validates
the complete record, pending choice, and RNG state before restore.

### Accessible fallback before presentation

The semantic DOM board remains mounted while WebGL is available. Canvas failure
or context loss leaves the same board and controls usable. Three.js never owns
legal moves or becomes the only playable representation.

### Offline Python oracle

The fixture exporter and replay suite compare canonical state and events against
the verified Python behavior at initial state, roll, bot decision, move, and
terminal boundaries. RNG implementation details remain outside canonical state.

## 11. Real v3 Debugging and Review Traces

### Trace 13 — Setup Speed Precedence

- **Symptom:** URL and CLI-equivalent setup values did not consistently win over
  JSON/wizard defaults.
- **Root cause:** One setup-resolution path merged speed separately from the
  other values.
- **Fix:** Apply the same documented `defaults < JSON < wizard < URL` precedence
  to every setting.
- **Verification:** Setup and controller tests pass, including deterministic URL
  startup.

### Trace 14 — Generated Validator Imports Broke Typecheck

- **Symptom:** TypeScript reported unused imports in generated Next.js validator
  output during a clean build.
- **Root cause:** A development-generated type file was being considered by the
  strict no-unused checks.
- **Fix:** Align generated build state with the project typecheck/build workflow
  instead of relaxing strictness.
- **Verification:** `npm run typecheck` and `npm run build` both exited 0.

### Trace 15 — WebGL Availability Callback Could Loop

- **Symptom:** The canvas availability callback could trigger repeated renderer
  setup.
- **Root cause:** Availability state and renderer initialization were coupled
  without a stable callback boundary.
- **Fix:** Stabilize callback behavior and separate renderer lifecycle from
  presentation availability.
- **Verification:** Board rendering, forced-failure fallback, and browser tests
  pass.

### Trace 16 — Immediate-Start URL Race

- **Symptom:** A URL requesting immediate autoplay could begin before the
  controller/provider lifecycle was fully ready.
- **Root cause:** Startup scheduling happened before controller publication.
- **Fix:** Start automation from the provider's committed lifecycle and clear
  scheduling when the controller changes or unmounts.
- **Verification:** Immediate-start and controller/provider browser tests pass.

### Trace 17 — 3D and Fallback Board Stacking

- **Symptom:** Real screenshots showed the optional canvas and semantic board
  competing for the same visual position.
- **Root cause:** The overlay was visible while its availability and positioning
  lifecycle were not yet settled.
- **Fix:** Tie overlay visibility to confirmed WebGL availability and keep the
  semantic board underneath as the complete fallback.
- **Verification:** Desktop/mobile screenshots were inspected and browser tests
  pass; this remains automated evidence rather than a human usability sign-off.

### Trace 18 — Accessibility Contrast, Semantics, and Focus

- **Symptom:** Initial axe and measured-style checks found low-contrast focus and
  board text, a list semantic conflict, focus escaping dialogs, an unassociated
  JSON error, and missing draw/result announcements.
- **Root cause:** Visual tokens and ARIA/live-region behavior had not been tested
  together against WCAG-oriented checks.
- **Fix:** Add a measured focus token, darken board labels, preserve native list
  semantics, trap dialog focus, associate errors with inputs, and add polite
  live announcements for draw handoffs and terminal results.
- **Verification:** The strengthened accessibility suite passes on desktop and
  mobile. No assertion was weakened.

### Trace 19 — Programmatic Focus Did Not Prove Focus-Visible

- **Symptom:** One focus-contrast test measured `outline-style: none` after
  calling `element.focus()`.
- **Root cause:** Programmatic focus does not reliably reproduce Chromium's
  keyboard `:focus-visible` heuristic.
- **Fix:** Navigate to the control with real Tab key presses, then assert the
  visible outline and its measured contrast.
- **Verification:** Focused desktop/mobile checks and the complete 50-test
  browser suite pass.

### Trace 20 — Formatting and Process Cleanup

- **Symptom:** Prettier initially failed on generated JSON fixtures; a stopped npm
  wrapper also left a stale Next.js production process on port 3100.
- **Root cause:** Fixture formatting and child-process lifecycle needed explicit
  handling.
- **Fix:** Format the fixture JSON and stop only the identified stale child
  process.
- **Verification:** `npm run format:check` passes and subsequent browser runs use
  the intended server.

### Trace 21 — Independent Reviewer Did Not Produce a Report

- **Symptom:** A background code-reviewer invocation failed with an invalid
  metadata rename error before returning findings.
- **Result:** No independent reviewer report exists. The release relies on
  direct source review and observed automated gates, and does not claim an
  independent review.

## 12. v3 Observed Verification

Fresh release-preparation output on 2026-11-29:

```text
npm run format:check
All matched files use Prettier code style!

npm run typecheck
passed

npm run lint
passed

npm run build
Next.js 16.4.6
Static routes: / and /_not-found
Build passed

npm run test:e2e
50 passed (49.8s)

npm test
Test Files  13 passed (13)
Tests       141 passed (141)
Web parity matrix: games=1080, wins=362, draws=718,
rolls=93403, moves=71678, snapshots=238919, mismatches=0
Duration 287.18s
```

The fresh Python v1 release gate also exited 0:

```text
Ran 86 tests in 0.110s
OK
Ran 13 tests in 183.240s
OK
Parity matrix: games=1080, wins=362, draws=718,
rolls=93403, moves=71678, snapshots=238919
AST summary: 28 Python files, 10 OOP classes, 0 functional/shared classes
GATE PASSED: Stage 'v1' achieved 100% perfection!
Failures: 0 | Warnings: 0
```

The final production build was also opened at 1440×1000 and 412×839. Setup
and post-roll match screenshots were captured and inspected. Both viewports
reported no console errors and no horizontal overflow. This was agent visual
inspection, not human usability sign-off.

These results establish local automated correctness and accessibility checks.
They do not establish production availability, human peer approval, human
screen-reader approval, or final Python submission completion.
