import { describe, expect, it } from "vitest";
import { buildConfig } from "../../src/game/config";
import {
  applyMove,
  advanceTurn,
  createGame,
  declareMutualDraw,
  exportCanonicalState,
  formatPosition,
  getGlobalPos,
  getValidMoves,
  previewMove,
  processRoll,
  quitGame,
  recordBotDecision,
  rollDie,
} from "../../src/game/engine";
import { stableStringify } from "../../src/game/stable-json";
import type { InternalGame, MatchConfig } from "../../src/game/types";

function makeGame(
  overrides: Record<string, unknown> = {},
  count = 2,
  mode: "quick" | "classic" = "quick",
): InternalGame {
  const config = buildConfig(mode, "classic", count, overrides);
  const names = Array.from({ length: count }, (_, index) => `P${index + 1}`);
  return createGame(config, names, 42n);
}

function setSteps(game: InternalGame, player: number, token: number, steps: number): void {
  game.players[player]!.tokens[token]!.steps = steps;
}

function setAllHome(game: InternalGame, player: number): void {
  for (const token of game.players[player]!.tokens) {
    token.steps = game.config.home_finish;
  }
}

function replaceConfig(game: InternalGame, config: MatchConfig): InternalGame {
  return createGame(
    config,
    game.players.map((player) => player.name),
    42n,
    game.players.map((player) => player.kind),
  );
}

describe("canonical game creation", () => {
  it("creates independent players and the exact initial event", () => {
    const config = buildConfig("quick", "showcase", 3, { tokens_per_player: 3 });
    const game = createGame(config, ["Ada", "Grace", "Linus"], 42n, ["human", "bot", "human"]);
    config.safe_tiles.push(99);

    expect(game.players.map((player) => player.start_index)).toEqual([0, 7, 14]);
    expect(game.players.map((player) => player.kind)).toEqual(["human", "bot", "human"]);
    expect(game.players.map((player) => player.tokens.map((token) => token.label))).toEqual([
      ["R1", "R2", "R3"],
      ["G1", "G2", "G3"],
      ["Y1", "Y2", "Y3"],
    ]);
    expect(game.config.safe_tiles).toEqual([0, 7, 14, 21]);
    expect(exportCanonicalState(game)).toEqual({
      config: game.config,
      max_turns: 100,
      turn_count: 0,
      current_player: 0,
      consecutive_sixes: 0,
      status: "PLAYING",
      winner_index: null,
      draw_reason: null,
      finish_order: [],
      last_event: "Game started.",
      events: [
        {
          type: "GAME_STARTED",
          turn: 0,
          player: null,
          data: { mode: "quick", profile: "showcase" },
        },
      ],
      players: exportCanonicalState(game).players,
    });
  });

  it("exports only canonical keys and deep-clones mutable values", () => {
    const game = makeGame();
    const snapshot = exportCanonicalState(game);
    expect(Object.keys(snapshot)).toEqual([
      "config",
      "max_turns",
      "turn_count",
      "current_player",
      "consecutive_sixes",
      "status",
      "winner_index",
      "draw_reason",
      "finish_order",
      "last_event",
      "events",
      "players",
    ]);
    expect(Object.keys(snapshot.players[0]!)).toEqual([
      "index",
      "name",
      "kind",
      "color",
      "start_index",
      "captures_made",
      "tokens",
    ]);
    expect(Object.keys(snapshot.players[0]!.tokens[0]!)).toEqual(["label", "steps"]);

    snapshot.config.safe_tiles.push(99);
    snapshot.players[0]!.tokens[0]!.steps = 99;
    snapshot.events[0]!.data.mode = "changed";
    snapshot.events.push({ type: "GAME_QUIT", turn: 0, player: null, data: {} });
    const fresh = exportCanonicalState(game);
    expect(fresh.config.safe_tiles).not.toContain(99);
    expect(fresh.players[0]!.tokens[0]!.steps).toBe(-1);
    expect(fresh.events[0]!.data.mode).toBe("quick");
    expect(fresh.events).toHaveLength(1);
  });

  it("uses the isolated Python-compatible random stream", () => {
    const first = makeGame();
    const second = makeGame();
    expect(Array.from({ length: 20 }, () => rollDie(first))).toEqual(
      Array.from({ length: 20 }, () => rollDie(second)),
    );
    expect(exportCanonicalState(first)).toEqual(exportCanonicalState(second));
  });
});

