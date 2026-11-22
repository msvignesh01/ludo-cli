# AI Interaction Log (`docs/04_ai_interaction_log.md`)

> **Submission Requirement #6:** Document real prompts, AI-generated outputs/architecture decisions, and concrete debugging examples showing human verification and iterative improvement.

---

## Session 1: Architecture & Scope Design
- **Objective:** Select Ludo, define Quick vs. Classic presets, resolve draw conditions required by rubric, and lock unified `steps` coordinate math.
- **Prompt Used:**
  > "Read AGENTS.md, PLAN.md, TRACKER.md, scripts/verify_gates.py, and everything in specs/ and testing/. Execute Phases 0 through 3 autonomously."
- **Key AI Output / Decision:**
  - Chose unified `steps` integer (`-1`, `0..track_len-2`, `track_len-1..home_finish-1`, `home_finish`) instead of raw global coordinates to eliminate off-by-one home-entry bugs.
  - Added dual mode toggle (`quick` 28-tile/2-token + `classic` 52-tile/4-token) and explicit draw conditions (`--max-turns` + mutual `draw`).
- **Human Review / Modification:**
  - Confirmed polished ANSI CLI (zero dependencies) over GUI to maximize code clarity for viva defense and eliminate peer-testing install friction.

---

## Session 2: Building `v1_initial/ludo_oop.py` & `v1_initial/ludo_func.py`
- **Prompt Used:**
  > "Implement the OOP and zero-class functional engines with the exact unified steps model, preset constants, canonical state, CLI parity, and test hooks."
- **Key Constraints Verified:**
  - Verified zero `class` keywords in `ludo_func.py` via automated AST scan.
  - Verified isolated `random.Random(seed)` instance in both engines for reproducible parity testing.
- **Code Snippet Highlight (OOP vs Functional Parity):**
  ```python
  # OOP:
  won = player.all_finished(self.board.home_finish)
  bonus_turn = not won and (roll == 6 or bool(captured) or reached_home)

  # Functional:
  won = all_tokens_finished(player, home_finish)
  bonus_turn = not won and (roll == 6 or bool(captured) or reached_home)
  ```

---

## Session 3: Automated Testing & Real Debugging Example(s)
*(Log at least 2 real bugs, edge cases, or parity mismatches caught during development or peer testing!)*

### Debugging Trace #1: Functional canonical mode
- **Symptom / Failing Test:** Initial canonical snapshots differed between engines until the functional preset gained an explicit mode field.
- **Root Cause Identified:** `create_game_state()` copied the preset but did not add `config["mode"]`; canonical export therefore had to infer mode from track length.
- **Fix Applied:** The functional initialization now adds `config["mode"] = mode`, matching the OOP board mode directly.
- **Verification:** `test_25_canonical_states_match_initially` passed and 1,000-game canonical snapshots matched after every action.

### Debugging Trace #2: Unit capture fixture positions
- **Symptom / Failing Test:** The single-capture and safe-tile tests used steps that did not resolve to the intended shared global tile.
- **Root Cause:** The tests ignored player-specific start indices when constructing enemy positions.
- **Fix Applied:** Fixtures now use `(start_index + steps) % track_len` coordinates, so the mover and enemy genuinely collide or remain safe.
- **Verification:** `test_10_single_capture` and `test_12_safe_tile_no_capture` passed in `python testing/test_suite.py`.

---

## Key Takeaway from AI-Assisted Development
- AI accelerated generation of matching engine scaffolds, CLI rendering, and test adapters.
- Human/agent verification enforced preset-derived coordinate math and zero third-party imports.
- The canonical snapshot contract and 1,000-game fuzzer exposed and prevented state divergence.
- The final v1 result is a 28-test unit suite plus 1,000 deterministic fuzz games and identical subprocess transcripts.
