# Flowchart & Pseudocode — Multiplayer Ludo CLI

This document provides the language-agnostic control flow and algorithmic specification implemented identically by both `ludo_oop.py` (Class-Based) and `ludo_func.py` (Function-Based).

---

## 1. Master Turn-Loop Flowchart (Mermaid)

```mermaid
flowchart TD
    A([Start Program]) --> B[Parse CLI Flags: --mode, --seed, --max-turns, --no-color]
    B --> C[Select Mode Quick/Classic & Player Count 2-4 & Names]
    C --> D[Initialize Game State: All Tokens at steps = -1, turn_count = 0]
    D --> E{turn_count >= max_turns?}
    E -- Yes --> DRAW_CAP([End Game: DRAW - Max Turns Reached])
    E -- No --> F[Render Colored CLI Board, Home Lanes & Last Event]
    F --> G[Prompt Active Player: ENTER to Roll / draw / quit]
    G -- quit confirmed --> QUIT([Exit Cleanly])
    G -- draw requested --> H{All Other Players Confirm y?}
    H -- Yes --> DRAW_MUT([End Game: DRAW - Mutual Agreement])
    H -- No --> F
    G -- Roll Die --> I[roll = RNG.randint 1..6]
    I --> J{roll == 6?}
    J -- Yes --> K[consecutive_sixes += 1]
    K --> L{consecutive_sixes == 3?}
    L -- Yes --> M[Log Triple-6 Forfeit & Reset consecutive_sixes = 0]
    M --> ADV[Advance Current Player & turn_count += 1]
    L -- No --> N[Compute Valid Moves for Current Player & roll]
    J -- No --> O[consecutive_sixes = 0]
    O --> N
    N --> P{Valid Moves Empty?}
    P -- Yes --> Q[Log Auto-Skip & Reset consecutive_sixes = 0]
    Q --> ADV
    P -- No --> R[Display Annotated Moves & Prompt Valid Move Selection]
    R --> S[Apply Move: Update Token steps]
    S --> T{Landed on Outer Non-Safe Tile with Opponent Tokens?}
    T -- Yes --> U[Reset All Opponent Tokens on Tile to BASE -1; captured = True]
    T -- No --> V[captured = False]
    U --> W{All Current Player Tokens at HOME?}
    V --> W
    W -- Yes --> WIN([Render Final Board & Declare WINNER])
    W -- No --> X{roll == 6 OR captured OR reached_home?}
    X -- Yes --> Y[Log Bonus Roll & Keep Same Current Player]
    Y --> F
    X -- No --> Z[Reset consecutive_sixes = 0]
    Z --> ADV
    ADV --> E
```

---

## 2. Core Algorithmic Pseudocode

### A. Coordinate Mapping (`GET_GLOBAL_POS`)
```text
FUNCTION GET_GLOBAL_POS(player_start_index, steps, track_len):
    IF steps < 0 OR steps > (track_len - 2):
        RETURN NULL   // Token is in BASE, Private Home Stretch, or HOME
    RETURN (player_start_index + steps) MOD track_len
END FUNCTION
```

### B. Move Validation (`GET_VALID_MOVES`)
```text
FUNCTION GET_VALID_MOVES(state, player_idx, roll):
    config = state.config
    player = state.players[player_idx]
    valid_moves = EMPTY LIST

    FOR EACH token IN player.tokens:
        IF token.steps == -1:
            IF roll == 6:
                target_steps = 0
                APPEND move_preview(token, target_steps) TO valid_moves
        ELSE IF token.steps < config.home_finish:
            IF token.steps + roll <= config.home_finish:
                target_steps = token.steps + roll
                APPEND move_preview(token, target_steps) TO valid_moves

    RETURN valid_moves
END FUNCTION
```

### C. Move Application & Capture Resolution (`APPLY_MOVE`)
```text
FUNCTION APPLY_MOVE(state, player_idx, token_idx, roll):
    config = state.config
    player = state.players[player_idx]
    token  = player.tokens[token_idx]

    old_steps = token.steps
    IF old_steps == -1:
        ASSERT roll == 6
        new_steps = 0
    ELSE:
        new_steps = old_steps + roll
        ASSERT new_steps <= config.home_finish

    token.steps = new_steps
    captured_tokens = EMPTY LIST
    reached_home = (new_steps == config.home_finish)

    // Check captures ONLY on shared outer non-safe tiles
    new_global = GET_GLOBAL_POS(player.start_index, new_steps, config.track_len)
    IF new_global IS NOT NULL AND new_global NOT IN config.safe_tiles:
        FOR EACH other_player IN state.players:
            IF other_player.index == player_idx:
                CONTINUE
            FOR EACH opp_token IN other_player.tokens:
                opp_global = GET_GLOBAL_POS(other_player.start_index, opp_token.steps, config.track_len)
                IF opp_global == new_global:
                    opp_token.steps = -1
                    APPEND (other_player.name, opp_token.label) TO captured_tokens

    // Check win condition
    won = ALL(t.steps == config.home_finish FOR t IN player.tokens)
    IF won:
        state.status = "WON"
        state.winner_index = player_idx

    bonus_turn = (NOT won) AND ((roll == 6) OR (LENGTH(captured_tokens) > 0) OR reached_home)

    RETURN {
        old_steps: old_steps,
        new_steps: new_steps,
        captured: captured_tokens,
        reached_home: reached_home,
        won: won,
        bonus_turn: bonus_turn
    }
END FUNCTION
```

### D. Turn Resolution (`PROCESS_ROLL_PHASE`)
```text
FUNCTION PROCESS_ROLL_PHASE(state, roll):
    IF roll == 6:
        state.consecutive_sixes += 1
        IF state.consecutive_sixes == 3:
            state.consecutive_sixes = 0
            ADVANCE_TURN(state)
            RETURN { event: "TRIPLE_SIX_FORFEIT", valid_moves: [] }
    ELSE:
        state.consecutive_sixes = 0

    valid_moves = GET_VALID_MOVES(state, state.current_player, roll)
    IF valid_moves IS EMPTY:
        state.consecutive_sixes = 0
        ADVANCE_TURN(state)
        RETURN { event: "NO_VALID_MOVES", valid_moves: [] }

    RETURN { event: "SELECT_MOVE", valid_moves: valid_moves }
END FUNCTION

FUNCTION ADVANCE_TURN(state):
    state.consecutive_sixes = 0
    state.current_player = (state.current_player + 1) MOD LENGTH(state.players)
    state.turn_count += 1
    IF state.turn_count >= state.max_turns AND state.status == "PLAYING":
        state.status = "DRAW"
        state.draw_reason = "Maximum turn limit reached"
END FUNCTION
```
