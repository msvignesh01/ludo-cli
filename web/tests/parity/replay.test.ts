import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { decisionDetails } from "../../src/game/bot";
import { configFromDict } from "../../src/game/config";
import {
  advanceTurn,
  applyMove,
  createGame,
  declareMutualDraw,
  exportCanonicalState,
  getValidMoves,
  previewMove,
  processRoll,
  quitGame,
  recordBotDecision,
  rollDie,
} from "../../src/game/engine";
import { stableStringify } from "../../src/game/stable-json";
import type {
  CanonicalSnapshot,
  MatchConfig,
  MovePreview,
  MoveResult,
  PlayerKind,
  RollResult,
} from "../../src/game/types";

type Scenario = [
  "quick" | "classic",
  number,
  number,
  "showcase" | "classic",
  "none" | "strict" | "safe_pair",
  boolean,
  boolean,
  number,
  number,
];

type GameAction =
  | { type: "roll"; roll: number }
  | { type: "bot"; token_idx: number; reason: string }
  | { type: "move"; token_idx: number; roll: number };

interface GameRecord {
  schema: number;
  revision: string;
  scenario: Scenario;
  seed: number;
  config: MatchConfig;
  names: string[];
  kinds: PlayerKind[];
  actions: GameAction[];
  transition_hash: string;
  final: CanonicalSnapshot;
  stats: { rolls: number; moves: number; snapshots: number };
}

type SetupMutation =
  | { type: "token_steps"; player: number; token: number; steps: number }
  | { type: "captures_made"; player: number; value: number }
  | { type: "current_player"; value: number }
  | { type: "turn_count"; value: number }
  | { type: "consecutive_sixes"; value: number }
  | { type: "finish_order"; value: number[] };

type RuleAction =
  | { type: "preview"; player: number; token_idx: number; roll: number }
  | { type: "valid_moves"; player: number; roll: number }
  | { type: "roll"; roll: number }
  | { type: "turn"; roll: number; token_idx: number | null }
  | { type: "move"; token_idx: number; roll: number }
  | { type: "advance" }
  | { type: "draw" }
  | { type: "quit" };

interface RuleRecord {
  name: string;
  config: MatchConfig;
  names: string[];
  kinds: PlayerKind[];
  setup: SetupMutation[];
  action: RuleAction;
  expected: {
    preview?: MovePreview;
    roll_result?: RollResult;
    result?: MoveResult;
    valid_moves?: number[];
    snapshot: CanonicalSnapshot;
  };
}

interface RulesFixture {
  schema: number;
  revision: string;
  python: string;
  records: RuleRecord[];
}

function assertSame(actual: unknown, expected: unknown, context: string): void {
  const actualJson = stableStringify(actual);
  const expectedJson = stableStringify(expected);
  if (actualJson !== expectedJson) {
    throw new Error(`${context}\nExpected: ${expectedJson}\nActual:   ${actualJson}`);
  }
}

function applySetup(game: ReturnType<typeof createGame>, mutations: SetupMutation[]): void {
  for (const mutation of mutations) {
    if (mutation.type === "token_steps") {
      game.players[mutation.player]!.tokens[mutation.token]!.steps = mutation.steps;
    } else if (mutation.type === "captures_made") {
      game.players[mutation.player]!.captures_made = mutation.value;
    } else if (mutation.type === "current_player") {
      game.current_player = mutation.value;
    } else if (mutation.type === "turn_count") {
      game.turn_count = mutation.value;
    } else if (mutation.type === "consecutive_sixes") {
      game.consecutive_sixes = mutation.value;
    } else if (mutation.type === "finish_order") {
      game.finish_order = [...mutation.value];
    }
  }
}

const gameLines = readFileSync(new URL("../../fixtures/games.jsonl", import.meta.url), "utf8")
  .trim()
  .split("\n");

const rulesFixture = JSON.parse(
  readFileSync(new URL("../../fixtures/rules.json", import.meta.url), "utf8"),
) as RulesFixture;

