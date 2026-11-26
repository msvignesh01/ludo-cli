import { configFromDict } from "../game/config";
import { exportCanonicalState, getValidMoves, previewMove } from "../game/engine";
import { deserializeRandom } from "../game/rng";
import type { SerializedRandom } from "../game/rng";
import { stableStringify } from "../game/stable-json";
import type {
  CanonicalSnapshot,
  CommentaryMode,
  MatchConfig,
  MovePreview,
  Speed,
} from "../game/types";
import { MatchController, restoreGame } from "./controller";

export const MATCH_STORAGE_KEY = "ludo-showcase:match:v1";
export const MAX_EXPORT_BYTES = 65_536;
export const MAX_SAVE_BYTES = 1_048_576;

export interface SavedMatch {
  schema: 1;
  saved_at: string;
  config: MatchConfig;
  snapshot: CanonicalSnapshot;
  rng: SerializedRandom;
  pending_roll: number | null;
  valid_moves: number[];
  previews: MovePreview[];
  preferences: {
    paused: boolean;
    autoplay: boolean;
    speed: Speed;
    commentary: CommentaryMode;
    reduced_motion: boolean;
  };
}

export type LoadMatchResult =
  | { status: "empty" }
  | { status: "valid"; match: SavedMatch }
  | { status: "invalid"; reason: string };

const TOP_LEVEL_KEYS = new Set([
  "schema",
  "saved_at",
  "config",
  "snapshot",
  "rng",
  "pending_roll",
  "valid_moves",
  "previews",
  "preferences",
]);
const PREFERENCE_KEYS = new Set(["paused", "autoplay", "speed", "commentary", "reduced_motion"]);
const RNG_KEYS = new Set(["seed", "index", "words"]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function isInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value);
}

function requireKeys(record: Record<string, unknown>, allowed: Set<string>, label: string): void {
  const unknown = Object.keys(record).filter((key) => !allowed.has(key));
  if (unknown.length > 0)
    throw new Error(`${label} contains unknown fields: ${unknown.join(", ")}`);
}

function validateConfig(value: unknown): MatchConfig {
  try {
    return configFromDict(value);
  } catch (error) {
    throw new Error(
      `configuration is invalid: ${error instanceof Error ? error.message : "invalid"}`,
    );
  }
}

function validateRng(value: unknown): SerializedRandom {
  if (!isRecord(value)) throw new Error("RNG state must be an object");
  requireKeys(value, RNG_KEYS, "RNG state");
  try {
    deserializeRandom(value);
  } catch (error) {
    throw new Error(`RNG state is invalid: ${error instanceof Error ? error.message : "invalid"}`);
  }
  return value as unknown as SerializedRandom;
}

function validateSnapshot(value: unknown): CanonicalSnapshot {
  if (!isRecord(value)) throw new Error("snapshot must be an object");
  if (!Array.isArray(value.players) || value.players.length < 2 || value.players.length > 4) {
    throw new Error("snapshot players must contain 2, 3, or 4 seats");
  }
  if (!Array.isArray(value.events)) throw new Error("snapshot events must be a list");
  if (!Array.isArray(value.finish_order)) throw new Error("snapshot finish_order must be a list");
  const players = value.players;
  const events = value.events;
  const finishOrder = value.finish_order;
  if (!isInteger(value.turn_count) || value.turn_count < 0) {
    throw new Error("snapshot turn_count must be a non-negative integer");
  }
  if (!isInteger(value.current_player) || value.current_player < 0) {
    throw new Error("snapshot current_player must be a non-negative integer");
  }
  if (!isInteger(value.consecutive_sixes) || value.consecutive_sixes < 0) {
    throw new Error("snapshot consecutive_sixes must be a non-negative integer");
  }
  if (!["PLAYING", "WON", "DRAW", "QUIT"].includes(String(value.status))) {
    throw new Error("snapshot status is invalid");
  }
  if (value.winner_index !== null && !isInteger(value.winner_index)) {
    throw new Error("snapshot winner_index must be an integer or null");
  }
  if (value.draw_reason !== null && typeof value.draw_reason !== "string") {
    throw new Error("snapshot draw_reason must be a string or null");
  }
  if (typeof value.last_event !== "string") throw new Error("snapshot last_event must be a string");

  players.forEach((player, index) => {
    if (!isRecord(player)) throw new Error(`snapshot player ${index} must be an object`);
    if (player.index !== index) throw new Error("snapshot player indices must be sequential");
    if (typeof player.name !== "string") throw new Error("snapshot player names must be strings");
    if (player.kind !== "human" && player.kind !== "bot") {
      throw new Error("snapshot player kinds must be human or bot");
    }
    if (!isInteger(player.start_index) || player.start_index < 0) {
      throw new Error("snapshot player start indices must be non-negative integers");
    }
    if (!isInteger(player.captures_made) || player.captures_made < 0) {
      throw new Error("snapshot captures_made must be a non-negative integer");
    }
    if (!Array.isArray(player.tokens) || player.tokens.length < 1 || player.tokens.length > 4) {
      throw new Error("snapshot tokens must contain 1 to 4 tokens per player");
    }
    player.tokens.forEach((token, tokenIndex) => {
      if (!isRecord(token) || typeof token.label !== "string") {
        throw new Error(`snapshot token ${tokenIndex} is invalid`);
      }
      if (!isInteger(token.steps) || token.steps < -1) {
        throw new Error("snapshot token steps must be integers greater than or equal to -1");
      }
    });
  });

  events.forEach((event, index) => {
    if (!isRecord(event) || typeof event.type !== "string") {
      throw new Error(`snapshot event ${index} is invalid`);
    }
    if (!isInteger(event.turn) || event.turn < 0) {
      throw new Error("snapshot event turns must be non-negative integers");
    }
    if (event.player !== null && !isInteger(event.player)) {
      throw new Error("snapshot event players must be integers or null");
    }
    if (!isRecord(event.data)) throw new Error("snapshot event data must be an object");
  });

  finishOrder.forEach((playerIndex) => {
    if (!isInteger(playerIndex) || playerIndex < 0 || playerIndex >= players.length) {
      throw new Error("snapshot finish_order contains an invalid player index");
    }
  });
  if (new Set(finishOrder).size !== finishOrder.length) {
    throw new Error("snapshot finish_order must not contain duplicates");
  }
  return value as unknown as CanonicalSnapshot;
}

