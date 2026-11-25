# OOP vs Functional Programming — Evidence-Based Comparison Report

## Scope and Evidence

This report compares the real `v1_initial/` implementations, not hypothetical
examples:

- OOP package: `v1_initial/oop_ludo/`.
- Functional package: `v1_initial/func_ludo/`.
- Shared presentation and contracts: `v1_initial/shared/`.
- Launchers: `v1_initial/ludo_oop.py` and `v1_initial/ludo_func.py`.

No peer-feedback changes have been received, so `v2_final/` is still reserved.
This report does **not** invent a v1-to-v2 improvement story. Concrete extension
evidence below comes from expanding the actual v1 implementation with
blockades, Kill-to-Enter, Podium Mode, bots, JSON setup, GUI controls, and
commentary.

## Executive Metrics

Measured from Python AST and source files:

| Metric | OOP | Functional |
|---|---:|---:|
| Package files | 9 | 9 |
| Package lines | 1,520 | 1,626 |
| Classes | 10 | **0** |
| Functions and methods | 104 | 89 |
| Launcher lines | 17 | 17 |
| Launcher classes | 0 | 0 |
| Primary state owner | Objects and attributes | One explicit state dictionary |
| Rule engine entry points | `LudoGame` methods | `rules.py` functions |
| Canonical state export | `export_canonical_state()` | `export_canonical_state(state)` |

Both depend on seven shared, zero-class modules containing 1,190 lines and 38
functions. Shared code covers presets, validation, seating, event creation,
board geometry, and rendering. It does **not** implement the game rules.

The complete `python scripts/verify_gates.py --stage v1` gate passed with zero
failures and zero warnings. Its observed run contained:

- 86 unit and edge-case tests.
- 13 parity/CLI tests.
- 1,080 complete games: 362 wins and 718 draws.
- 93,403 rolls, 71,678 moves, and 238,919 compared snapshots.
- 28 audited Python files: 10 OOP classes and 0 functional/shared classes.

## Question 1: How Is Data Stored in Each Approach?

### OOP: data belongs to the object that uses it

`Token` stores `token_idx`, `label`, and `steps`; `Player` owns a list of tokens
plus seat metadata and `captures_made`; `Board` owns locked geometry; `LudoGame`
owns match-wide turn and result state.

A player is constructed in `v1_initial/oop_ludo/models.py:63`:

```python
self.tokens = [
    Token(token_idx, f"{self.prefix}{token_idx + 1}")
    for token_idx in range(tokens_per_player)
]
```

A token owns its movement behavior in `v1_initial/oop_ludo/models.py:35`:

```python
def can_move(self, roll: int, home_finish: int, exact_home_roll: bool = True) -> bool:
    if self.is_in_base():
        return roll == 6
    if self.is_finished(home_finish):
        return False
    if exact_home_roll:
        return self.steps + roll <= home_finish
    return True
```

Moving and capture therefore use clear domain statements:

```python
token.move_to(new_steps)
victim.send_to_base()
```

These operations are at `v1_initial/oop_ludo/engine.py:224` and
`v1_initial/oop_ludo/engine.py:241`.

### Functional: data is explicit in nested collections

`create_game_state()` builds one dictionary with keys `config`, `players`,
`current_player`, `turn_count`, `consecutive_sixes`, `status`, `finish_order`,
`events`, and others. Each player is a dictionary; each token is also a
dictionary. The creation is at `v1_initial/func_ludo/state.py:12`.

```python
"tokens": [
    {
        "token_idx": token_idx,
        "label": f"{spec['prefix']}{token_idx + 1}",
        "steps": -1,
    }
    for token_idx in range(int(match_config["tokens_per_player"]))
]
```

Movement is a visible key update at `v1_initial/func_ludo/rules.py:265`:

```python
token["steps"] = new_steps
```

Capture is equally explicit at `v1_initial/func_ludo/rules.py:283`:

```python
victim["steps"] = -1
player["captures_made"] += 1
```

### Comparison