describe("movement queries", () => {
  it("unlocks a base token only on a six", () => {
    const game = makeGame();
    expect(getValidMoves(game, 0, 5)).toEqual([]);
    expect(previewMove(game, 0, 0, 6)).toEqual({
      legal: true,
      label: "R1",
      token_idx: 0,
      old_steps: -1,
      new_steps: 0,
      old_position: "BASE",
      new_position: "T00",
      global_pos: 0,
      captured: [],
      reached_home: false,
      safe: true,
      wrapped: false,
      blockade_formed: false,
    });
    expect(previewMove(game, 0, 0, 5)).toEqual({
      legal: false,
      reason: "Move is not legal for this roll.",
    });
  });

  it("distinguishes the outer track, private lane, and home", () => {
    const game = makeGame();
    expect(getGlobalPos(14, 13, 28, 26)).toBe(27);
    expect(getGlobalPos(14, 14, 28, 26)).toBe(0);
    expect(getGlobalPos(0, 27, 28, 26)).toBeNull();
    expect(getGlobalPos(0, -1, 28, 26)).toBeNull();
    expect(formatPosition(game, 14, -1)).toBe("BASE");
    expect(formatPosition(game, 14, 26)).toBe("T12");
    expect(formatPosition(game, 14, 27)).toBe("H1");
    expect(formatPosition(game, 14, 31)).toBe("HOME");
  });

  it("rejects exact overshoot and clamps non-exact overshoot", () => {
    const game = makeGame();
    setSteps(game, 0, 0, 29);
    expect(getValidMoves(game, 0, 2)).toEqual([0]);
    expect(getValidMoves(game, 0, 3)).toEqual([]);

    const relaxed = replaceConfig(
      game,
      buildConfig("quick", "classic", 2, { exact_home_roll: false }),
    );
    setSteps(relaxed, 0, 0, 29);
    expect(applyMove(relaxed, 0, 6)).toMatchObject({ new_steps: 31, reached_home: true });
    expect(relaxed.players[0]!.tokens[0]!.steps).toBe(31);
  });

  it("loops at the home boundary until Kill-to-Enter is unlocked", () => {
    const game = makeGame({ kill_to_enter: true });
    setSteps(game, 0, 0, 26);
    const preview = previewMove(game, 0, 0, 1);
    expect(preview).toMatchObject({ legal: true, new_steps: 0, wrapped: true, global_pos: 0 });
    expect(applyMove(game, 0, 1)).toMatchObject({ new_steps: 0, wrapped: true });

    const unlocked = makeGame({ kill_to_enter: true });
    setSteps(unlocked, 0, 0, 26);
    setSteps(unlocked, 0, 1, 26);
    unlocked.players[0]!.captures_made = 1;
    expect(getValidMoves(unlocked, 0, 1)).toEqual([0, 1]);
    expect(applyMove(unlocked, 0, 1)).toMatchObject({ new_steps: 27, wrapped: false });
    expect(formatPosition(unlocked, 0, 27)).toBe("H1");
  });
});

describe("captures and blockades", () => {
  it("allows friendly stacks without capturing or blocking them", () => {
    const game = makeGame();
    setSteps(game, 0, 0, 2);
    setSteps(game, 0, 1, 3);
    expect(applyMove(game, 0, 1)).toMatchObject({ captured: [], blockade_formed: true });
    expect(game.players[0]!.tokens.map((token) => token.steps)).toEqual([3, 3]);

    const landing = makeGame();
    setSteps(landing, 0, 0, 8);
    setSteps(landing, 0, 1, 8);
    setSteps(landing, 1, 0, 22);
    landing.current_player = 1;
    expect(previewMove(landing, 1, 0, 2)).toMatchObject({
      legal: true,
      captured: [],
      blockade_formed: false,
    });
  });

  it("protects safe tiles unless safe tiles are disabled", () => {
    const safe = makeGame();
    setSteps(safe, 0, 0, 6);
    setSteps(safe, 1, 0, 21);
    expect(applyMove(safe, 0, 1).captured).toEqual([]);
    expect(safe.players[1]!.tokens[0]!.steps).toBe(21);

    const unsafe = makeGame({ safe_tiles_enabled: false });
    setSteps(unsafe, 1, 0, 14);
    expect(applyMove(unsafe, 0, 6).captured).toEqual(["P2's G1"]);
    expect(unsafe.players[1]!.tokens[0]!.steps).toBe(-1);
    expect(unsafe.players[0]!.captures_made).toBe(1);
  });

  it("captures one token or every token in an unprotected stack", () => {
    const single = makeGame();
    setSteps(single, 0, 0, 4);
    setSteps(single, 1, 0, 22);
    expect(applyMove(single, 0, 4).captured).toEqual(["P2's G1"]);

    const stacked = makeGame();
    setSteps(stacked, 0, 0, 4);
    setSteps(stacked, 1, 0, 22);
    setSteps(stacked, 1, 1, 22);
    expect(applyMove(stacked, 0, 4).captured).toEqual(["P2's G1", "P2's G2"]);
    expect(stacked.players[0]!.captures_made).toBe(2);
    expect(stacked.players[1]!.tokens.map((token) => token.steps)).toEqual([-1, -1]);
  });

  it.each([
    [2, 4],
    [1, 5],
  ])("blocks strict landings and crossed paths from step %i with roll %i", (start, roll) => {
    const game = makeGame({ blockades: "strict" });
    setSteps(game, 0, 0, start);
    setSteps(game, 1, 0, 20);
    setSteps(game, 1, 1, 20);
    expect(getValidMoves(game, 0, roll)).toEqual([]);
    expect(previewMove(game, 0, 0, roll)).toEqual({
      legal: false,
      reason: "A strict blockade blocks the path.",
    });
  });

  it("checks strict intermediate tiles", () => {
    const game = makeGame({ blockades: "strict" });
    setSteps(game, 0, 0, 1);
    setSteps(game, 1, 0, 18);
    setSteps(game, 1, 1, 18);
    expect(previewMove(game, 0, 0, 5).legal).toBe(false);
  });

  it("allows safe-pair passage but prevents landing captures", () => {
    const game = makeGame({ blockades: "safe_pair" });
    setSteps(game, 0, 0, 2);
    setSteps(game, 1, 0, 20);
    setSteps(game, 1, 1, 20);
    expect(getValidMoves(game, 0, 4)).toContain(0);
    expect(applyMove(game, 0, 4).captured).toEqual([]);
    expect(game.players[1]!.tokens.map((token) => token.steps)).toEqual([20, 20]);
  });

  it("captures stacks when blockades are disabled", () => {
    const game = makeGame({ blockades: "none" });
    setSteps(game, 0, 0, 2);
    setSteps(game, 1, 0, 20);
    setSteps(game, 1, 1, 20);
    expect(applyMove(game, 0, 4).captured).toHaveLength(2);
  });
});