function validatePreferences(value: unknown): SavedMatch["preferences"] {
  if (!isRecord(value)) throw new Error("preferences must be an object");
  requireKeys(value, PREFERENCE_KEYS, "preferences");
  if (typeof value.paused !== "boolean" || typeof value.autoplay !== "boolean") {
    throw new Error("paused and autoplay preferences must be booleans");
  }
  if (value.speed !== "slow" && value.speed !== "normal" && value.speed !== "fast") {
    throw new Error("speed preference is invalid");
  }
  if (
    value.commentary !== "gameplay" &&
    value.commentary !== "code" &&
    value.commentary !== "both" &&
    value.commentary !== "off"
  ) {
    throw new Error("commentary preference is invalid");
  }
  if (typeof value.reduced_motion !== "boolean") {
    throw new Error("reduced_motion preference must be a boolean");
  }
  return value as unknown as SavedMatch["preferences"];
}

function validatePendingChoices(
  saved: Record<string, unknown>,
  snapshot: CanonicalSnapshot,
): { pendingRoll: number | null; validMoves: number[]; previews: MovePreview[] } {
  const pendingRoll = saved.pending_roll;
  if (pendingRoll !== null && (!isInteger(pendingRoll) || pendingRoll < 1 || pendingRoll > 6)) {
    throw new Error("pending roll must be an integer from 1 to 6 or null");
  }
  if (!Array.isArray(saved.valid_moves) || !Array.isArray(saved.previews)) {
    throw new Error("pending valid_moves and previews must be lists");
  }
  const validMoves = saved.valid_moves;
  const tokenCount = snapshot.config.tokens_per_player;
  if (
    validMoves.some(
      (tokenIndex) => !isInteger(tokenIndex) || tokenIndex < 0 || tokenIndex >= tokenCount,
    )
  ) {
    throw new Error("pending valid_moves contains an invalid token index");
  }
  if (new Set(validMoves).size !== validMoves.length) {
    throw new Error("pending valid_moves must not contain duplicates");
  }
  const previews = saved.previews as MovePreview[];
  if (pendingRoll === null) {
    if (validMoves.length !== 0 || previews.length !== 0) {
      throw new Error("pending choices require a pending roll");
    }
    return { pendingRoll: null, validMoves: [], previews: [] };
  }
  if (snapshot.status !== "PLAYING") throw new Error("pending choices require a playing match");
  if (snapshot.current_player >= snapshot.players.length) {
    throw new Error("snapshot current_player is outside the player list");
  }
  const game = restoreGame(snapshot, validateRng(saved.rng));
  const expectedMoves = getValidMoves(game, snapshot.current_player, pendingRoll);
  if (expectedMoves.length === 0) throw new Error("pending roll has no legal choice");
  const expectedPreviews = expectedMoves.map((tokenIndex) =>
    previewMove(game, snapshot.current_player, tokenIndex, pendingRoll),
  );
  if (stableStringify(validMoves) !== stableStringify(expectedMoves)) {
    throw new Error("pending valid_moves do not match the restored rules");
  }
  if (stableStringify(previews) !== stableStringify(expectedPreviews)) {
    throw new Error("pending previews do not match the restored rules");
  }
  return { pendingRoll, validMoves: [...validMoves], previews };
}