The functional form makes the complete schema easy to inspect: `state` is the
single object passed between functions. The OOP form hides implementation
details behind meaningful attributes and methods, but the complete match state
must be understood across several objects.

Both export the same JSON-friendly structure through
`LudoGame.export_canonical_state()` at `v1_initial/oop_ludo/engine.py:343` and
`export_canonical_state(state)` at `v1_initial/func_ludo/state.py:72`.

## Question 2: How Is Game Logic Organized?

### OOP: behavior is placed near its owner

The core class layout is:

- `Token`: movement legality and personal coordinate changes.
- `Player`: token collection and finishing checks.
- `Board`: coordinate translation and safe-tile lookup.
- `LudoGame`: roll processing, legal moves, captures, turn rewards, draws, and
  canonical export.
- `BotPolicy`: deterministic token scoring.
- `CLIRenderer`, `Commentary`, `GuiSession`, `LudoGUI`, and `CliApplication`:
  presentation and interaction.

For example, coordinate translation belongs to `Board` at
`v1_initial/oop_ludo/models.py:122`:

```python
def get_global_pos(self, start_index: int, steps: int) -> int | None:
    if steps < 0 or steps > self.outer_last_step:
        return None
    return (start_index + steps) % self.track_len
```

The engine asks objects to do their work:

```python
target = self._compute_target(player, token, roll)
token.move_to(new_steps)
player_finished = player.all_finished(self.board.home_finish)
```

### Functional: a function pipeline makes every argument visible

`rules.py` separates the workflow into functions:

```text
get_valid_moves(state, player_idx, roll)
    -> preview_move(state, player_idx, token_idx, roll)
    -> apply_move(state, token_idx, roll)
    -> advance_turn(state)
```

The equivalent coordinate function at `v1_initial/func_ludo/rules.py:26` receives
all required values explicitly:

```python
def get_global_pos(
    start_index: int,
    steps: int,
    track_len: int,
    outer_last_step: int,
) -> int | None:
```

Queries such as `preview_move()` do not mutate state. State changes happen in
`process_roll()`, `apply_move()`, `advance_turn()`, `declare_mutual_draw()`, and
`quit()`.

### Comparison

Read-only helpers look similar in both paradigms because they answer the same
question. Mutating logic differs: OOP delegates updates to owned objects, while
functional code passes a shared dictionary to named operations. Neither
implementation delegates Ludo rules to the shared package; both rule engines
are independently written and parity-tested.

## Question 3: How Are Player Turns Managed?

### OOP turn ownership

`LudoGame` stores `current_player_index`, `turn_count`, `consecutive_sixes`,
`finish_order`, and terminal status as attributes.

`process_roll()` emits the roll, handles a third-six forfeiture, finds legal
moves, and automatically advances when no move exists. `apply_move()` owns the
bonus-versus-advance decision after a legal move. Callers must not advance a
second time.

At `v1_initial/oop_ludo/engine.py:279`, bonus turns are represented as one
boolean condition:

```python
bonus_turn = bool(
    roll == 6
    or (captured_labels and self.config["bonus_on_capture"])
    or (reached_home and self.config["bonus_on_home"])
)
```

At `v1_initial/oop_ludo/engine.py:312`, `advance_turn()` skips finished players,
increments `turn_count`, emits `TURN_ADVANCED`, and enforces the draw cap:

```python
candidate = (self.current_player_index + offset) % len(self.players)
if not self.players[candidate].all_finished(self.board.home_finish):
    self.current_player_index = candidate
    break
self.turn_count += 1
```

### Functional turn ownership

The same values live under explicit keys in `state`.

At `v1_initial/func_ludo/rules.py:323`, the equivalent bonus condition is:

```python
bonus_turn = bool(
    roll == 6
    or (captured_labels and config["bonus_on_capture"])
    or (reached_home and config["bonus_on_home"])
)
```

At `v1_initial/func_ludo/rules.py:364`, `advance_turn(state)` updates the same
canonical values:

