# PLAN.md — Phase-by-Phase Execution Roadmap (CIA1 Ludo)

**Target:** 100 / 100 Rubric Score
**Game:** Multiplayer Ludo CLI (Quick 28-tile/2-token + Classic 52-tile/4-token Toggle)
**UI:** Polished ANSI-Colored CLI (Windows/macOS/Linux, zero external dependencies)
**Implementations:** `ludo_oop.py` (Class-Based) + `ludo_func.py` (Strictly Zero-Class Function-Based)

---

## Rubric Alignment Map (100 Marks)

| Rubric Component | Marks | Owning Phases | Key Submission Artifacts |
|---|---:|---|---|
| Game design and logic | 10 | Phase 1 | `docs/01_game_design_document.md`, `docs/02_flowchart_pseudocode.md` |
| Class-based implementation | 15 | Phase 2, Phase 5 | `v1_initial/ludo_oop.py`, `v2_final/ludo_oop.py` |
| Function-based implementation | 15 | Phase 2, Phase 5 | `v1_initial/ludo_func.py`, `v2_final/ludo_func.py` |
| Understanding of AI-generated code | 15 | Phase 2, Phase 3, Phase 6 | Clean docstrings, `docs/04_ai_interaction_log.md`, Viva prep |
| Comparison of both approaches | 15 | Phase 6 | `docs/03_comparison_report.md` (with real code citations) |
| Testing and bug fixing | 15 | Phase 3, Phase 4, Phase 5 | `testing/test_suite.py`, `testing/parity_test.py`, Peer reports |
| Peer feedback and improvements | 5 | Phase 4, Phase 5 | `testing/team1_report.md`, `testing/team2_report.md`, `v2_final/CHANGELOG.md` |
| Demonstration and presentation | 10 | Phase 6 | Live CLI demo (`v2_final/`), `docs/05_viva_prep.md` |
| **Total** | **100** | **All Phases** | **All 8 required deliverables verified** |

---

## Target Repository Structure (Created in Phase 0)

```text
ludo-cia1/
├── AGENTS.md
├── PLAN.md
├── TRACKER.md
├── docs/
│   ├── 01_game_design_document.md
│   ├── 02_flowchart_pseudocode.md
│   ├── 03_comparison_report.md
│   ├── 04_ai_interaction_log.md
│   └── 05_viva_prep.md
├── v1_initial/
│   ├── ludo_oop.py
│   └── ludo_func.py
├── testing/
│   ├── test_suite.py               # Exhaustive unit & edge-case tests for BOTH engines
│   ├── parity_test.py              # 1,000-game seeded fuzz parity + subprocess CLI diff
│   ├── peer_test_kit.md            # Handout guide for Peer Teams 1 & 2
│   ├── team1_report.md             # Peer Team 1 completed report (human phase)
│   └── team2_report.md             # Peer Team 2 completed report (human phase)
├── v2_final/
│   ├── ludo_oop.py                 # Post-peer-feedback improved OOP version
│   ├── ludo_func.py                # Post-peer-feedback improved Functional version
│   └── CHANGELOG.md                # Exact delta map: Peer Feedback -> Fix in both files
└── scripts/
    └── verify_gates.py             # Master static, AST, structure & test runner
```

---

## Phase 0: Workspace Initialization & Spec Alignment
**Goal:** Establish directory structure, verify Python 3.11+, and lock all specification contracts before coding.

### Tasks
1. Verify `python --version` is 3.11+ and UTF-8/ANSI environment behavior.
2. Create directories: `docs/`, `v1_initial/`, `testing/`, `v2_final/`, `scripts/`.
3. Copy/finalize `specs/01_game_design_document.md` -> `docs/01_game_design_document.md` and `specs/02_flowchart_pseudocode.md` -> `docs/02_flowchart_pseudocode.md`.
4. Copy `testing/peer_test_kit.md` and initialize `testing/team1_report.md` and `testing/team2_report.md` from `testing/team_report_template.md`.
5. Initialize `docs/04_ai_interaction_log.md` from `templates/ai_interaction_log_template.md`.

### Exit Gate 0
- All directories and baseline doc files exist.
- `TRACKER.md` Phase 0 items checked off.

---

## Phase 1: Finalize Design Artifacts (Submission #1 & #2)
**Goal:** Lock every mathematical invariant, rule edge case, CLI layout, and canonical state schema so both implementations derive from a single source of truth.

