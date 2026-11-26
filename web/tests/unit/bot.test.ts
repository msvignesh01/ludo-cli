import { describe, expect, it } from "vitest";
import { buildConfig } from "../../src/game/config";
import { chooseMove, decisionDetails, scoreMove } from "../../src/game/bot";
import { createGame, recordBotDecision } from "../../src/game/engine";
import type { InternalGame } from "../../src/game/types";

function makeGame(overrides: Record<string, unknown> = {}): InternalGame {
  return createGame(buildConfig("quick", "classic", 2, overrides), ["P1", "P2"], 42n);
}

function setSteps(game: InternalGame, player: number, token: number, steps: number): void {
  game.players[player]!.tokens[token]!.steps = steps;
}

describe("deterministic bot policy", () => {
  it("prioritizes finishing home", () => {
    const game = makeGame();
    setSteps(game, 0, 0, 29);
    setSteps(game, 0, 1, 4);
    setSteps(game, 1, 0, 22);
    expect(chooseMove(game, 0, 2, [0, 1])).toBe(0);
    expect(decisionDetails(game, 0, 2, [0, 1])).toEqual({
      token_idx: 0,
      reason: "Finish Home",
    });
  });

  it("prioritizes capture over a safe landing", () => {
    const game = makeGame();
    setSteps(game, 0, 0, 4);
    setSteps(game, 0, 1, 3);
    setSteps(game, 1, 0, 22);
    expect(decisionDetails(game, 0, 4, [0, 1])).toEqual({ token_idx: 0, reason: "Capture" });
  });

  it("prioritizes the first capture that unlocks Kill-to-Enter", () => {
    const game = makeGame({ kill_to_enter: true });
    setSteps(game, 0, 0, 4);
    setSteps(game, 1, 0, 22);
    expect(decisionDetails(game, 0, 4, [0])).toEqual({
      token_idx: 0,
      reason: "Unlock Kill-to-Enter",
    });
    game.players[0]!.captures_made = 1;
    expect(decisionDetails(game, 0, 4, [0])).toEqual({ token_idx: 0, reason: "Capture" });
  });

  it("prioritizes a safe tile over advancing further", () => {
    const game = makeGame();
    setSteps(game, 0, 0, 3);
    setSteps(game, 0, 1, 8);
    expect(decisionDetails(game, 0, 4, [0, 1])).toEqual({ token_idx: 0, reason: "Safe tile" });
  });

  it("escapes danger before taking a slower safe advance", () => {
    const game = makeGame({ safe_tiles_enabled: false });
    setSteps(game, 0, 0, 4);
    setSteps(game, 0, 1, 2);
    setSteps(game, 1, 0, 12);
    expect(decisionDetails(game, 0, 6, [0, 1])).toEqual({
      token_idx: 0,
      reason: "Escape danger",
    });
  });

  it("advances furthest and uses the lowest token index for ties", () => {
    const game = makeGame();
    setSteps(game, 0, 0, 8);
    setSteps(game, 0, 1, 9);
    expect(decisionDetails(game, 0, 1, [0, 1])).toEqual({
      token_idx: 1,
      reason: "Advance furthest",
    });
    setSteps(game, 0, 1, 8);
    expect(chooseMove(game, 0, 1, [0, 1])).toBe(0);
  });

  it("counts wrapped progress using the configured track length", () => {
    const game = makeGame({ kill_to_enter: true, safe_tiles_enabled: false });
    setSteps(game, 0, 0, 26);
    setSteps(game, 0, 1, 20);
    expect(decisionDetails(game, 0, 1, [0, 1])).toEqual({
      token_idx: 0,
      reason: "Advance furthest",
    });
  });

  it("uses the exact lexicographic score tuple", () => {
    const game = makeGame();
    setSteps(game, 0, 0, 4);
    setSteps(game, 1, 0, 13);
    setSteps(game, 1, 1, 22);
    expect(scoreMove(game, 0, 0, 4)).toEqual([0, 1, 0, 0, 1, 8, 0]);
  });

  it("returns no decision for an empty legal list", () => {
    const game = makeGame();
    expect(chooseMove(game, 0, 3, [])).toBeNull();
    expect(decisionDetails(game, 0, 3, [])).toEqual({ token_idx: null, reason: "No legal moves" });
  });

  it("records a decision without changing token positions or turn ownership", () => {
    const game = makeGame();
    setSteps(game, 0, 0, 4);
    const before = game.players.map((player) => player.tokens.map((token) => token.steps));
    recordBotDecision(game, 0, 4, "Advance furthest");
    expect(game.events.at(-1)).toEqual({
      type: "BOT_DECISION",
      turn: 0,
      player: 0,
      data: { token: "R1", token_idx: 0, roll: 4, reason: "Advance furthest" },
    });
    expect(game.players.map((player) => player.tokens.map((token) => token.steps))).toEqual(before);
    expect(game.current_player).toBe(0);
  });
});
