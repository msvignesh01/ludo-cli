import {
  BOOLEAN_RULE_KEYS,
  LOCKED_GEOMETRY_KEYS,
  MATCH_DEFAULTS,
  PRESETS,
  PROFILE_RULES,
  SPEED_DELAYS,
  isBlockades,
} from "./presets";
import type {
  MatchConfig,
  Mode,
  PlayerKind,
  Profile,
  ResolvedSetup,
  SetupInput,
} from "./types";

const LOCKED_GEOMETRY = new Set<string>(LOCKED_GEOMETRY_KEYS);
const SETUP_METADATA = new Set(["config", "names", "kinds", "seat", "autoplay", "no_color", "speed"]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function isInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value);
}

function isMode(value: unknown): value is Mode {
  return value === "quick" || value === "classic";
}

function isProfile(value: unknown): value is Profile {
  return value === "showcase" || value === "classic";
}

function cloneConfig(config: MatchConfig): MatchConfig {
  return {
    ...config,
    safe_tiles: [...config.safe_tiles],
    start_indices_2p: [...config.start_indices_2p],
    start_indices_4p: [...config.start_indices_4p],
  };
}

function validateConfig(config: MatchConfig): void {
  if (!isMode(config.mode)) throw new Error("mode must be 'quick' or 'classic'");
  if (!isProfile(config.profile)) throw new Error("profile must be 'showcase' or 'classic'");
  if (!isInteger(config.player_count) || config.player_count < 2 || config.player_count > 4) {
    throw new Error("player_count must be 2, 3, or 4");
  }
  if (!isInteger(config.tokens_per_player) || config.tokens_per_player < 1 || config.tokens_per_player > 4) {
    throw new Error("tokens_per_player must be an integer from 1 to 4");
  }
  if (!isInteger(config.max_turns) || config.max_turns <= 0) {
    throw new Error("max_turns must be a positive integer");
  }
  if (typeof config.auto_delay !== "number" || !Number.isFinite(config.auto_delay) || config.auto_delay < 0) {
    throw new Error("auto_delay must be a finite non-negative number");
  }
  if (config.seed !== null && !isInteger(config.seed)) {
    throw new Error("seed must be a safe integer or null");
  }
  if (!isBlockades(config.blockades)) {
    throw new Error("blockades must be 'none', 'strict', or 'safe_pair'");
  }
  if (!["gameplay", "code", "both", "off"].includes(config.commentary)) {
    throw new Error("commentary must be 'gameplay', 'code', 'both', or 'off'");
  }
  if (config.ui !== "cli" && config.ui !== "gui") {
    throw new Error("ui must be 'cli' or 'gui'");
  }
  for (const key of BOOLEAN_RULE_KEYS) {
    if (typeof config[key] !== "boolean") throw new Error(`${key} must be true or false`);
  }
}

export function buildConfig(
  mode: string,
  profile: string = "showcase",
  playerCount: number = 2,
  overrides: Record<string, unknown> = {},
): MatchConfig {
  if (!isMode(mode)) throw new Error("mode must be 'quick' or 'classic'");
  if (!isProfile(profile)) throw new Error("profile must be 'showcase' or 'classic'");
  if (!isInteger(playerCount) || playerCount < 2 || playerCount > 4) {
    throw new Error("player_count must be 2, 3, or 4");
  }
  if (!isRecord(overrides)) throw new Error("overrides must be a dictionary");
  const locked = Object.keys(overrides).filter((key) => LOCKED_GEOMETRY.has(key));
  if (locked.length > 0) {
    throw new Error(`board geometry cannot be overridden: ${locked.sort().join(", ")}`);
  }

  const base: MatchConfig = {
    ...PRESETS[mode],
    mode,
    profile,
    player_count: playerCount,
    ...MATCH_DEFAULTS,
    ...PROFILE_RULES[profile],
    max_turns: PRESETS[mode].default_max_turns,
  };
  const unknown = Object.keys(overrides).filter((key) => !(key in base));
  if (unknown.length > 0) {
    throw new Error(`unknown configuration keys: ${unknown.sort().join(", ")}`);
  }
  const merged = { ...base, ...overrides } as MatchConfig;
  validateConfig(merged);
  return cloneConfig(merged);
}

