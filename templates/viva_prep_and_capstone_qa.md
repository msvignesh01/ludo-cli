# Viva Defense Playbook & Demo Script (`docs/05_viva_prep.md`)

**Rubric Stakes:** Understanding of AI-generated code (15 marks) + Demonstration & presentation (10 marks) = **25 Marks**.

---

## 1. Team Ownership Split (Zero Single Points of Failure)
**Rule:** Every team member MUST understand BOTH `ludo_oop.py` and `ludo_func.py` end-to-end. Split by **presentation lead role**, not by hiding code from each other:

| Role | 2-Student Team | 3-Student Team |
|---|---|---|
| **Lead 1: Design & OOP Walkthrough** | GDD, coordinate math, `ludo_oop.py` classes, live Quick Mode demo | GDD, flowchart, `ludo_oop.py` architecture walkthrough |
| **Lead 2: Functional & Parity Proof** | `ludo_func.py` zero-class design, `parity_test.py`, Comparison Report & Capstone Q | `ludo_func.py` state dict walkthrough + Comparison Report |
| **Lead 3: Testing, Peer Feedback & Demo** | *(Shared)* | Live CLI demo (Quick + Classic toggle + Draw), Peer Testing Reports, `v1 -> v2` Changelog & Capstone Q |

---

## 2. 5-Minute Live Demo Runbook (Zero Surprises)

Run commands in this exact sequence during evaluation:

1. **Show Automated Verification First (30 sec):**
   `python scripts/verify_gates.py --stage v2`
   *(Proves AST zero-class rule, stdlib-only imports, unit tests, and 1,000-game parity live in front of faculty!)*
2. **Play 3–4 Turns in Quick Mode OOP (90 sec):**
   `python v2_final/ludo_oop.py --mode quick --seed 42`
   *(Show colored board, safe tiles `★`, invalid input rejection, unlock on 6, capture/move previews.)*
3. **Prove Determinism in Function-Based Version (60 sec):**
   `python v2_final/ludo_func.py --mode quick --seed 42`
   *(Take the same first 2 moves — faculty sees identical rolls and board state!)*
4. **Show Classic 52-Tile Toggle & Draw Condition (60 sec):**
   `python v2_final/ludo_oop.py --mode classic --max-turns 2`
   *(Displays full 52-tile, 4-token board and cleanly triggers the max-turn Draw condition.)*
5. **Show Peer Feedback Delta (30 sec):**
   Highlight `v2_final/CHANGELOG.md` showing exact improvements made from Peer Teams 1 & 2.

---

## 3. High-Probability Viva Questions & Crisp Answers

1. **"Explain how a token moves from the shared outer track into its private home stretch without off-by-one bugs."**
   - Every token tracks personal `steps` from `-1` (Base) to `home_finish` (`31` in Quick, `56` in Classic). Only while `0 <= steps <= track_len - 2` is it on the shared track, mapped via `(start_index + steps) % track_len`. At `steps == track_len - 1`, it enters private lane `H1` where `get_global_pos()` returns `None`, automatically making it immune to captures.
2. **"How did you guarantee `ludo_func.py` has zero classes?"**
   - We wrote an automated Python `ast` check inside `scripts/verify_gates.py` that parses `ludo_func.py` into an Abstract Syntax Tree and asserts `0` `ast.ClassDef` nodes.
3. **"Standard Ludo doesn't have a draw—how did you handle the rubric's draw testing requirement?"**
   - We engineered two clean draw mechanisms: a configurable `--max-turns` turn cap (default 100/250, settable to `2` for fast testing) and an in-game mutual `draw` command requiring unanimous `y` confirmation from all other players.
4. **"What happens if two players sit on a safe tile, or if a player rolls three 6s in a row?"**
   - On safe tiles (`★`), `is_safe_tile()` short-circuits capture checks so opposing tokens coexist peacefully. On three consecutive 6s, `consecutive_sixes == 3` voids the 3rd roll before move selection, resets the counter, and advances the turn.
5. **"Why did you isolate `random.Random(seed)` instead of calling `random.randint()`?"**
   - Isolating the RNG per game prevents global state leakage across tests and allows deterministic `--seed` parity proofs comparing OOP and Functional engines move-for-move.

---

## 4. Mastering the Mandatory Capstone Question

> **Question:** *"If AI can generate both versions of a program, why is it important for a programmer to understand programming concepts and design?"*

**Anchor Your Answer in 4 Concrete Lessons from This Exact Project:**
1. **Specification & Architecture Come Before Syntax:** AI will gladly generate a messy 1,000-line script with hardcoded numbers (`52`, `4`) unless a programmer designs a clean parameterized coordinate model (`steps` + `PRESETS`) and decouples game logic from CLI I/O.
2. **Enforcing Paradigm Integrity:** Without understanding OOP vs. Functional boundaries, AI often slips `@dataclass` or helper classes into a "function-based" file, or dumps procedural logic into a single "god class" in OOP. We had to explicitly design and AST-verify both architectures.
3. **Catching Subtle State & Edge-Case Bugs:** AI frequently makes off-by-one errors on circular wraparound, forgets to reset `consecutive_sixes` after an auto-skip or non-6 capture, or mutates shared references silently. Only a programmer who understands state invariants can write a 1,000-game parity fuzzer and diagnose root causes.
4. **Safe Evolution & Accountability:** When Peer Teams 1 & 2 requested changes for `v2_final`, understanding encapsulation vs. centralized state dictionaries let us evolve both codebases safely without breaking rule parity. AI accelerates typing; engineering judgment guarantees correctness, maintainability, and trust.