describe("Python oracle replay", () => {
  it("replays all 1,080 games with zero transition mismatches", () => {
    expect(gameLines).toHaveLength(1080);
    const totals = {
      games: 0,
      wins: 0,
      draws: 0,
      rolls: 0,
      moves: 0,
      snapshots: 0,
      mismatches: 0,
    };
    let revision: string | null = null;

    for (const [lineIndex, line] of gameLines.entries()) {
      const record = JSON.parse(line) as GameRecord;
      const context = `game ${lineIndex + 1}, scenario ${record.scenario.join("/")}, seed ${record.seed}`;
      expect(record.schema).toBe(1);
      expect(record.revision).toMatch(/^[0-9a-f]{40}$/);
      revision ??= record.revision;
      expect(record.revision).toBe(revision);

      const config = configFromDict(record.config);
      assertSame(config, record.config, `${context}: invalid config`);
      const game = createGame(config, record.names, BigInt(record.seed), record.kinds);
      const hash = createHash("sha256");
      const actualStats = { rolls: 0, moves: 0, snapshots: 1 };
      let pendingRoll: number | null = null;
      hash.update(stableStringify(exportCanonicalState(game)), "utf8");

      for (const [actionIndex, action] of record.actions.entries()) {
        const actionContext = `${context}, action ${actionIndex + 1} (${action.type})`;
        if (action.type === "roll") {
          assertSame(rollDie(game), action.roll, `${actionContext}: die stream`);
          processRoll(game, action.roll);
          pendingRoll = action.roll;
          actualStats.rolls += 1;
        } else if (action.type === "bot") {
          if (pendingRoll === null) throw new Error(`${actionContext}: missing pending roll`);
          const validMoves = getValidMoves(game, game.current_player, pendingRoll);
          const decision = decisionDetails(game, game.current_player, pendingRoll, validMoves);
          assertSame(
            decision,
            { token_idx: action.token_idx, reason: action.reason },
            `${actionContext}: bot decision`,
          );
          recordBotDecision(game, action.token_idx, pendingRoll, action.reason);
        } else {
          applyMove(game, action.token_idx, action.roll);
          pendingRoll = null;
          actualStats.moves += 1;
        }
        hash.update(stableStringify(exportCanonicalState(game)), "utf8");
        actualStats.snapshots += 1;
      }

      const finalSnapshot = exportCanonicalState(game);
      hash.update(stableStringify(finalSnapshot), "utf8");
      actualStats.snapshots += 1;
      assertSame(hash.digest("hex"), record.transition_hash, `${context}: transition hash`);
      assertSame(finalSnapshot, record.final, `${context}: final snapshot`);
      assertSame(actualStats, record.stats, `${context}: replay stats`);
      expect(["WON", "DRAW"]).toContain(finalSnapshot.status);

      totals.games += 1;
      totals.wins += Number(finalSnapshot.status === "WON");
      totals.draws += Number(finalSnapshot.status === "DRAW");
      totals.rolls += actualStats.rolls;
      totals.moves += actualStats.moves;
      totals.snapshots += actualStats.snapshots;
    }

    expect(totals).toEqual({
      games: 1080,
      wins: 362,
      draws: 718,
      rolls: 93403,
      moves: 71678,
      snapshots: 238919,
      mismatches: 0,
    });
    console.log(
      "Web parity matrix: games=1080, wins=362, draws=718, " +
        "rolls=93403, moves=71678, snapshots=238919, mismatches=0",
    );
  }, 300000);

  it("matches every focused Python rule fixture", () => {
    expect(rulesFixture.schema).toBe(1);
    expect(rulesFixture.revision).toMatch(/^[0-9a-f]{40}$/);
    expect(rulesFixture.records.length).toBeGreaterThanOrEqual(16);

    for (const record of rulesFixture.records) {
      const game = createGame(
        configFromDict(record.config),
        record.names,
        BigInt(record.config.seed ?? 0),
        record.kinds,
      );
      applySetup(game, record.setup);
      const action = record.action;
      const actual: RuleRecord["expected"] = { snapshot: exportCanonicalState(game) };

      if (action.type === "preview") {
        actual.preview = previewMove(game, action.player, action.token_idx, action.roll);
      } else if (action.type === "valid_moves") {
        actual.valid_moves = getValidMoves(game, action.player, action.roll);
      } else if (action.type === "roll") {
        actual.roll_result = processRoll(game, action.roll);
      } else if (action.type === "turn") {
        actual.roll_result = processRoll(game, action.roll);
        actual.valid_moves = getValidMoves(game, game.current_player, action.roll);
        if (action.token_idx !== null) {
          actual.preview = previewMove(game, game.current_player, action.token_idx, action.roll);
          actual.result = applyMove(game, action.token_idx, action.roll);
        }
      } else if (action.type === "move") {
        actual.preview = previewMove(game, game.current_player, action.token_idx, action.roll);
        actual.result = applyMove(game, action.token_idx, action.roll);
      } else if (action.type === "advance") {
        advanceTurn(game);
      } else if (action.type === "draw") {
        declareMutualDraw(game);
      } else if (action.type === "quit") {
        quitGame(game);
      }

      actual.snapshot = exportCanonicalState(game);
      for (const key of ["preview", "roll_result", "result", "valid_moves", "snapshot"] as const) {
        if (key in record.expected) {
          assertSame(actual[key], record.expected[key], `rule fixture ${record.name}: ${key}`);
        }
      }
    }
  });
});
