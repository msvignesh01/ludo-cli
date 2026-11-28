import type { Blockades, MatchConfig, Mode, Profile } from "./types";

export interface PlayerSpec {
  color: "RED" | "GREEN" | "YELLOW" | "BLUE";
  hex: string;
  ansi: string;
  prefix: string;
}

export const PLAYER_SPECS: readonly PlayerSpec[] = [
  { color: "RED", hex: "#EF4444", ansi: "\u001b[91m", prefix: "R" },
  { color: "GREEN", hex: "#22C55E", ansi: "\u001b[92m", prefix: "G" },
  { color: "YELLOW", hex: "#EAB308", ansi: "\u001b[93m", prefix: "Y" },
  { color: "BLUE", hex: "#3B82F6", ansi: "\u001b[94m", prefix: "B" },
];

export const PRESETS: Record<
  Mode,
  Omit<
    MatchConfig,
    keyof ProfileRules | "max_turns" | "auto_delay" | "commentary" | "ui" | "seed" | "blockades"
  >
> = {
  quick: {
    mode: "quick",
    profile: "showcase",
    player_count: 2,
    track_len: 28,
    home_len: 4,
    tokens_per_player: 2,
    outer_last_step: 26,
    home_finish: 31,
    safe_tiles: [0, 7, 14, 21],
    start_indices_2p: [0, 14],
    start_indices_4p: [0, 7, 14, 21],
    default_max_turns: 100,
  },
  classic: {
    mode: "classic",
    profile: "showcase",
    player_count: 2,
    track_len: 52,
    home_len: 5,
    tokens_per_player: 4,
    outer_last_step: 50,
    home_finish: 56,
    safe_tiles: [0, 8, 13, 21, 26, 34, 39, 47],
    start_indices_2p: [0, 26],
    start_indices_4p: [0, 13, 26, 39],
    default_max_turns: 250,
  },
};

type ProfileRules = Pick<
  MatchConfig,
  | "blockades"
  | "kill_to_enter"
  | "podium_mode"
  | "exact_home_roll"
  | "triple_six_forfeit"
  | "safe_tiles_enabled"
  | "bonus_on_capture"
  | "bonus_on_home"
>;

export const PROFILE_RULES: Record<Profile, ProfileRules> = {
  showcase: {
    blockades: "safe_pair",
    kill_to_enter: true,
    podium_mode: true,
    exact_home_roll: true,
    triple_six_forfeit: true,
    safe_tiles_enabled: true,
    bonus_on_capture: true,
    bonus_on_home: true,
  },
  classic: {
    blockades: "none",
    kill_to_enter: false,
    podium_mode: false,
    exact_home_roll: true,
    triple_six_forfeit: true,
    safe_tiles_enabled: true,
    bonus_on_capture: true,
    bonus_on_home: true,
  },
};

export const MATCH_DEFAULTS = {
  auto_delay: 0.35,
  commentary: "gameplay",
  ui: "cli",
  seed: null,
} as const;

export const LOCKED_GEOMETRY_KEYS = [
  "track_len",
  "home_len",
  "outer_last_step",
  "home_finish",
  "safe_tiles",
  "start_indices_2p",
  "start_indices_4p",
  "default_max_turns",
] as const;

export const BOOLEAN_RULE_KEYS = [
  "kill_to_enter",
  "podium_mode",
  "exact_home_roll",
  "triple_six_forfeit",
  "safe_tiles_enabled",
  "bonus_on_capture",
  "bonus_on_home",
] as const;

export const SPEED_DELAYS: Record<"slow" | "normal" | "fast", number> = {
  slow: 0.8,
  normal: 0.35,
  fast: 0.05,
};

export function isBlockades(value: unknown): value is Blockades {
  return value === "none" || value === "strict" || value === "safe_pair";
}