export function configFromDict(data: unknown): MatchConfig {
  if (!isRecord(data)) throw new Error("configuration must be a dictionary");
  if (!("mode" in data)) throw new Error("configuration requires a mode");
  const mode = data.mode;
  if (!isMode(mode)) throw new Error("mode must be 'quick' or 'classic'");
  const profile = data.profile ?? "showcase";
  const playerCount = data.player_count ?? 2;
  for (const key of LOCKED_GEOMETRY_KEYS) {
    if (key in data && JSON.stringify(data[key]) !== JSON.stringify(PRESETS[mode][key])) {
      throw new Error(`board geometry cannot be overridden: ${key}`);
    }
  }
  const overrides: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(data)) {
    if (key === "mode" || key === "profile" || key === "player_count" || LOCKED_GEOMETRY.has(key)) {
      continue;
    }
    overrides[key] = value;
  }
  return buildConfig(mode, profile as string, playerCount as number, overrides);
}

export function getStartIndices(config: MatchConfig): number[] {
  const key = config.player_count === 2 ? "start_indices_2p" : "start_indices_4p";
  return config[key].slice(0, config.player_count);
}

export function normalizePlayerNames(names: readonly unknown[], count: number): string[] {
  const normalized: string[] = [];
  for (let index = 0; index < count; index += 1) {
    const rawValue = names[index];
    if (rawValue !== undefined && typeof rawValue !== "string") {
      throw new Error("player names must be strings");
    }
    const raw = (rawValue ?? "").trim();
    let candidate = raw || `Player ${index + 1}`;
    if (normalized.includes(candidate)) {
      let suffix = index + 1;
      candidate = `${raw || `Player ${index + 1}`} (${suffix})`;
      while (normalized.includes(candidate)) {
        suffix += 1;
        candidate = `${raw || `Player ${index + 1}`} (${suffix})`;
      }
    }
    normalized.push(candidate);
  }
  return normalized;
}

export function normalizePlayerKinds(
  kinds: readonly unknown[],
  count: number,
  defaultKind: PlayerKind = "human",
): PlayerKind[] {
  if (kinds.length > count) throw new Error("too many seat kinds for the player count");
  const normalized: PlayerKind[] = [];
  for (const kind of kinds) {
    if (kind !== "human" && kind !== "bot") {
      throw new Error("seat kinds must be 'human' or 'bot'");
    }
    normalized.push(kind);
  }
  while (normalized.length < count) normalized.push(defaultKind);
  return normalized;
}

export function resolveSetup(sources: {
  wizard?: SetupInput;
  json?: SetupInput;
  url?: SetupInput;
}): ResolvedSetup {
  const settings: Record<string, unknown> = {};
  let names: unknown[] = [];
  let kinds: unknown[] = [];
  let autoplay = false;
  for (const source of [sources.wizard, sources.json, sources.url]) {
    if (!source) continue;
    if (!isRecord(source)) throw new Error("setup sources must be dictionaries");
    for (const [key, value] of Object.entries(source)) {
      if (SETUP_METADATA.has(key) || LOCKED_GEOMETRY.has(key) || value === null || value === undefined) {
        continue;
      }
      settings[key] = value;
    }
    if (source.names !== undefined) {
      if (!Array.isArray(source.names)) throw new Error("names must be a list");
      names = source.names;
    }
    const sourceKinds = source.kinds ?? source.seat;
    if (sourceKinds !== undefined) {
      if (!Array.isArray(sourceKinds)) throw new Error("seat kinds must be a list");
      kinds = sourceKinds;
    }
    if (source.autoplay !== undefined) {
      if (typeof source.autoplay !== "boolean") throw new Error("autoplay must be true or false");
      autoplay = source.autoplay;
    }
    if (settings.auto_delay === undefined && typeof source.speed === "string") {
      if (!(source.speed in SPEED_DELAYS)) throw new Error("speed must be 'slow', 'normal', or 'fast'");
      settings.auto_delay = SPEED_DELAYS[source.speed as keyof typeof SPEED_DELAYS];
    }
  }
  const mode = settings.mode ?? "quick";
  const profile = settings.profile ?? "showcase";
  const playerCount = settings.player_count ?? 2;
  if (typeof mode !== "string" || typeof profile !== "string" || typeof playerCount !== "number") {
    throw new Error("mode, profile, and player_count have invalid types");
  }
  const config = buildConfig(mode, profile, playerCount, settings);
  return {
    config,
    names: normalizePlayerNames(names, config.player_count),
    kinds: normalizePlayerKinds(kinds, config.player_count, autoplay ? "bot" : "human"),
    autoplay,
  };
}

export function parseSetupJson(text: string): SetupInput {
  if (new TextEncoder().encode(text).byteLength > 65_536) {
    throw new Error("configuration JSON exceeds the 64 KiB import limit");
  }
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch (error) {
    throw new Error(`could not load configuration: ${error instanceof Error ? error.message : "invalid JSON"}`);
  }
  if (!isRecord(data)) throw new Error("configuration must be a dictionary");
  const settings = { ...data };
  delete settings.config;
  return settings;
}
