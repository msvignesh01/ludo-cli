# Changelog — `v1_initial` to `v2_final`

All changes below were driven by peer testing feedback from **Peer Team 1** and **Peer Team 2**, applied symmetrically to **both** `v2_final/ludo_oop.py` and `v2_final/ludo_func.py`, and verified with regression tests and the 1,000-game parity suite.

---

## Summary of Changes

| ID | Source | Type | Issue / Suggestion | Fix Applied (Both OOP & Functional) | Regression Test |
|---|---|---|---|---|---|
| CHG-01 | Peer Team 1 | Bug / UX | *(Fill from Team 1 report)* | *(Exact change in both files)* | `test_...` |
| CHG-02 | Peer Team 1 | UX | *(Fill from Team 1 report)* | *(Exact change in both files)* | `test_...` |
| CHG-03 | Peer Team 2 | Bug / UX | *(Fill from Team 2 report)* | *(Exact change in both files)* | `test_...` |
| CHG-04 | Peer Team 2 | UX | *(Fill from Team 2 report)* | *(Exact change in both files)* | `test_...` |

---

## Parity & Quality Verification After `v2_final` Changes
- **AST Zero-Class Gate (`v2_final/ludo_func.py`):** PASS (0 classes)
- **Unit & Regression Tests (`testing/test_suite.py`):** PASS (`X / X` tests)
- **1,000-Game Seeded Parity Fuzz (`testing/parity_test.py`):** PASS (`1,000 / 1,000` identical)
- **Subprocess CLI Transcript Diff:** PASS (0-line diff under `--no-color`)
