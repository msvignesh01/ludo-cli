# Viva Preparation — Multiplayer Ludo Showcase

## 1. The Thirty-Second Project Summary

> We built the same configurable multiplayer Ludo game twice. The OOP version
> models tokens, players, a board, the match engine, bots, and interfaces as
> classes. The functional version keeps the same match state in dictionaries
> and passes it through functions, with zero class definitions. Both use shared
> configuration, geometry, and rendering contracts, but each implements the
> rules independently. We verify them with unit tests, real CLI subprocesses,
> and 1,080 deterministic full-game comparisons.

Do not describe the functional version as an OOP wrapper. Its rule engine,
state, bot policy, CLI, and GUI session are function-based.

## 2. What to Show First

1. Open `v1_initial/oop_ludo/models.py` and point out `Token`, `Player`, and
   `Board`.
2. Open `v1_initial/func_ludo/state.py` and point out the explicit `state`
   dictionary.
3. Show `LudoGame.apply_move()` and `apply_move(state, ...)`.
4. Run the quick test suite.
5. Show the recorded full verifier output in `TRACKER.md`.
6. Run a seeded match or open the GUI.

A complete full gate takes several minutes. Do not start it casually during a
short live demonstration; show the recorded result and run the fast unit suite
live.

## 3. Fast Commands

From the repository root:

```text
python testing/test_suite.py
python play_ludo.py --engine oop --mode quick --seed 42 --no-color
python play_ludo.py --engine functional --mode quick --seed 42 --no-color
python v1_initial/ludo_oop.py --wizard
python v1_initial/ludo_func.py --config configs/showcase.json
python v1_initial/ludo_oop.py --mode quick --players 4 --seat bot --seat bot --seat bot --seat bot --autoplay --speed fast --no-color
python v1_initial/ludo_func.py --mode quick --seed 42 --ui gui
```

The full verification command is:

```text
python scripts/verify_gates.py --stage v1
```

Do not claim `--stage final` passes. Final-stage completion depends on real peer
reports and genuine peer-driven v2 fixes, which are not present yet.

## 4. Five-Minute Demonstration Plan

### Minute 1: Architecture

Show the two launchers and explain that they only import modular `main()`
functions. Then show one OOP class and one functional state dictionary.

### Minute 2: Setup and rules

Launch:

```text
python play_ludo.py --engine oop --mode quick --seed 42 --no-color
```

Explain Quick's 28-tile route and 9×9 board, Showcase defaults, and the fact
that a token leaves base only on 6.

### Minute 3: A turn and a bot

If using a bot seat, show its `BOT_DECISION` reason. Explain the priority order:
home, capture, unlock, safety, escape, progress, lowest token index.

### Minute 4: GUI or autoplay

Open the GUI and show Roll, token buttons, Pause, Step, Speed, Commentary, Draw,
and Quit. If no display is available, use the four-bot autoplay command instead
and explain that headless GUI controller tests cover the same turn transitions.

### Minute 5: Proof

Run:

```text
python testing/test_suite.py
```

Then show the recorded 1,080-game matrix metrics in `TRACKER.md`. Mention that
canonical snapshots are compared after every roll, bot decision, and move.

## 5. Rule Explanations You Must Be Able to Give

### Board geometry

- Quick: 28 outer tiles, home length 4, two default tokens, 9×9 cross.
- Classic: 52 outer tiles, home length 5, four default tokens, 15×15 cross.
- Geometry comes from the preset and is validated as immutable.
- A token uses personal `steps`: `-1` means base, `0..track_len-2` is the outer
  route, the home lane follows, and `home_finish` means finished.

### Kill-to-Enter Option A

A player with `captures_made == 0` cannot enter the private home stretch. A
token that would cross the home gate keeps looping around the outer route.
The first capture unlocks home entry for every token owned by that player.

Why Option A? It preserves active competition. Gate Hold was rejected because
tokens could simply wait at the gate and encourage passive stalemates.

### Blockades

- `none`: opponents pass and can capture a stack.
- `strict`: two same-color enemy tokens block both passing and landing. Every
  intermediate tile is checked.
- `safe_pair`: opponents may pass a pair, but a single token cannot capture it.

### Safe tiles

A safe tile prevents capture. Friendly tokens are never captured. Disabling
safe tiles also removes starting-tile immunity. Passing over a token never
captures it; landing is required.

### Extra rolls

A six, capture bonus, or home bonus grants one extra roll. Multiple reasons do
not stack. An extra roll does not increase `turn_count`.

### Triple six

The first two sixes and moves remain. The third consecutive six is forfeited
when the rule is enabled. A non-six resets the streak. Reaching home also resets
it.

### Exact home

With exact-home enabled, overshooting `home_finish` is illegal. With it
disabled, an otherwise legal overshoot clamps the token to home.

### Podium Mode

With two players, first finisher wins. In 3P/4P podium play, finished seats are
skipped until only one unfinished player remains. The first finisher is still
the winner; `finish_order` records the podium.

### Draw and quit

- Turn cap produces an automatic draw.
- Mutual draw requires every other player to accept.
- A declined draw resumes without advancing the turn.
- Quit requires confirmation in the CLI/GUI and exits cleanly.
- EOF and Ctrl+C also terminate without a traceback.

## 6. Bot Priority Order

The bot scores legal moves lexicographically:

1. Finish Home.
2. Number of captures.
3. Unlock Kill-to-Enter.
4. Land safely.
5. Escape danger.
6. Advance furthest.
7. Lowest token index on an exact tie.

The OOP implementation is `BotPolicy` in
`v1_initial/oop_ludo/bot.py:11`. The functional implementation is
`decision_details()` in `v1_initial/func_ludo/bot.py:73`.

