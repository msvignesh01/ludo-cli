# Multiplayer Ludo Showcase — User Manual

This manual covers the complete Python game in `v1_initial/`: Quick and Classic
modes, CLI and Tkinter GUI, human and bot seats, configurable rules, JSON
presets, and playback controls.

## 1. Requirements

- Python 3.11 or newer.
- Windows, macOS, or Linux with a terminal.
- Tkinter for the graphical interface; it is included with many standard Python
  installations but may be absent from minimal builds.
- No third-party Python packages and no `pip install` step.

The game is local hot-seat multiplayer. Two to four seats share one computer.

## 2. Start the Game

### Use the launcher

From the repository root:

```text
python play_ludo.py
```

Choose `1` for Object-oriented or `2` for Function-based. You can skip that
choice:

```text
python play_ludo.py --engine oop --mode quick --seed 42 --no-color
python play_ludo.py --engine functional --mode classic --seed 42
```

All game options after `--engine` are forwarded to the selected implementation.

### Run an implementation directly

```text
python v1_initial/ludo_oop.py
python v1_initial/ludo_func.py
```

Both versions have the same rules, flags, prompts, and output. If `--mode` is not
provided by any configuration source, the game asks you to choose Quick or
Classic.

### Open the full setup wizard

```text
python v1_initial/ludo_oop.py --wizard
```

Press Enter to keep a displayed default. The wizard asks only for settings that
were not already supplied by JSON or command-line flags.

### Load a JSON preset

```text
python v1_initial/ludo_func.py --config configs/showcase.json
python v1_initial/ludo_oop.py --config configs/classic.json --max-turns 20
```

`configs/showcase.json` is a four-bot Quick demonstration.
`configs/classic.json` is a two-human Classic match. Explicit command-line
options override the JSON values.

### Open the GUI

```text
python v1_initial/ludo_oop.py --mode quick --ui gui --seed 42
python v1_initial/ludo_func.py --config configs/showcase.json --ui gui
```

If Tkinter cannot open a display, the program prints a clear error instead of a
Python traceback. Use `--ui cli` to select the terminal explicitly.

## 3. Configuration Precedence

Settings are resolved in this order:

```text
built-in defaults < JSON preset < wizard answers < explicit CLI flags
```

A higher-priority source replaces only the values it supplies. Locked board
geometry cannot be changed by any source.

### Main command-line options

| Option | Meaning |
|---|---|
| `--config PATH` | Load match settings and seat metadata from JSON |
| `--wizard` | Ask for unresolved match settings interactively |
| `--mode quick/classic` | Select board scale |
| `--profile showcase/classic` | Select default rule family |
| `--players 2/3/4` | Number of seats |
| `--tokens 1/2/3/4` | Tokens per player |
| `--name NAME` | Set the next player name; repeat for more seats |
| `--seat human/bot` | Set the next seat type; repeat for more seats |
| `--blockades none/strict/safe_pair` | Select blockade behavior |
| `--kill-to-enter` / `--no-kill-to-enter` | Enable/disable capture-gated home entry |
| `--podium-mode` / `--no-podium-mode` | Enable/disable continued podium play |
| `--exact-home-roll` / `--no-exact-home-roll` | Reject or clamp home overshoots |
| `--triple-six-forfeit` / `--no-triple-six-forfeit` | Enable/disable third-six penalty |
| `--safe-tiles` / `--no-safe-tiles` | Enable/disable safe-tile immunity |
| `--bonus-on-capture` / `--no-bonus-on-capture` | Enable/disable capture bonus |
| `--bonus-on-home` / `--no-bonus-on-home` | Enable/disable home bonus |
| `--max-turns N` | Positive turn cap for an automatic draw |
| `--seed N` | Repeatable dice stream |
| `--auto-delay SECONDS` | Non-negative delay for automated actions |
| `--speed slow/normal/fast` | Set delay to 0.8/0.35/0.05 seconds |
| `--commentary gameplay/code/both/off` | Select narration style |
| `--ui cli/gui` | Select interface |
| `--autoplay` | Let automation drive every seat |
| `--no-color` | Disable ANSI colors |
| `--help` | Show all options |