### Tasks
1. Review `specs/01_game_design_document.md`, `specs/02_flowchart_pseudocode.md`, `specs/03_oop_architecture_spec.md`, `specs/04_functional_architecture_spec.md`, and `specs/05_cli_ui_and_ansi_spec.md`.
2. Confirm exact formulas for both presets:
   - **Quick Mode:** `track_len=28`, `home_len=4`, `tokens=2`, `home_finish=31`, `safe_tiles={0, 7, 14, 21}`, `starts_4p=[0, 7, 14, 21]`, `starts_2p=[0, 14]`, `default_max_turns=100`.
   - **Classic Mode:** `track_len=52`, `home_len=5`, `tokens=4`, `home_finish=56`, `safe_tiles={0, 8, 13, 21, 26, 34, 39, 47}`, `starts_4p=[0, 13, 26, 39]`, `starts_2p=[0, 26]`, `default_max_turns=250`.
3. Verify canonical state snapshot contract (`export_canonical_state`) is 100% identical across OOP and Functional specs.

### Exit Gate 1
- `docs/01_game_design_document.md` and `docs/02_flowchart_pseudocode.md` are complete, self-contained, and free of placeholders.

---

## Phase 2: Build `v1_initial` Dual Implementations (Submission #3 & #4)
**Goal:** Build both `v1_initial/ludo_oop.py` and `v1_initial/ludo_func.py` to spec with polished ANSI CLI, Quick/Classic mode toggle, complete edge-case handling, and clean testable hooks.

### Tasks
1. **Build `v1_initial/ludo_oop.py`:**
   - Implement `Token`, `Player`, `Board`, `CLIRenderer`, and `LudoGame` per `specs/03_oop_architecture_spec.md`.
   - Support CLI flags: `--mode`, `--seed`, `--max-turns`, `--no-color`.
   - Implement `LudoGame.export_canonical_state()` returning a pure JSON-serializable `dict` for parity testing.
   - Implement clean separation between headless step logic (`roll_die`, `get_valid_moves`, `apply_move`, `handle_roll`, `advance_turn`) and interactive I/O (`run_cli`).
2. **Build `v1_initial/ludo_func.py`:**
   - Implement strictly zero-class architecture per `specs/04_functional_architecture_spec.md`.
   - Store all game state in a single `state: dict` passed explicitly to modular functions (`create_game_state`, `get_global_pos`, `get_valid_moves`, `apply_move`, `handle_roll`, `advance_turn`, `render_board`, `run_cli`).
   - Implement `export_canonical_state(state)` returning the exact same schema as `ludo_oop.py`.
   - Support identical CLI flags, prompts, ANSI styling, move annotations, and error messages.
3. **Log AI Build Iterations:**
   - Record architecture prompts, verification findings, and any subtle bugs caught between the two versions in `docs/04_ai_interaction_log.md`.

### Exit Gate 2
- Both files run cleanly via `python v1_initial/ludo_oop.py --help` and `python v1_initial/ludo_func.py --help`.
- AST audit confirms **0 classes** in `ludo_func.py` and **5 classes** in `ludo_oop.py`.
- Zero third-party imports in either file.

---

## Phase 3: Exhaustive Automated Testing & Perfection Loop
**Goal:** Prove mathematically and empirically that both `v1_initial` implementations are bug-free, crash-proof, and 100% identical in behavior before handing them to peer teams.

### Tasks
1. **Build `testing/test_suite.py`** (`unittest` standard library) covering every test case in `testing/TEST_MATRIX_AND_GATES.md`:
   - Preset configuration math (Quick & Classic).
   - 2P diagonal seating vs 3P/4P clockwise seating.
   - Base unlock rule (rolls 1–5 blocked, roll 6 unlocks to `steps=0`).
   - Circular outer track wrap-around (e.g., player at start index 14 or 21 wrapping past 27 -> 0 without skipping or duplicating tiles).
   - Private home stretch entry and immunity from capture.
   - Exact roll to Home (`steps + roll == home_finish` wins token; `steps + roll > home_finish` rejected).
   - Capture on non-safe tile (single enemy token AND stacked multiple enemy tokens sent back to Base `-1`).
   - Safe tile immunity (opponents coexist safely on `★` tiles; no capture, no bonus roll).
   - Same-color stacking (no blockades; opponent can pass over and capture on non-safe tiles).
   - Bonus roll rules (roll 6, capture, reach Home; verify non-stacking when 6 + capture occur together).
   - Triple consecutive 6s forfeit (3rd 6 voids move, resets streak, advances turn).
   - Auto-skip when zero valid moves exist (e.g., all tokens in Base and roll != 6, or all remaining tokens need smaller exact roll).
   - Win condition (all tokens at `home_finish` terminates immediately).
   - Draw conditions: `max_turns` reached AND mutual `draw` command (both accepted and rejected by another player).
   - CLI input resilience: empty lines, spaces, letters, floats, negative integers, out-of-range integers, `quit` confirmed/cancelled, `EOFError`, `KeyboardInterrupt`.
   - `--no-color` produces zero `[` ANSI escape sequences.