A bot does not use a second random number stream. Seeded dice plus deterministic
token choice make a bot match repeatable.

## 7. Likely Viva Questions and Strong Answers

### Why two implementations?

To demonstrate the same requirements in two programming paradigms and prove
that their observable behavior is identical rather than merely similar.

### How many classes are in the functional version?

Zero across `ludo_func.py`, `func_ludo/`, and `shared/`. The verifier scans
recursively using Python AST.

### Why does the OOP launcher contain no class?

Because it is a thin entry point. The required OOP classes live in
`oop_ludo/`; class audit checks the package, not only the 17-line launcher.

### Is shared code cheating?

No. Shared modules contain presets, validation, seating, event contracts,
geometry, and presentation. They contain no classes and no Ludo rule engine.
Both implementations independently calculate moves, captures, turns, and
results.

### How do you prove parity?

For each of 1,080 games, both engines start from equivalent configuration and
seed. Tests compare canonical snapshots initially and after every roll, bot
decision, move, and terminal transition. Real subprocess tests also compare CLI
transcripts after masking only intentional code-trace wording.

### Why exclude the RNG from canonical state?

The random-number generator is an internal mechanism, not an observable game
fact. The exported state contains configuration, seats, tokens, turn counters,
status, results, and events, all JSON-serializable.

### Does a six always grant another roll?

Only when a legal move is made. No legal move skips. Three consecutive sixes
forfeit the third roll when enabled. Capture/home bonuses also grant one roll,
but reasons never stack.

### Who advances the turn after a move?

`apply_move()` owns that decision. It advances, grants a bonus, records a finish,
or ends the match. The caller must not call `advance_turn()` again.

### What happens when a player finishes in podium mode?

They stop taking turns. Play continues among unfinished players until the
podium condition is met.

### What does `--seed` guarantee?

It guarantees the dice sequence. Human decisions must also be repeated for an
identical transcript. Bot choices are deterministic for the same state.

### How does configuration precedence work?

Explicit CLI values override JSON; JSON overrides wizard answers; wizard
answers override defaults. Locked geometry cannot be overridden.

### Why not put all rules in one shared engine?

That would turn the functional version into a wrapper around common logic and
undermine the paradigm comparison. Independent engines plus canonical tests
provide a stronger correctness check.

### How does the GUI avoid changing game rules?

It calls a headless `GuiSession` controller. Tkinter only draws widgets and uses
`after()` to schedule automated actions. Pause stops scheduling; Step still
performs one action.

### Can autoplay drive human seats?

Yes. It preserves human/bot metadata but lets automation make the input and
move decisions, which is useful for demonstrations and repeatable tests.

### Why do code commentary lines differ?

They are intentionally paradigm-specific: for example, an OOP method call and a
functional state function call. Gameplay commentary and canonical states remain
identical. The parity normalizer masks only those code traces.

### What is in v2?

Nothing has been populated because no real peer feedback exists. `v1_initial/`
is the current full-feature handoff. Peer-driven fixes belong in `v2_final/`
with a changelog.

### Was the web app built?

No. The approved deliverable is the executable plan in
`docs/06_v3_web_build_plan.md`. It defines a pure TypeScript rules core, React
controller, Three.js presentation, Python fixtures, and acceptance gates.

## 8. How to Explain a Change Safely

If asked to add a rule, do not say “change one file.” Explain the full path:

1. Add or update validated configuration in `shared/contracts.py`.
2. Implement the behavior independently in `LudoGame` and `rules.py`.
3. Update bot scoring in both `BotPolicy` and `bot.py` if the new consequence
   affects choice priority.
4. Update move descriptions, commentary, or GUI labels only when presentation
   changes.
5. Add focused tests for both engines and edge cases.
6. Add a scenario to the parity matrix or subprocess coverage.
7. Run the complete verifier and record real evidence.

This demonstrates design understanding, not just syntax knowledge.

## 9. Common Defensive Mistakes

- Calling the functional version “procedural classes” or claiming it has hidden
  class wrappers.
- Saying both implementations import one common rule engine.
- Claiming a seed fixes human token choices.
- Saying bonus reasons stack.
- Saying a blockade only blocks landing; strict mode also blocks crossing.
- Saying safe-pair mode cannot be passed.
- Saying a gate-hold token waits outside home; Option A loops.
- Calling `apply_move()` and then advancing again.
- Reporting old 28-test or old 1,000-game numbers as current evidence.
- Claiming peer reports or v2 improvements that do not exist.
- Claiming the Tkinter GUI was visually demonstrated if only its headless
  controller and drawing tests were run.

## 10. Evidence Checklist

Before submission, be able to point to:

- `AGENTS.md`: project constraints.
- `docs/01_game_design_document.md`: complete rule specification.
- `docs/02_flowchart_pseudocode.md`: algorithm walkthrough.
- `docs/03_comparison_report.md`: seven evidence-based comparison answers.
- `docs/04_ai_interaction_log.md`: real prompts, decisions, and debugging.
- `testing/TEST_MATRIX_AND_GATES.md`: test coverage and gate matrix.
- `TRACKER.md`: observed command results and metrics.
- `docs/06_v3_web_build_plan.md`: future web implementation plan.
- `configs/showcase.json` and `configs/classic.json`: runnable presets.
- Clean peer-report templates: no fabricated test outcomes.

## 11. Closing Statement

> Our strongest result is not that two files exist. It is that both designs
> implement a complex, configurable game while remaining structurally honest,
> and that automated evidence checks their behavior at hundreds of thousands
> of state boundaries. We can explain where data lives, who owns each decision,
> how the paradigms differ, and how to extend either one without breaking
> parity.
