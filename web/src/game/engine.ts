import { getStartIndices, normalizePlayerKinds, normalizePlayerNames } from "./config";
import { makeEvent } from "./events";
import { PLAYER_SPECS } from "./presets";
import {
  capturableTokens,
  computeTarget,
  formatPosition,
  getGlobalPos,
  getValidMoves,
  isSafeTile,
  killLocked,
  previewMove,
  strictPathBlocked,
  tokensAt,
} from "./queries";
import { createPythonRandom } from "./rng";
import {
  advanceTurn,
  applyMove,
  cloneEvent,
  declareMutualDraw,
  processRoll,
  quitGame,
  recordBotDecision,
} from "./transitions";
import type {
  CanonicalSnapshot,
  InternalGame,
  InternalPlayer,
  MatchConfig,
  PlayerKind,
} from "./types";

function cloneConfig(config: MatchConfig): MatchConfig {
  return {
    ...config,
    safe_tiles: [...config.safe_tiles],
    start_indices_2p: [...config.start_indices_2p],
    start_indices_4p: [...config.start_indices_4p],
  };
}

function randomSeed(): bigint {
  const words = new Uint32Array(2);
  if (typeof globalThis.crypto?.getRandomValues === "function") {
    globalThis.crypto.getRandomValues(words);
  } else {
    words[0] = Date.now() >>> 0;
    words[1] = (Date.now() * 2654435761) >>> 0;
  }
  return (BigInt(words[1]!) << 32n) | BigInt(words[0]!);
}

export function createGame(
  config: MatchConfig,
  playerNames: string[],
  seed?: bigint | null,
  playerKinds?: PlayerKind[],
): InternalGame {
  const matchConfig = cloneConfig(config);
  const names = normalizePlayerNames(playerNames, matchConfig.player_count);
  const kinds = normalizePlayerKinds(playerKinds ?? [], matchConfig.player_count);
  const starts = getStartIndices(matchConfig);
  const players: InternalPlayer[] = names.map((name, index) => {
    const spec = PLAYER_SPECS[index]!;
    return {
      index,
      name,
      kind: kinds[index]!,
      color: spec.color,
      color_hex: spec.hex,
      color_code: spec.ansi,
      prefix: spec.prefix,
      start_index: starts[index]!,
      captures_made: 0,
      tokens: Array.from({ length: matchConfig.tokens_per_player }, (_, tokenIndex) => ({
        token_idx: tokenIndex,
        label: `${spec.prefix}${tokenIndex + 1}`,
        steps: -1,
      })),
    };
  });
  const selectedSeed =
    seed ?? (matchConfig.seed === null ? randomSeed() : BigInt(matchConfig.seed));
  return {
    config: matchConfig,
    max_turns: matchConfig.max_turns,
    rng: createPythonRandom(selectedSeed),
    current_player: 0,
    turn_count: 0,
    consecutive_sixes: 0,
    status: "PLAYING",
    winner_index: null,
    draw_reason: null,
    finish_order: [],
    last_event: "Game started.",
    events: [
      makeEvent("GAME_STARTED", 0, null, {
        mode: matchConfig.mode,
        profile: matchConfig.profile,
      }),
    ],
    players,
  };
}

export function exportCanonicalState(game: InternalGame): CanonicalSnapshot {
  return {
    config: cloneConfig(game.config),
    max_turns: game.max_turns,
    turn_count: game.turn_count,
    current_player: game.current_player,
    consecutive_sixes: game.consecutive_sixes,
    status: game.status,
    winner_index: game.winner_index,
    draw_reason: game.draw_reason,
    finish_order: [...game.finish_order],
    last_event: game.last_event,
    events: game.events.map(cloneEvent),
    players: game.players.map((player) => ({
      index: player.index,
      name: player.name,
      kind: player.kind,
      color: player.color,
      start_index: player.start_index,
      captures_made: player.captures_made,
      tokens: player.tokens.map((token) => ({ label: token.label, steps: token.steps })),
    })),
  };
}

export function rollDie(game: InternalGame): number {
  return game.rng.randint(1, 6);
}

export {
  advanceTurn,
  applyMove,
  capturableTokens,
  computeTarget,
  declareMutualDraw,
  formatPosition,
  getGlobalPos,
  getValidMoves,
  isSafeTile,
  killLocked,
  previewMove,
  processRoll,
  quitGame,
  recordBotDecision,
  strictPathBlocked,
  tokensAt,
};