describe("roll and turn transitions", () => {
  it("resets the six streak when a token reaches home on a six", () => {
    const game = makeGame();
    processRoll(game, 6);
    applyMove(game, 0, 6);
    setSteps(game, 0, 0, 25);
    setSteps(game, 0, 1, 30);
    const result = processRoll(game, 6);
    expect(result.valid_moves).toEqual([0]);
    const move = applyMove(game, 0, 6);
    expect(move.reached_home).toBe(true);
    expect(move.bonus_turn).toBe(true);
    expect(game.consecutive_sixes).toBe(0);
    expect(game.current_player).toBe(0);
  });

  it("grants only one capture bonus and advances once after a normal move", () => {
    const game = makeGame();
    setSteps(game, 0, 0, 2);
    setSteps(game, 1, 0, 22);
    processRoll(game, 6);
    expect(applyMove(game, 0, 6)).toMatchObject({ bonus_turn: true, captured: ["P2's G1"] });
    expect(game.current_player).toBe(0);
    expect(game.consecutive_sixes).toBe(1);
    expect(game.turn_count).toBe(0);

    setSteps(game, 0, 0, 8);
    setSteps(game, 0, 1, 31);
    setSteps(game, 1, 0, 31);
    processRoll(game, 1);
    expect(applyMove(game, 0, 1).bonus_turn).toBe(false);
    expect(game.current_player).toBe(1);
    expect(game.turn_count).toBe(1);
    expect(game.consecutive_sixes).toBe(0);
  });

  it("keeps capture and home bonus toggles independent", () => {
    const noCaptureBonus = makeGame({ bonus_on_capture: false });
    setSteps(noCaptureBonus, 0, 0, 4);
    setSteps(noCaptureBonus, 1, 0, 22);
    expect(applyMove(noCaptureBonus, 0, 4).bonus_turn).toBe(false);

    const noHomeBonus = makeGame({ bonus_on_home: false });
    setSteps(noHomeBonus, 0, 0, 29);
    expect(applyMove(noHomeBonus, 0, 2)).toMatchObject({ reached_home: true, bonus_turn: false });
  });

  it("forfeits the third six and can disable that penalty", () => {
    const game = makeGame();
    expect(processRoll(game, 6).event).toBe("SELECT_MOVE");
    expect(processRoll(game, 6).event).toBe("SELECT_MOVE");
    expect(processRoll(game, 6).event).toBe("TRIPLE_SIX_FORFEIT");
    expect(game).toMatchObject({ current_player: 1, turn_count: 1, consecutive_sixes: 0 });
    expect(game.events.map((event) => event.type)).toEqual([
      "GAME_STARTED",
      "DICE_ROLLED",
      "DICE_ROLLED",
      "DICE_ROLLED",
      "TRIPLE_SIX_FORFEIT",
      "TURN_ADVANCED",
    ]);

    const relaxed = makeGame({ triple_six_forfeit: false });
    expect([6, 6, 6].map(() => processRoll(relaxed, 6).event)).toEqual([
      "SELECT_MOVE",
      "SELECT_MOVE",
      "SELECT_MOVE",
    ]);
    expect(relaxed.consecutive_sixes).toBe(3);
  });

  it("auto-skips a roll with no legal move", () => {
    const game = makeGame();
    expect(processRoll(game, 1)).toEqual({ event: "NO_VALID_MOVES", valid_moves: [] });
    expect(game).toMatchObject({ current_player: 1, turn_count: 1, consecutive_sixes: 0 });
    expect(game.last_event).toBe("No legal move for roll 1; turn skipped.");
    expect(game.events.at(-2)).toEqual({
      type: "NO_VALID_MOVES",
      turn: 0,
      player: 0,
      data: { roll: 1 },
    });
    expect(game.events.at(-1)!.type).toBe("TURN_ADVANCED");
  });

  it("rejects illegal moves without mutating state", () => {
    const game = makeGame();
    const before = exportCanonicalState(game);
    expect(() => applyMove(game, 0, 1)).toThrow("Illegal move");
    expect(exportCanonicalState(game)).toEqual(before);
  });

  it("records the exact deterministic bot decision payload", () => {
    const game = makeGame({}, 2);
    recordBotDecision(game, 1, 4, "Safe tile");
    expect(game.events.at(-1)).toEqual({
      type: "BOT_DECISION",
      turn: 0,
      player: 0,
      data: { token: "R2", token_idx: 1, roll: 4, reason: "Safe tile" },
    });
  });
});

