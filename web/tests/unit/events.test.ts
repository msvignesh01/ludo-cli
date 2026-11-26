import { describe, expect, it } from "vitest";
import { EVENT_TYPES, makeEvent } from "../../src/game/events";

describe("event contract", () => {
  it("creates the exact canonical event shape", () => {
    expect(makeEvent("GAME_STARTED", 0, null, { mode: "quick", profile: "showcase" })).toEqual({
      type: "GAME_STARTED",
      turn: 0,
      player: null,
      data: { mode: "quick", profile: "showcase" },
    });
  });

  it("exposes all fourteen Python event names", () => {
    expect(EVENT_TYPES).toEqual([
      "GAME_STARTED",
      "DICE_ROLLED",
      "NO_VALID_MOVES",
      "TRIPLE_SIX_FORFEIT",
      "BOT_DECISION",
      "TOKEN_MOVED",
      "TOKEN_CAPTURED",
      "BLOCKADE_FORMED",
      "PLAYER_FINISHED",
      "BONUS_TURN",
      "TURN_ADVANCED",
      "GAME_WON",
      "GAME_DRAW",
      "GAME_QUIT",
    ]);
  });

  it("rejects unknown event types", () => {
    expect(() => makeEvent("UNKNOWN", 0, null)).toThrow("unknown event type");
  });
});
