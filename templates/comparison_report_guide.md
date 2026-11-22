# Comparison Report Guide (`docs/03_comparison_report.md`)

> **Agent & Team Rule:** Do NOT write generic textbook essays! Every answer below MUST reference **actual classes, functions, dictionary keys, line counts, and side-by-side code snippets** taken directly from our finished `v2_final/ludo_oop.py` and `v2_final/ludo_func.py`.

---

## Required Structure (Covers All 7 Prompt Questions — 15 Marks)

### Executive Metrics Table (Auto-Computed from `v2_final/`)
| Metric | `v2_final/ludo_oop.py` (OOP) | `v2_final/ludo_func.py` (Functional) |
|---|---|---|
| Total Lines of Code (LOC) | *(measure)* | *(measure)* |
| Number of Classes | *(measure — e.g. 5)* | **0** *(AST-verified)* |
| Number of Methods / Functions | *(measure)* | *(measure)* |
| Primary State Container | Distributed object attributes (`Token`, `Player`, `Board`, `LudoGame`) | Single centralized `state` dictionary |
| Automated Parity Test Result | 1,000 / 1,000 games identical | 1,000 / 1,000 games identical |

### Question 1: How is data stored in each approach?
- Contrast `Token.steps`, `Player.tokens`, `Board.safe_tiles`, `LudoGame.turn_count` (encapsulated attributes on objects) vs. nested `state["players"][i]["tokens"][j]["steps"]` dictionary/list structure.
- Include a real side-by-side snippet showing token initialization in both files.

### Question 2: How is game logic organized?
- Contrast behavior co-located with data (`token.can_move()`, `board.get_global_pos()`, `game.apply_move()`) vs. flat modular function pipelines (`get_valid_moves(state, player_idx, roll)` -> `apply_move(state, token_idx, roll)`).
- Explain how pure query helpers (`get_global_pos`, `can_token_move`, `preview_move`) look nearly identical in spirit, while stateful mutations differ structurally.

### Question 3: How are player turns managed?
- Contrast `LudoGame.current_player_index`, `self.consecutive_sixes`, and `self.advance_turn()` mutating internal object state vs. `advance_turn(state)` explicitly mutating `state["current_player"]`, `state["consecutive_sixes"]`, and `state["turn_count"]`.
- Show the exact `process_roll()` + `advance_turn()` code side by side.

### Question 4: Which version is easier to understand?
- Provide a nuanced, honest engineering answer grounded in our Ludo codebase:
  - **Function-Based** is easier for beginners to trace sequentially from top to bottom (`main -> run_cli -> process_roll -> apply_move`) with zero `self` indirection.
  - **Class-Based** becomes easier to read once the domain grows (Quick + Classic presets, multiple players, multiple tokens, separate renderer) because `player.all_finished()` reads like natural English compared to deeply nested dict indexing `state["players"][idx]["tokens"]`.

### Question 5: Which version is easier to debug?
- **Function-Based advantage:** Printing or JSON-dumping a single `state` dict immediately exposes the entire universe of the game in one snapshot—making parity debugging and serialization trivial.
- **Class-Based advantage:** Type structure and attribute names (`token.steps`) catch typos faster via IDE autocomplete and `AttributeError` vs. silent dictionary key mistakes (`state["turn_cnt"] = 1` creating a phantom key instead of updating `turn_count`!).

### Question 6: Which version is easier to modify and extend?
- **Use real evidence from our `v1 -> v2` peer-feedback cycle!**
- Walk through one concrete feature we actually added in `v2_final` (and a hypothetical future extension like adding AI Bot players or Blockades):
  - Adding an `AIPlayer(Player)` subclass in OOP isolates bot decision logic cleanly via polymorphism.
  - Adding a new field in `ludo_func.py` requires auditing every function that reads or initializes the `state` dictionary schema.

### Question 7: Advantages and Limitations of Each Approach
- Present a crisp comparative matrix covering: Encapsulation, Boilerplate, State Inspection/Serialization, Extensibility, Risk of Silent Key Typos, and Ideal Use Cases.

### Capstone Reflection
- Close with a sharp, evidence-backed paragraph answering: *"If AI can generate both versions of a program, why is it important for a programmer to understand programming concepts and design?"*
