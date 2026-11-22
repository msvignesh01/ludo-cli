# AI Interaction Log (`docs/04_ai_interaction_log.md`)

> **Submission Requirement #6:** Document real prompts, AI-generated outputs/architecture decisions, and concrete debugging examples showing human verification and iterative improvement.

---

## Session 1: Architecture & Scope Design
- **Objective:** Select Ludo, define Quick vs. Classic presets, resolve draw conditions required by rubric, and lock unified `steps` coordinate math.
- **Prompt Used:**
  > *(Paste actual prompt)*
- **Key AI Output / Decision:**
  - Chose unified `steps` integer (`-1`, `0..track_len-2`, `track_len-1..home_finish-1`, `home_finish`) instead of raw global coordinates to eliminate off-by-one home-entry bugs.
  - Added dual mode toggle (`quick` 28-tile/2-token + `classic` 52-tile/4-token) and explicit draw conditions (`--max-turns` + mutual `draw`).
- **Human Review / Modification:**
  - Confirmed polished ANSI CLI (zero dependencies) over GUI to maximize code clarity for viva defense and eliminate peer-testing install friction.

---

## Session 2: Building `v1_initial/ludo_oop.py` & `v1_initial/ludo_func.py`
- **Prompt Used:**
  > *(Paste actual prompt)*
- **Key Constraints Verified:**
  - Verified zero `class` keywords in `ludo_func.py` via automated AST scan.
  - Verified isolated `random.Random(seed)` instance in both engines for reproducible parity testing.
- **Code Snippet Highlight (OOP vs Functional Parity):**
  ```python
  # Paste short side-by-side snippet of a core rule (e.g. capture or exact home check)
  ```

---

## Session 3: Automated Testing & Real Debugging Example(s)
*(Log at least 2 real bugs, edge cases, or parity mismatches caught during development or peer testing!)*

### Debugging Trace #1: [Short Bug Title — e.g., Triple-6 Streak Reset / Windows Encoding / Parity Mismatch]
- **Symptom / Failing Test:** *(Exact test name or CLI output)*
- **Root Cause Identified by Human/Agent:** *(Exact line & logic flaw)*
- **Fix Applied (Before -> After):**
  ```python
  # Before:
  ...
  # After:
  ...
  ```
- **Verification:** *(Command run + pass proof)*

### Debugging Trace #2: [Short Bug Title — e.g., Peer Feedback Fix in v2_final]
- **Reported By:** Peer Team [1 / 2]
- **Root Cause:** ...
- **Fix Applied to BOTH `v2_final/ludo_oop.py` and `v2_final/ludo_func.py`:** ...
- **Regression Test Added:** `test_...` in `testing/test_suite.py`

---

## Key Takeaway from AI-Assisted Development
- *(Summarize in 3–5 bullet points how AI accelerated boilerplate generation while human architectural oversight, parity testing, and edge-case verification ensured correctness.)*