describe("terminal transitions", () => {
  it("wins immediately for a two-player non-podium match", () => {
    const game = makeGame();
    setSteps(game, 0, 0, 30);
    setSteps(game, 0, 1, 31);
    expect(applyMove(game, 0, 1)).toMatchObject({ won: true, bonus_turn: false });
    expect(game).toMatchObject({ status: "WON", winner_index: 0, turn_count: 0 });
    expect(game.finish_order).toEqual([0]);
    expect(game.last_event).toBe("P1 wins!");
  });

  it("continues podium matches until all but one player finish", () => {
    const game = makeGame({ podium_mode: true, tokens_per_player: 2 }, 3);
    setSteps(game, 0, 0, 30);
    setSteps(game, 0, 1, 31);
    expect(applyMove(game, 0, 1)).toMatchObject({ player_finished: true, won: false });
    expect(game.finish_order).toEqual([0]);
    expect(game.status).toBe("PLAYING");
    expect(game.current_player).toBe(1);
    expect(game.turn_count).toBe(1);

    setSteps(game, 1, 0, 30);
    setSteps(game, 1, 1, 31);
    expect(applyMove(game, 0, 1).won).toBe(true);
    expect(game.finish_order).toEqual([0, 1]);
    expect(game.status).toBe("WON");
    expect(game.winner_index).toBe(0);
    expect(game.current_player).toBe(1);
  });

  it("draws at the maximum turn limit with the exact reason", () => {
    const game = makeGame({ max_turns: 1 });
    advanceTurn(game);
    expect(game).toMatchObject({
      status: "DRAW",
      draw_reason: "Maximum turn limit reached",
      turn_count: 1,
      current_player: 1,
    });
    expect(game.last_event).toBe("Maximum turn limit reached");
    expect(game.events.at(-1)).toEqual({
      type: "GAME_DRAW",
      turn: 1,
      player: null,
      data: { reason: "Maximum turn limit reached" },
    });
  });

  it("declares mutual draw without advancing the turn", () => {
    const game = makeGame();
    declareMutualDraw(game);
    expect(game).toMatchObject({
      status: "DRAW",
      draw_reason: "Mutual agreement",
      last_event: "Mutual agreement",
      turn_count: 0,
    });
    expect(game.events.at(-1)!.data).toEqual({ reason: "Mutual agreement" });
  });

  it("quits cleanly with empty event data", () => {
    const game = makeGame();
    quitGame(game);
    expect(game).toMatchObject({ status: "QUIT", last_event: "Game quit." });
    expect(game.events.at(-1)).toEqual({ type: "GAME_QUIT", turn: 0, player: null, data: {} });
  });

  it("does not advance or mutate a terminal match", () => {
    const game = makeGame();
    quitGame(game);
    const before = exportCanonicalState(game);
    advanceTurn(game);
    expect(exportCanonicalState(game)).toEqual(before);
  });

  it("skips finished players when advancing", () => {
    const game = makeGame({ tokens_per_player: 1 }, 3);
    setAllHome(game, 1);
    advanceTurn(game);
    expect(game.current_player).toBe(2);
    expect(game.turn_count).toBe(1);
  });
});

describe("stable canonical JSON", () => {
  it("sorts object keys recursively without escaping Unicode", () => {
    expect(stableStringify({ z: [3, { b: 2, a: "Ludo雪" }], a: null })).toBe(
      '{"a":null,"z":[3,{"a":"Ludo雪","b":2}]}',
    );
  });
});
