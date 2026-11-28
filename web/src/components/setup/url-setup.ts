import { BOOLEAN_RULE_KEYS } from "../../game/presets";
import type { SetupInput } from "../../game/types";

function booleanValue(value: string): unknown {
  if (value === "true") return true;
  if (value === "false") return false;
  return value;
}

export function setupFromUrl(search: string): {
  source: SetupInput;
  reducedMotion: boolean;
} {
  const params = new URLSearchParams(search);
  const source: SetupInput = {};

  for (const key of ["mode", "profile", "blockades", "speed", "commentary", "ui"]) {
    const value = params.get(key);
    if (value !== null) source[key] = value;
  }
  for (const key of ["player_count", "tokens_per_player", "max_turns", "seed", "auto_delay"]) {
    const value = params.get(key);
    if (value !== null) source[key] = Number(value);
  }
  const players = params.get("players");
  if (players !== null) source.player_count = Number(players);
  const tokens = params.get("tokens");
  if (tokens !== null) source.tokens_per_player = Number(tokens);
  const maxTurns = params.get("max-turns");
  if (maxTurns !== null) source.max_turns = Number(maxTurns);
  for (const key of BOOLEAN_RULE_KEYS) {
    const value = params.get(key);
    if (value !== null) source[key] = booleanValue(value);
  }

  const autoplay = params.get("autoplay");
  if (autoplay !== null) source.autoplay = booleanValue(autoplay);
  const seat = params.get("seat");
  if (seat !== null) source.seat = seat.split(",").map((value) => value.trim());
  const names = params.get("names");
  if (names !== null) source.names = names.split("|").map((value) => value.trim());

  return {
    source,
    reducedMotion:
      params.get("reduced_motion") === "true" ||
      (typeof window !== "undefined" &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches),
  };
}