`--auto-delay` takes precedence over `--speed` when both are supplied.

### Examples

Mixed human and bot seats:

```text
python v1_initial/ludo_oop.py --mode quick --players 2 --seat human --seat bot --seed 7 --no-color
```

Four bots with a short draw demonstration:

```text
python v1_initial/ludo_func.py --mode quick --players 4 --tokens 2 --seat bot --seat bot --seat bot --seat bot --autoplay --max-turns 12 --speed fast --commentary gameplay --no-color
```

Strict blockades with Kill-to-Enter disabled:

```text
python v1_initial/ludo_oop.py --mode classic --players 3 --blockades strict --no-kill-to-enter --no-podium-mode --seed 42
```

## 4. Modes, Profiles, and Board Size

| Mode | Track | Home lane | Default tokens | Default turn cap |
|---|---:|---:|---:|---:|
| Quick | 28 tiles on a 9×9 cross | 4 | 2 | 100 |
| Classic | 52 tiles on a 15×15 cross | 5 | 4 | 250 |

**Showcase** defaults to safe-pair blockades, Kill-to-Enter, and Podium Mode.
**Classic** defaults to no blockades, normal home entry, and first-finisher
victory. Other rule defaults remain enabled in both profiles.

The board display uses these token positions:

- `BASE`: waiting in the yard.
- `T00`, `T01`, etc.: shared outer track.
- `H1`, `H2`, etc.: private home lane.
- `HOME`: finished.

Two players start diagonally. Three or four players use clockwise seating.

## 5. Taking a Turn in the CLI

At the active player's prompt:

1. Press Enter, or type `r` / `roll`, to roll.
2. If moves exist, read the numbered choices and destination/consequence notes.
3. Enter the number of the desired move and press Enter.
4. If no move is legal, the game skips automatically.

The number selects a **menu entry**, not a token label. Invalid values are
rejected and the prompt repeats.

### Roll-prompt commands

| Input | Result |
|---|---|
| Enter, `r`, `roll` | Roll the die |
| `draw` | Ask every other player to accept a mutual draw |
| `quit`, `q` | Ask for confirmation before quitting |
| `commentary` | Cycle gameplay → code → both → off |
| `commentary MODE` | Set a specific narration mode |
| `speed SPEED` | Change automated delay to slow, normal, or fast |

Commands are case-insensitive and surrounding spaces are ignored. A blank or
whitespace-only answer means Roll. At yes/no prompts, `y`/`yes` accepts and
`n`/`no` declines. Ctrl+C and closed input end the match cleanly.

### Commentary modes

- **gameplay:** player-friendly event descriptions.
- **code:** real OOP or functional entry-point traces.
- **both:** one gameplay line and one code line per event.
- **off:** no extra event narration; board status still appears.

Changing commentary never changes dice, moves, or canonical game state.

## 6. Rules of Play

### Leaving base

A base token enters only on a 6 and lands on its owner's start tile. With safe
tiles enabled, start tiles are safe. A roll with no legal move passes the turn.

### Moving and reaching home

Tokens move forward by the rolled amount. With exact-home enabled, a token must
finish with an exact roll. With exact-home disabled, an otherwise legal overshoot
finishes the token instead. Tokens in a private home lane cannot be captured.

### Kill-to-Enter

When enabled, a player with zero captures cannot enter their private home lane.
At the end of the outer route, tokens keep looping around the outer track. The
player's first capture unlocks home entry for all of their tokens.

This rule creates active competition. It is not a gate where tokens simply wait.

### Captures and safe tiles

Landing on an opponent on a non-safe outer tile sends that opponent's tokens on
the tile back to base. Each captured token increases `captures_made` by one.
Friendly tokens are never captured. Passing over a token does not capture it;
the mover must land on its tile.

Safe tiles allow different colors to coexist without capture. Disabling safe
tiles also removes starting-tile immunity.

