# Ludo CIA1 — Complete AI Agent Build & Verification Blueprint

This package contains the complete, phase-by-phase engineering specification, agent governance rules, verification gates, testing kits, and submission templates to build a **100/100 CIA1 Python Programming Assignment**: a dual-paradigm multiplayer **Ludo CLI** (Object-Oriented vs. strictly zero-class Function-Based) featuring a **Quick / Classic mode toggle** and a **polished ANSI-colored terminal interface**.

For player setup, controls, and game rules, see the [User Manual](docs/USER_MANUAL.md).

## Play the Game

With Python 3.11+ installed, run `python play_ludo.py` from this folder. The
launcher lets you choose the OOP or function-based version, then the game asks
for the mode, player count, and names. Game options such as `--mode quick`,
`--seed 42`, and `--no-color` can be passed through the launcher. Colors are on
by default in ANSI-compatible terminals; add `--no-color` to turn them off.

## How to Run with Any AI Coding Agent (Claude Code, Codex, Cursor, Antigravity)

1. Unzip this folder into your working repository directory (`ludo-cia1/`).
2. Point your AI coding agent to read these three control files **in order** before writing any code:
   - `AGENTS.md` — Non-negotiable engineering rules, constraints, and perfection stop-conditions.
   - `PLAN.md` — Master Phase 0 to Phase 6 build, test, and submission roadmap.
   - `TRACKER.md` — Live execution ledger (the agent must check off tasks and log command evidence as it progresses).
3. Kick off the agent with a single prompt:
   > "Read `AGENTS.md`, `PLAN.md`, `TRACKER.md`, and all files under `specs/` and `testing/`. Execute Phase 0 through Phase 3 autonomously. Do not stop until every automated test, AST audit, 1,000-game parity fuzz suite, and subprocess CLI parity check passes with zero errors."

## Package Contents

```text
ludo-cia1-agent-plan/
├── README.md                              # Start here
├── AGENTS.md                              # Agent operating contract & perfection gates
├── PLAN.md                                # Master phase-by-phase execution plan (Phases 0–6)
├── TRACKER.md                             # Granular execution & rubric verification checklist
├── specs/
│   ├── 01_game_design_document.md         # Complete GDD: Quick & Classic modes, math, rules, CLI flags
│   ├── 02_flowchart_pseudocode.md         # Mermaid flowchart & language-agnostic pseudocode
│   ├── 03_oop_architecture_spec.md        # Class-Based (OOP) engine & CLI contract
│   ├── 04_functional_architecture_spec.md # Zero-Class Function-Based engine & CLI contract
│   └── 05_cli_ui_and_ansi_spec.md         # ANSI color system, Windows compatibility, board rendering
├── testing/
│   ├── TEST_MATRIX_AND_GATES.md           # Exhaustive unit, edge-case, fuzz & CLI parity test specs
│   ├── peer_test_kit.md                   # Structured testing guide for the 2 peer testing teams
│   └── team_report_template.md            # Fillable testing report template for Peer Teams 1 & 2
├── templates/
│   ├── comparison_report_guide.md         # 7-question OOP vs Functional comparison blueprint
│   ├── ai_interaction_log_template.md     # Structured log for prompts, diffs, and debugging traces
│   ├── viva_prep_and_capstone_qa.md       # Viva defense playbook, team split & capstone answer
│   └── changelog_template.md              # v1 -> v2 improvement ledger mapped to peer feedback
└── scripts/
    └── verify_gates.py                    # Automated AST, stdlib, structure & parity gate verifier
```

## Target Python Environment

- **Runtime:** Python 3.11+ (Windows, macOS, Linux compatible)
- **Dependencies:** **Python Standard Library ONLY** (zero `pip install` requirements)