export function validateSavedMatch(value: unknown): SavedMatch {
  if (!isRecord(value)) throw new Error("saved match must be an object");
  requireKeys(value, TOP_LEVEL_KEYS, "saved match");
  if (value.schema !== 1) throw new Error("saved match schema must be 1");
  if (typeof value.saved_at !== "string" || Number.isNaN(Date.parse(value.saved_at))) {
    throw new Error("saved match timestamp is invalid");
  }
  const config = validateConfig(value.config);
  const snapshot = validateSnapshot(value.snapshot);
  if (!isRecord(snapshot.config)) throw new Error("snapshot configuration is invalid");
  if (stableStringify(snapshot.config) !== stableStringify(config)) {
    throw new Error("saved configuration does not match the snapshot");
  }
  if (snapshot.max_turns !== config.max_turns) {
    throw new Error("snapshot max_turns does not match the configuration");
  }
  if (snapshot.players.length !== config.player_count) {
    throw new Error("snapshot player count does not match the configuration");
  }
  if (snapshot.current_player >= snapshot.players.length) {
    throw new Error("snapshot current_player is outside the player list");
  }
  if (
    snapshot.winner_index !== null &&
    (snapshot.winner_index < 0 || snapshot.winner_index >= snapshot.players.length)
  ) {
    throw new Error("snapshot winner_index is outside the player list");
  }
  snapshot.players.forEach((player) => {
    if (player.tokens.length !== config.tokens_per_player) {
      throw new Error("snapshot token count does not match the configuration");
    }
    if (player.start_index >= config.track_len) {
      throw new Error("snapshot player start_index is outside the track");
    }
    if (player.tokens.some((token) => token.steps > config.home_finish)) {
      throw new Error("snapshot token steps exceed the home finish");
    }
  });
  snapshot.events.forEach((event) => {
    if (event.player !== null && (event.player < 0 || event.player >= snapshot.players.length)) {
      throw new Error("snapshot event player is outside the player list");
    }
  });

  const rng = validateRng(value.rng);
  const restored = restoreGame(snapshot, rng);
  if (stableStringify(exportCanonicalState(restored)) !== stableStringify(snapshot)) {
    throw new Error("snapshot does not match its canonical configuration and players");
  }
  const preferences = validatePreferences(value.preferences);
  const choices = validatePendingChoices(value, snapshot);
  return {
    schema: 1,
    saved_at: value.saved_at,
    config,
    snapshot,
    rng,
    pending_roll: choices.pendingRoll,
    valid_moves: choices.validMoves,
    previews: choices.previews,
    preferences,
  };
}

function createSavedMatch(controller: MatchController): SavedMatch {
  return {
    schema: 1,
    saved_at: new Date().toISOString(),
    config: controller.getSnapshot().config,
    snapshot: controller.getSnapshot(),
    rng: controller.getRngState(),
    pending_roll: controller.getPendingRoll(),
    valid_moves: controller.getValidMoves(),
    previews: controller.getPreviews(),
    preferences: {
      paused: controller.isPaused(),
      autoplay: controller.getAutoplay(),
      speed: controller.getSpeed(),
      commentary: controller.getCommentaryMode(),
      reduced_motion: controller.getReducedMotion(),
    },
  };
}

function browserStorage(storage?: Storage): Storage | null {
  if (storage) return storage;
  try {
    return globalThis.localStorage ?? null;
  } catch {
    return null;
  }
}

export function saveMatch(controller: MatchController, storage?: Storage): SavedMatch {
  const saved = createSavedMatch(controller);
  const target = browserStorage(storage);
  if (!target) return saved;
  const encoded = JSON.stringify(saved);
  if (new TextEncoder().encode(encoded).byteLength > MAX_SAVE_BYTES) return saved;
  try {
    target.setItem(MATCH_STORAGE_KEY, encoded);
  } catch {
    return saved;
  }
  return saved;
}

export function loadMatch(storage?: Storage): LoadMatchResult {
  const target = browserStorage(storage);
  if (!target) return { status: "empty" };
  let raw: string | null;
  try {
    raw = target.getItem(MATCH_STORAGE_KEY);
  } catch (error) {
    return {
      status: "invalid",
      reason: `browser storage is unavailable: ${error instanceof Error ? error.message : "access denied"}`,
    };
  }
  if (raw === null) return { status: "empty" };
  if (new TextEncoder().encode(raw).byteLength > MAX_SAVE_BYTES) {
    return { status: "invalid", reason: "saved match payload is oversized" };
  }
  try {
    return { status: "valid", match: validateSavedMatch(JSON.parse(raw)) };
  } catch (error) {
    return {
      status: "invalid",
      reason: error instanceof Error ? error.message : "saved match is invalid",
    };
  }
}

export function clearMatch(storage?: Storage): void {
  const target = browserStorage(storage);
  if (!target) return;
  try {
    target.removeItem(MATCH_STORAGE_KEY);
  } catch {
    return;
  }
}

export function exportMatch(controller: MatchController): string {
  const encoded = JSON.stringify(createSavedMatch(controller));
  if (new TextEncoder().encode(encoded).byteLength > MAX_EXPORT_BYTES) {
    throw new Error("Match export exceeds the 64 KiB import limit");
  }
  return encoded;
}

export function importMatch(text: string): LoadMatchResult {
  if (new TextEncoder().encode(text).byteLength > MAX_EXPORT_BYTES) {
    return { status: "invalid", reason: "match import exceeds the 64 KiB import limit" };
  }
  try {
    return { status: "valid", match: validateSavedMatch(JSON.parse(text)) };
  } catch (error) {
    return {
      status: "invalid",
      reason: error instanceof Error ? error.message : "saved match is invalid",
    };
  }
}