### Blockades

| Setting | Behavior |
|---|---|
| `none` | Opponents pass freely and can capture a stack |
| `strict` | Two same-color opponent tokens block passing and landing |
| `safe_pair` | Opponents can pass a pair, but one token cannot capture the pair |

Strict blockades inspect every tile crossed by the move, not just the landing
tile.

### Extra rolls and three sixes

A move earns exactly one extra roll if it rolls 6, captures with capture bonus
enabled, or reaches home with home bonus enabled. These reasons never stack.
Extra rolls do not increase the turn count.

Three consecutive sixes forfeit the third roll when the rule is enabled. The
first two moves remain. Any non-six resets the streak, including a non-six that
earns a capture bonus. Reaching home also resets it.

### Winning and podium play

A player finishes when every token is home.

- In 2P, the first finisher wins.
- With Podium disabled, the first finisher wins in any match.
- With Podium enabled in 3P/4P, play continues until only one player remains
  unfinished. Finished seats are skipped, and the first finisher is the winner.

### Draws and quitting

- **Turn-limit draw:** occurs when the turn cap is reached.
- **Mutual draw:** every other player must accept. A decline resumes the same
  player without losing a turn.
- **Quit:** confirm `quit` to leave cleanly with exit code 0.

## 7. Bot and Autoplay Controls

Bots choose legal moves using this priority:

1. Finish Home.
2. Capture.
3. Unlock Kill-to-Enter.
4. Land on a safe tile.
5. Escape danger.
6. Advance furthest.
7. Lowest token index on an exact tie.

Bot seats run automatically. `--autoplay` also drives human-marked seats while
preserving their human/bot metadata. This is useful for demonstrations and
repeatable tests.

Speed changes only scheduling delay:

| Speed | Delay |
|---|---:|
| slow | 0.8 seconds |
| normal | 0.35 seconds |
| fast | 0.05 seconds |

## 8. GUI Controls

The Tkinter window displays the cross-shaped board, token markers, player home
and capture counts, legal moves, last event, and commentary.

| Control | Behavior |
|---|---|
| Roll die | Roll for a waiting human seat |
| Token button | Apply one displayed legal move |
| Pause/Resume | Stop or restart automatic scheduling |
| Step | Perform one roll or move manually |
| Speed | Cycle slow, normal, fast |
| Commentary | Cycle gameplay, code, both, off |
| Agree draw | Confirm unanimous draw |
| Quit | Confirm and end the match |

Pause does not prevent Step. Terminal matches disable turn controls. Closing the
window asks for confirmation while a match is active and cancels pending timers.

## 9. Deterministic Seeds

A seed repeats the dice stream. It does not choose token moves. To reproduce a
match, both players or bots must make the same choices in the same order.

Useful demo:

```text
python v1_initial/ludo_oop.py --mode quick --seed 0 --max-turns 100 --no-color
python v1_initial/ludo_func.py --mode quick --seed 0 --max-turns 100 --no-color
```

## 10. Testing the Project

From the repository root:

```text
python testing/test_suite.py
python testing/parity_test.py
python scripts/verify_gates.py --stage v1
```

The parity suite runs 1,080 complete games and real subprocess CLI comparisons,
so it takes several minutes. No packages need to be installed.

## 11. Troubleshooting

- **`python` is not recognized:** install Python 3.11+ and add it to PATH, or use
  your platform's launcher such as `py`.
- **The GUI cannot open:** Tkinter or a display may be unavailable; use
  `--ui cli`.
- **Colors look incorrect:** add `--no-color`.
- **A token cannot move:** it may be in base without a 6, finished, blocked by a
  strict blockade, waiting for a first capture, or needing an exact roll.
- **The wizard does not ask every question:** JSON or CLI values already supplied
  those answers; precedence is intentional.
- **Autoplay does not start:** confirm the seat is bot or `--autoplay` is set.
- **A draw happens quickly:** check `--max-turns`; bonus rolls count within the
  same turn and do not increase the cap.
