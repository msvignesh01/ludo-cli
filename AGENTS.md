# AGENTS.md — Autonomous Agent Governance & Perfection Contract

You are operating as a senior Python systems engineer and QA architect building the **CIA1 Multiplayer Ludo Assignment**. Follow every directive in this file strictly. **Do not stop early, do not skip verification gates, and do not leave TODOs or placeholders in code.**

---

## 1. Non-Negotiable Hard Constraints

1. **Zero External Dependencies:**
   - Use **Python 3.11+ Standard Library ONLY** (`random`, `os`, `sys`, `argparse`, `copy`, `unittest`, `subprocess`, `ast`, etc.).
   - No `colorama`, `rich`, `pygame`, `pytest`, `pydantic`, or third-party packages. Peer testers must run `python ludo_oop.py` and `python ludo_func.py` out of the box.
2. **Strict Paradigm Separation (AST-Enforced):**
   - `ludo_oop.py`: Must use idiomatic Object-Oriented Programming with cleanly designed user-defined classes (`Token`, `Player`, `Board`, `CLIRenderer`, `LudoGame`), encapsulated state, and methods.
   - `ludo_func.py`: Must contain **ZERO `class` definitions anywhere in the file** (verified via Python `ast.ClassDef` scan). Do NOT use `@dataclass`, `Enum` subclasses, `NamedTuple` class syntax, or custom `Exception` subclasses. Use only functions and built-in data structures (`dict`, `list`, `tuple`, `set`, primitives).
3. **100% Deterministic Rule & Output Parity:**
   - Given the exact same `--mode`, player list, `--seed`, `--max-turns`, and input sequence, `ludo_oop.py` and `ludo_func.py` MUST produce **byte-for-byte identical canonical game states** on every turn AND identical game outcomes (winner or draw reason).
   - Both files must support identical CLI arguments:
     - `--mode {quick,classic}` (optional; interactive prompt if omitted)
     - `--seed <int>` (optional; deterministic RNG for testing)
     - `--max-turns <int>` (optional; overrides default turn cap for draw testing)
     - `--no-color` (optional; strips ANSI escape codes cleanly)
4. **Windows & Cross-Platform ANSI Safety:**
   - Enable native Windows VT100 ANSI escape processing at startup (`os.system("")` when `os.name == "nt"` and colors are enabled).
   - Never rely on platform-only modules (`termios`, `curses`, `fcntl`).
   - Use standard UTF-8 safe characters with clean ASCII fallbacks if stdout encoding is not UTF-8 (e.g., `cp1252` on default Windows PowerShell/CMD).
5. **Code Clarity for Human Viva Defense (15 Rubric Marks):**
   - Every function and method must have a concise, clear docstring and type hints (using built-in `list[int]`, `dict[str, Any]` — never `class` aliases in `ludo_func.py`).
   - Avoid clever one-liners or obscure metaprogramming. A final-year undergrad team must be able to read and explain every single line aloud to faculty.
6. **Preserve `v1_initial/` as Immutable Baseline:**
   - Once `v1_initial/` passes all verification gates and is handed off for peer testing, NEVER overwrite `v1_initial/`. All peer-feedback bug fixes and UX improvements go into `v2_final/` alongside `v2_final/CHANGELOG.md`.

---

## 2. Mandatory Agent Operating Loop ("Stop Only at Perfection")

For **every** phase in `PLAN.md`, execute this exact loop:

```text
READ SPEC -> IMPLEMENT -> RUN GATES -> INSPECT FAILURES -> FIX ROOT CAUSE -> RE-RUN ALL GATES -> UPDATE TRACKER.md
```

### Perfection Exit Criteria (You May ONLY Stop When ALL Are True)
- [ ] `python scripts/verify_gates.py --stage <v1|v2>` exits with code `0` and **0 warnings**.
- [ ] AST audit confirms **0 `class` nodes** in `ludo_func.py` and **>= 4 core `class` nodes** in `ludo_oop.py`.
- [ ] Stdlib-only import audit passes across all Python files.
- [ ] Unit & edge-case test suite passes **100%** (unlock on 6, exact home roll, overshoot rejection, safe tile non-capture, non-safe multi-token capture, bonus roll non-stacking, triple-6 forfeit, auto-skip, 2P diagonal seating, 3P/4P clockwise seating, max-turn draw, mutual `/draw`, quit handling, invalid inputs).
- [ ] Automated **Parity Fuzz Test** simulates at least **1,000 full games** across:
  - Quick Mode: 2P, 3P, 4P
  - Classic Mode: 2P, 3P, 4P
  comparing canonical state snapshots after *every single move* between OOP and Functional engines with **0 mismatches**.
- [ ] End-to-End **Subprocess CLI Test** drives both `ludo_oop.py` and `ludo_func.py` via `subprocess.run` with scripted stdin (including invalid inputs, captures, draw prompt, and full win playthroughs under `--seed` and `--no-color`) and verifies **100% identical outputs and exit code `0`**.
- [ ] `TRACKER.md` has all completed items checked off with recorded command outputs/metrics.
- [ ] `docs/04_ai_interaction_log.md` records real prompts, architectural decisions, and real bugs caught/fixed during the build.

---

## 3. Anti-Shortcuts & Failure Prevention Rules

- **NEVER** loosen a test assertion to make a failing test pass. Fix the engine logic instead.
- **NEVER** copy-paste logic blindly without keeping OOP and Functional idioms authentic:
  - In `ludo_oop.py`, methods belong on the objects owning the data (`token.can_move()`, `board.get_global_pos()`, `player.all_home()`, `game.play_turn()`).
  - In `ludo_func.py`, functions accept `state` (and explicit arguments) and operate on pure Python collections without hidden class wrappers or global mutable singletons.
- **NEVER** let an unhandled exception crash the CLI on bad user input (`EOFError`, `KeyboardInterrupt`, empty string, negative numbers, huge numbers, emojis, whitespace, non-ASCII text).
- **NEVER** hardcode magic numbers (`28`, `52`, `4`, `5`, `31`, `56`) inside movement or rendering logic. Always derive everything from the active preset dictionary/config (`track_len`, `home_len`, `tokens_per_player`, `home_finish`, `safe_tiles`).
- **NEVER** fabricate peer test reports. Leave `testing/team1_report.md` and `testing/team2_report.md` as clean ready-to-fill templates until actual peer feedback is provided by the human team.
