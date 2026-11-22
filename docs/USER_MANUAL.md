# Multiplayer Ludo — User Manual

This manual explains how to start and play either command-line version of the
game. It is for players; development and testing instructions are in the
repository's other documents.

## 1. What You Need

- Python 3.11 or newer
- A terminal such as PowerShell, Command Prompt, Windows Terminal, or a macOS/Linux terminal
- No additional Python packages

The game is local hot-seat multiplayer for 2–4 people. Players take turns at
the same computer.

## 2. Start a Game

### Recommended: use the launcher

From the project directory, run:

```text
python play_ludo.py
```

Choose the Object-oriented or Function-based version when prompted. The game
then asks for the mode (unless supplied on the command line), number of
players, and names. The launcher checks for Python 3.11+ and needs no package
installation.

You can select a version and pass game options directly:

```text
python play_ludo.py --engine oop --mode quick --seed 42
python play_ludo.py --engine functional --mode classic --no-color
```

`--engine` may be `oop` or `functional`. If it is omitted, the launcher asks
which version to run.

### Run an implementation directly

You can also bypass the launcher and run either implementation:

```text
python v1_initial/ludo_oop.py
```

or:

```text
python v1_initial/ludo_func.py
```

The two versions follow the same rules and accept the same options. If you omit
`--mode`, choose Quick or Classic when prompted. Then enter the number of
players and each player's name. A blank name uses the suggested default.
Repeated names are made unique automatically.

### Optional command-line options

| Option | What it does | Example |
|---|---|---|
| `--mode quick` | Starts Quick Mode without asking for the mode | `python v1_initial/ludo_oop.py --mode quick` |
| `--mode classic` | Starts Classic Mode without asking for the mode | `python v1_initial/ludo_func.py --mode classic` |
| `--seed INTEGER` | Uses a repeatable dice sequence, useful for demonstrations | `--seed 42` |
| `--max-turns INTEGER` | Sets the turn limit; it must be a positive number | `--max-turns 20` |
| `--no-color` | Disables ANSI colors | `--no-color` |
| `--help` | Shows the available options | `python v1_initial/ludo_oop.py --help` |

Options can be combined:

```text
python v1_initial/ludo_oop.py --mode quick --seed 42 --max-turns 20 --no-color
```

The `--seed` option does not choose moves for you; it only makes the die rolls
repeatable. For identical play, players must also make the same choices.

### Are there colors?

Yes. The game uses ANSI terminal colors for the mode heading, player names,
and winner banner. Colors are enabled by default. They display in terminals
that support ANSI escape codes, including modern Windows Terminal and VS Code
terminals. Use `--no-color` if colors do not display correctly or you prefer
plain text.

## 3. The Board and Tokens

There are four player colors, in seat order: Red, Green, Yellow, and Blue.
Each token has a short label, such as `R1` or `G2`.

| Mode | Shared track | Home stretch | Tokens per player | Default turn limit |
|---|---:|---:|---:|---:|
| Quick | 28 tiles | 4 spaces | 2 | 100 turns |
| Classic | 52 tiles | 5 spaces | 4 | 250 turns |

The board display shows numbered track tiles. A `*` next to a tile marks a
safe tile. Tokens shown on the same tile are displayed together. The status
panel lists every token's position:

- `BASE` — waiting to enter the board
- `T00`, `T01`, and so on — a shared track tile
- `H1`, `H2`, and so on — that player's private home stretch
- `HOME` — finished

Two players start opposite one another. With three or four players, seats use
the clockwise color order.

## 4. Taking a Turn

At the active player's prompt:

1. Press **Enter**, or type `r` / `roll`, to roll.
2. If there are legal moves, the game displays numbered choices and previews.
3. Type the number of the token move you want and press **Enter**.
4. If there are no legal moves, the game skips the move and passes play
   automatically.

When the game asks for a move number, enter a number shown in the menu—not a
token label. Invalid entries are rejected and the game asks again.

### Commands at the roll prompt

| Input | Result |
|---|---|
| Enter, `r`, or `roll` | Roll the die |
| `draw` | Ask every other player to agree to a draw |
| `quit` or `q` | Ask for confirmation before ending the game |

Commands are case-insensitive, and surrounding spaces are ignored. At a yes/no
confirmation prompt, enter `y` / `yes` or `n` / `no`. Pressing Ctrl+C or
Ctrl+Z/EOF exits gracefully.

## 5. Rules of Play

### Leaving the base

A token in `BASE` can enter the track only when its player rolls a 6. It then
lands on that player's starting tile. Starting tiles are safe, so this entry
cannot capture an opponent.

### Moving and reaching home

- A token already on the track or in its home stretch moves forward by the
  number rolled.
- A token must reach `HOME` with an exact roll. If a move would go past `HOME`,
  that move is not offered.
- After completing the outer track, a token enters its owner's private home
  stretch. Tokens in that stretch cannot be captured.
- A player wins as soon as all of their tokens reach `HOME`.

### Safe tiles and captures

- Landing on a safe tile does not capture opponents there; different players'
  tokens may share that tile safely.
- Landing on an opponent's token on a non-safe outer tile sends **all** of that
  opponent's tokens on that tile back to `BASE`.
- Your own tokens are not captured by your moves. Multiple same-color tokens
  can share a tile, and there are no blockades.
- Passing over another token does not capture it; the moving token must land
  on its tile.

### Extra rolls and three sixes

A move earns one extra roll if it rolls a 6, captures at least one opponent
token, or reaches `HOME`. These reasons do not stack into multiple extra rolls.

Three consecutive sixes by the same player cause the third roll to be forfeited
and pass the turn. Previous moves from the first two sixes remain in place.
Any roll from 1 to 5 resets the consecutive-six count. A roll with no legal
move is skipped and passes play automatically.

### Draws and ending a game

- **Turn-limit draw:** The game draws when the configured maximum number of
  turns is reached. The default depends on the selected mode; `--max-turns`
  changes it.
- **Mutual draw:** At the roll prompt, type `draw`. Every other player must
  accept for the draw to take effect. If a player declines, play resumes with
  the proposer, who can roll or make another choice.
- **Quit:** Type `quit` or `q`, then confirm with `y` / `yes`. Answer `n` / `no`
  to continue the game instead.

## 6. Quick Example

Start a short, plain-text Quick game:

```text
python v1_initial/ludo_func.py --mode quick --seed 42 --max-turns 20 --no-color
```

Enter the player count and names. At each roll prompt, press Enter. If a 6
unlocks one or more tokens, choose the desired numbered option. After a
non-bonus move, the next player takes their turn. The game ends with a winner,
a turn-limit draw, a mutual draw, or a confirmed quit.

## 7. Troubleshooting

- **`python` is not recognized:** Install Python 3.11+ and ensure it is
  available on your PATH. On some Windows systems, use `py` instead of `python`.
- **ANSI colors look odd:** Add `--no-color`.
- **The game asks for another move after an invalid entry:** Enter one of the
  numbered choices currently displayed.
- **A token cannot move:** It may still be in `BASE` without a 6, already be at
  `HOME`, or need an exact roll that does not overshoot the finish.