```python
candidate = (state["current_player"] + offset) % len(state["players"])
if not _all_finished(state["players"][candidate], int(state["config"]["home_finish"])):
    state["current_player"] = candidate
    break
state["turn_count"] += 1
```

### Comparison

The control flow is deliberately parallel. A bonus roll retains the active
seat and does not increase the turn cap. A normal advance resets the six streak.
Podium play skips finished players. The first finisher remains the terminal
winner, while 3P/4P podium play continues until only one unfinished player
remains.

Canonical snapshots compare `turn_count`, `current_player`,
`consecutive_sixes`, `finish_order`, status, and event history after every roll,
bot decision, and move. This catches drift at transition boundaries rather
than only comparing the final winner.

## Question 4: Which Version Is Easier to Understand?

### Functional strengths

For a beginner, the functional version is easy to trace as a data pipeline.
`main -> run_cli -> _human_turn -> _roll_and_move -> process_roll/apply_move`
shows explicit inputs and outputs. There is no `self` indirection, and a printed
`state` exposes the whole match.

For example, this functional statement is immediately readable:

```python
player = state["players"][state["current_player"]]
token = player["tokens"][token_idx]
```

### OOP strengths

As the match grows, OOP reads closer to the domain language:

```python
token.can_move(roll, self.board.home_finish, self.config["exact_home_roll"])
player.all_finished(self.board.home_finish)
board.get_global_pos(player.start_index, token.steps)
```

These expressions are at `v1_initial/oop_ludo/models.py:35`,
`v1_initial/oop_ludo/models.py:87`, and `v1_initial/oop_ludo/models.py:122`.
They avoid repeatedly spelling out deep dictionary paths and show which object
owns a responsibility.

### Balanced answer

The functional package is easier to inspect linearly; the OOP package is easier
to navigate by concept once students understand objects. The modular layout is
important for both: no rule algorithm is hidden inside the launcher, and both
packages use concise docstrings and type hints.

## Question 5: Which Version Is Easier to Debug?

### Functional debugging advantage

`export_canonical_state(state)` produces a serializable snapshot from one
object. A failure can be compared key-by-key: active seat, token coordinates,
captures, finish order, status, and event sequence. The event stream is ordered
and JSON-compatible, so it can be saved as a fixture or replayed for inspection.

The functional version's direct key paths can also make a faulty update visible:

```python
token["steps"] = new_steps
state["current_player"] = candidate
```

Its limitation is that a misspelled dictionary key may create an unused field
without raising the immediate error that an unknown attribute would raise.

### OOP debugging advantage

Objects separate responsibilities and expose meaningful failures such as
`AttributeError`. A stack trace points toward a domain object and operation,
for example `Token.send_to_base()` or `LudoGame.advance_turn()`. The canonical
export method converts all objects into the same comparison schema used by the
functional version.

Its limitation is that the live match is distributed. A debugger may need to
inspect `game.players`, each `player.tokens`, and `game.board` rather than print
one dictionary. `export_canonical_state()` solves this for reproducible
comparison.

### Actual debugging evidence

The project's gate runs both implementations as real subprocesses and compares
output after masking only paradigm-specific `OOP:`/`Functional:` code traces.
It compares canonical snapshots after every engine action. This found the real
harness problem where `apply_move()` was followed by an extra `advance_turn()`;
the fix removed the duplicate test-side advance, not a game rule.

The optimized event-copy helpers at `v1_initial/shared/contracts.py:218` also
preserve snapshot independence without deep-copying arbitrary object graphs.

## Question 6: Which Version Is Easier to Modify and Extend?

### Real extension evidence from v1

The implemented expansion touched several coordinated areas in both paradigms:

| Extension | OOP change | Functional change |
|---|---|---|
| Strict blockades | `LudoGame._strict_path_blocked()` uses `Player.tokens_at()` | `_strict_path_blocked(state, ...)` uses `_tokens_at()` |
| Safe-pair immunity | `_capturable_tokens()` skips pairs | `_capturable_tokens()` skips pairs |
| Kill-to-Enter | `_compute_target()` wraps the outer route | `_compute_target()` wraps the outer route |
| Podium Mode | `finish_order` and required finishers | `state["finish_order"]` and required finishers |
| Bot seats | `BotPolicy.decision_details()` | `decision_details()` and `choose_move()` |
| GUI playback | `GuiSession` methods | Functions operating on a session dictionary |
| Commentary | `Commentary.gameplay()` and `.code()` | `gameplay_message()` and `code_message()` |

The blockade code demonstrates the structural difference without shared rule
logic:

```python
# OOP — v1_initial/oop_ludo/engine.py:125
if opponent.index != player.index and len(opponent.tokens_at(self.board, global_pos)) >= 2:
    return True
```

```python
# Functional — v1_initial/func_ludo/rules.py:145
if opponent["index"] != player["index"] and len(_tokens_at(state, opponent, global_pos)) >= 2:
    return True
```

### Which is easier to extend?

OOP is easier when new behavior naturally belongs to an existing object. A new
token rule can become a `Token` method, and a new match rule can become a
`LudoGame` method. Bot behavior is separately isolated in `BotPolicy`, so the
engine does not embed selection heuristics.

Functional code is easier when the extension is a new transformation over a
known schema. Explicit parameters make dependencies visible, and the whole
change can be expressed as functions. Its cost is schema auditing: when a state
key is added or renamed, creation, export, rendering, and every affected rule
must be updated consistently.

Shared contracts reduce schema drift in the functional version. Configuration
validation and canonical exports prevent arbitrary key additions, while tests
check that both state schemas remain compatible. This improves the functional
design without replacing it with a class wrapper.

### Honest v2 limitation

There are no genuine peer reports or peer-driven v2 fixes yet. The comparison
therefore uses actual v1 extension work as evidence and leaves `v2_final/`
untouched. Claiming a completed peer-improvement cycle would be fabricated.

## Question 7: Advantages and Limitations of Each Approach

| Dimension | OOP | Functional |
|---|---|---|
| Encapsulation | Strong: token/player/board state has clear owners | Explicit: all state passed to functions |
| Boilerplate | Classes, constructors, attributes, methods | Dictionary schema and repeated key paths |
| Domain readability | `player.all_finished()` reads naturally | `_all_finished(player, home_finish)` is direct |
| State inspection | Distributed; canonical export provides one snapshot | One dictionary is directly inspectable |
| Serialization | Requires export mapping | `export_canonical_state(state)` still excludes RNG and copies containers |
| Extensibility | Strong for new object-owned behavior | Strong for new state transformations |
| Silent key typos | Unknown attributes usually fail clearly | Misspelled keys can silently add data |
| Reuse | Behavior follows objects | Functions are easy to call with explicit inputs |
| Testing | Objects can be inspected and compared via canonical export | State transitions are direct to assert |
| Best fit | Larger domain models and multiple interaction layers | Data-oriented pipelines and compact algorithms |
| Main limitation | More structure and object navigation | Schema consistency becomes the developer's responsibility |

### Shared design choices

Both versions benefit from shared presets, geometry, rendering, event schemas,
and setup validation. This avoids duplicating presentation code while keeping
both rule engines authentic and independently understandable.

## Capstone Reflection: Why Understand Design if AI Can Generate Both Versions?

AI can produce syntactically valid classes and functions, but correctness
depends on design decisions: who owns state, which operation advances a turn,
how a capture is previewed without mutation, whether a blockade blocks crossing,
and how two paradigms expose the same canonical state. The 1,080-game gate
checks those decisions at 238,919 boundaries; it cannot be replaced by a claim
that the programs look similar.

Understanding both paradigms lets a programmer review generated code, explain
tradeoffs, detect duplicated state changes, preserve invariants, and choose a
structure that remains understandable during a viva and future maintenance.
The goal is not merely generated code; it is code whose behavior can be proved,
explained, and safely changed.