2. **Build `testing/parity_test.py`:**
   - **Fuzz Parity Engine:** Run **1,000+ simulated games** across `(quick, classic) x (2P, 3P, 4P)` using deterministic seeds and synchronized move choices. Assert `oop.export_canonical_state() == func_export_canonical_state(state)` after **every single roll and move**.
   - **Subprocess CLI Parity Test:** Run both scripts as real OS subprocesses with identical scripted stdin transcripts (covering setup, invalid inputs, captures, bonus rolls, max-turn draw, mutual draw, and full game win) under `--no-color --seed <N>`. Assert exit code `0` and **100% identical normalized stdout**.
3. **Run Master Gate Script:**
   - Execute `python scripts/verify_gates.py --stage v1`.
   - Fix any discrepancy immediately and re-run until 100% green.

### Exit Gate 3 (Perfection Gate for v1)
- `verify_gates.py --stage v1` passes with **0 failures, 0 errors, 0 warnings**.
- 1,000/1,000 parity fuzz games match on every turn.
- Subprocess CLI transcripts match 100%.

---

## Phase 4: Peer Testing Execution (Human Team Handoff — Submission #7)
**Goal:** Have TWO other teams test `v1_initial/ludo_oop.py` and `v1_initial/ludo_func.py` thoroughly and document real feedback.

### Tasks (Human Team + Agent Prep)
1. Hand `v1_initial/ludo_oop.py`, `v1_initial/ludo_func.py`, and `testing/peer_test_kit.md` to **Peer Team 1** and **Peer Team 2**.
2. Each peer team executes all 10 scenarios in `peer_test_kit.md` (Quick mode, Classic mode, invalid inputs, capture, safe zone, exact home, triple-6, draw conditions, quit, UX review).
3. Collect completed reports into `testing/team1_report.md` and `testing/team2_report.md`.
4. **Agent Action on Return:** Parse both peer reports, classify every item (`Bug`, `Edge Case`, `UX Improvement`), and build a prioritized `v2` fix plan.

### Exit Gate 4
- Two distinct, genuine peer testing reports saved in `testing/team1_report.md` and `testing/team2_report.md`.

---

## Phase 5: Build `v2_final` Improvements & Re-Verify (Submission #8)
**Goal:** Incorporate every valid bug fix and UX enhancement from Peer Teams 1 & 2 into **both** `v2_final/ludo_oop.py` and `v2_final/ludo_func.py` while maintaining 100% parity.

### Tasks
1. Copy `v1_initial/*` into `v2_final/` (keeping `v1_initial/` strictly untouched).
2. Implement every accepted fix/improvement symmetrically in both `v2_final/ludo_oop.py` and `v2_final/ludo_func.py` (examples of common peer suggestions to anticipate cleanly: in-game `help`/`rules` command, compact ASCII die art, turn summary/capture scoreboard, auto-confirm single valid move option, colorblind token brackets, clearer error hints).
3. Add new regression test cases to `testing/test_suite.py` for every bug or feature reported by peers.
4. Populate `v2_final/CHANGELOG.md` mapping every Peer Team 1 & Team 2 item -> exact fix in both files -> test proof.
5. Run `python scripts/verify_gates.py --stage v2` until 100% green.

### Exit Gate 5 (Perfection Gate for v2)
- `verify_gates.py --stage v2` passes with **0 failures, 0 errors, 0 warnings**.
- All peer-reported bugs have dedicated passing regression tests.
- `v1_initial/` remains intact and passes `verify_gates.py --stage v1`.

---

## Phase 6: Deep Comparison Report, AI Log & Viva Polish (Submission #5, #6 & Demo)
**Goal:** Produce an executive-grade Comparison Report backed by real code snippets from `v2_final/`, finalize the AI Interaction Log, and prepare the team for a 10/10 live demo and viva.

### Tasks
1. Write `docs/03_comparison_report.md` following `templates/comparison_report_guide.md`:
   - Answer all **7 required rubric questions** thoroughly.
   - Cite **actual functions, classes, line numbers, and side-by-side code snippets** directly from `v2_final/ludo_oop.py` and `v2_final/ludo_func.py`.
   - Include concrete metrics (line counts, function/method counts, state representation diff, effort required to apply peer feedback to OOP vs Functional).
2. Finalize `docs/04_ai_interaction_log.md` with curated real prompts, generated code snippets, actual bugs caught by `parity_test.py` or peer testers, and concrete debugging fixes.
3. Finalize `docs/05_viva_prep.md` using `templates/viva_prep_and_capstone_qa.md`, tailored to the exact final code in `v2_final/`.
4. Run final submission completeness audit: `python scripts/verify_gates.py --stage final`.

### Exit Gate 6 (Submission Perfection Gate)
- All 8 required submission artifacts exist, are non-empty, and contain zero `TODO` / `TBD` placeholders.
- Both `v1_initial` and `v2_final` pass all automated tests and parity checks.
- Live demo dry-run completes cleanly in under 5 minutes (Quick Mode + Classic Mode toggle showcase + `--max-turns` draw demo).
