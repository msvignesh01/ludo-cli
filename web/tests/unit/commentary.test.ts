import { describe, expect, it } from "vitest";
import { codeMessage, formatCommentary, gameplayMessage } from "../../src/game/commentary";
import { makeEvent } from "../../src/game/events";
import type { GameEvent } from "../../src/game/types";

const names = ["P1", "P2"];

const examples: Array<[string, Record<string, unknown>, string, string]> = [
  ["GAME_STARTED", {}, "Match started.", "Web: createGame(config, playerNames, seed)"],
  ["DICE_ROLLED", { roll: 6 }, "P1 rolls 6.", "Web: rollDie(game) -> processRoll(game, roll=6)"],
  [
    "NO_VALID_MOVES",
    {},
    "P1 has no legal move and skips.",
    "Web: processRoll(game, roll) -> advanceTurn(game)",
  ],
  [
    "TRIPLE_SIX_FORFEIT",
    {},
    "P1 forfeits the third consecutive six.",
    "Web: processRoll(game, roll) -> advanceTurn(game)",
  ],
  [
    "BOT_DECISION",
    { token: "R1", reason: "Capture" },
    "P1 bot chooses R1: Capture.",
    "Web: chooseMove(game, playerIndex, roll, validMoves)",
  ],
  [
    "TOKEN_MOVED",
    { token: "R1", token_idx: 0, roll: 3, old_steps: -1, new_steps: 0 },
    "P1 moves R1 from steps -1 to 0.",
    "Web: applyMove(game, tokenIdx=0, roll=3)",
  ],
  [
    "TOKEN_CAPTURED",
    { victim_player: 1, victim_token: "G1" },
    "P1 captures P2's G1.",
    "Web: applyMove() sets victim.steps = -1",
  ],
  [
    "BLOCKADE_FORMED",
    { tile: 4 },
    "P1 forms a blockade on T04.",
    "Web: applyMove() emits BLOCKADE_FORMED",
  ],
  [
    "PLAYER_FINISHED",
    { place: 1 },
    "P1 finishes in place 1.",
    "Web: allFinished(player, homeFinish)",
  ],
  ["BONUS_TURN", {}, "P1 earns another roll.", "Web: applyMove() -> bonusTurn"],
  ["TURN_ADVANCED", {}, "Next turn: P1.", "Web: advanceTurn(game)"],
  ["GAME_WON", {}, "P1 wins!", "Web: applyMove() sets status = WON"],
  [
    "GAME_DRAW",
    { reason: "Mutual agreement" },
    "Draw: Mutual agreement.",
    "Web: declareMutualDraw(game) or advanceTurn(game)",
  ],
  ["GAME_QUIT", {}, "Game quit.", "Web: quitGame(game)"],
];

describe("event commentary", () => {
  it.each(examples)(
    "renders %s for gameplay and web code audiences",
    (type, data, gameplay, code) => {
      const event = makeEvent(type, 1, 0, data);
      expect(gameplayMessage(event, names)).toBe(gameplay);
      expect(codeMessage(event, names)).toBe(code);
    },
  );

  it("uses a safe Game label for missing or invalid player indices", () => {
    const event = makeEvent("TURN_ADVANCED", 1, null);
    expect(gameplayMessage(event, names)).toBe("Next turn: Game.");
    expect(gameplayMessage({ ...event, player: 99 }, names)).toBe("Next turn: Game.");
    expect(
      gameplayMessage(
        makeEvent("TOKEN_CAPTURED", 1, 0, { victim_player: 99, victim_token: "G1" }),
        names,
      ),
    ).toBe("P1 captures Game's G1.");
  });

  it("formats gameplay code both and off modes", () => {
    const event = makeEvent("DICE_ROLLED", 0, 0, { roll: 3 });
    expect(formatCommentary(event, "gameplay", "Gameplay text", "Code text")).toEqual([
      "Gameplay text",
    ]);
    expect(formatCommentary(event, "code", "Gameplay text", "Code text")).toEqual(["Code text"]);
    expect(formatCommentary(event, "both", "Gameplay text", "Code text")).toEqual([
      "[Gameplay] Gameplay text",
      "[Code] Code text",
    ]);
    expect(formatCommentary(event, "off", "Gameplay text", "Code text")).toEqual([]);
  });

  it("has safe output for every canonical event type", () => {
    const event: GameEvent = { type: "UNKNOWN", turn: 0, player: null, data: {} };
    expect(gameplayMessage(event, names)).toBe("UNKNOWN.");
    expect(codeMessage(event, names)).toBe("Web: UNKNOWN");
  });
});
