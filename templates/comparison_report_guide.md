# Comparison Report Guide

Use this guide for `docs/03_comparison_report.md`. Base every claim on the
actual stage being submitted. The current completed implementation is the
modular `v1_initial/`; `v2_final/` must be used only after genuine peer feedback
produces real changes.

## Required Evidence

Measure rather than estimate:

- Python files and lines in each paradigm package.
- AST class count and function/method count.
- Classes and functions in shared modules.
- Launcher size.
- Latest observed unit, parity, subprocess, and verifier results.

Label package metrics separately from thin launcher metrics. Do not claim the
launcher contains the OOP classes when they live in `oop_ludo/`.

## Seven Required Questions

### 1. How is data stored?

Compare real `Token`, `Player`, `Board`, and `LudoGame` attributes with the
functional `state["players"][i]["tokens"][j]["steps"]` structure. Include a
short initialization snippet from both implementations.

### 2. How is game logic organized?

Compare object-owned methods such as `token.can_move()`,
`board.get_global_pos()`, and `game.apply_move()` with explicit function
pipelines such as `get_valid_moves(state, ...)` and `apply_move(state, ...)`.
Explain which helpers are read-only and which mutate state.

### 3. How are turns managed?

Show real roll, bonus, advance, finish, and draw behavior. State clearly that
`apply_move()` owns post-move turn resolution. Compare turn counters, six
streaks, finished-seat skipping, and podium termination.

### 4. Which version is easier to understand?

Give a nuanced answer. Functional data flow is explicit and linear; OOP domain
methods become easier to navigate as the model grows. Ground the answer in real
expressions from the code.

### 5. Which version is easier to debug?

Compare direct dictionary inspection with object navigation. Explain how both
use canonical JSON-serializable exports and ordered events. Include at least one
real failure and its root cause.

### 6. Which version is easier to modify and extend?

Use a real implemented extension such as blockades, Kill-to-Enter, Podium
Mode, bots, or GUI control. If peer-driven v2 evidence exists, map the actual
report to both code changes and regression proof. Never invent a peer cycle.

### 7. Advantages and limitations

Compare encapsulation, boilerplate, state inspection, serialization,
extensibility, silent key typos, testing, and ideal use cases.

## Capstone

Answer why understanding design still matters when AI can generate both
versions. Refer to invariants, canonical contracts, test evidence, and the
ability to explain and safely change code.

## Accuracy Rules

- Do not use stale test counts or hypothetical metrics.
- Do not present shared contracts as a shared rules engine.
- Do not claim a working v3 web application.
- Do not claim human visual GUI testing unless it actually occurred.
- Do not fabricate peer reports or v2 fixes.
