import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  buildConfig,
  configFromDict,
  normalizePlayerKinds,
  normalizePlayerNames,
  parseSetupJson,
  resolveSetup,
} from "../../src/game/config";

describe("configuration", () => {
  it("locks Quick geometry", () => {
    expect(() => buildConfig("quick", "showcase", 2, { track_len: 52 })).toThrow(
      "board geometry cannot be overridden",
    );
  });

  it("uses Showcase defaults", () => {
    const config = buildConfig("quick");
    expect(config.blockades).toBe("safe_pair");
    expect(config.kill_to_enter).toBe(true);
    expect(config.podium_mode).toBe(true);
    expect(config.tokens_per_player).toBe(2);
    expect(config.home_finish).toBe(31);
  });

  it("applies URL overrides above JSON and wizard values", () => {
    const setup = resolveSetup({
      wizard: { mode: "quick", seed: 1 },
      json: { mode: "classic", seed: 2 },
      url: { seed: 42 },
    });
    expect(setup.config.mode).toBe("classic");
    expect(setup.config.seed).toBe(42);
    expect(setup.names).toEqual(["Player 1", "Player 2"]);
    expect(setup.kinds).toEqual(["human", "human"]);
  });

  it("keeps speed precedence consistent across wizard, JSON, and URL sources", () => {
    const setup = resolveSetup({
      wizard: { speed: "slow" },
      json: { speed: "fast" },
      url: { speed: "normal" },
    });
    expect(setup.config.auto_delay).toBe(0.35);
  });

  it("defaults omitted seats to bots when autoplay is enabled", () => {
    const setup = resolveSetup({ wizard: { player_count: 3, autoplay: true } });
    expect(setup.kinds).toEqual(["bot", "bot", "bot"]);
  });

  it("imports the existing Classic preset", () => {
    const config = configFromDict({
      mode: "classic",
      profile: "classic",
      player_count: 2,
      tokens_per_player: 4,
      blockades: "none",
      kill_to_enter: false,
      podium_mode: false,
      max_turns: 250,
      seed: 42,
    });
    expect(config.home_finish).toBe(56);
    expect(config.start_indices_2p).toEqual([0, 26]);
  });

  it.each(["showcase", "classic"])("accepts the %s JSON preset unchanged", (name) => {
    const text = readFileSync(new URL(`../../../configs/${name}.json`, import.meta.url), "utf8");
    const setup = resolveSetup({ json: parseSetupJson(text) });
    expect(setup.config.mode).toBe(name === "showcase" ? "quick" : "classic");
    expect(setup.config.player_count).toBe(name === "showcase" ? 4 : 2);
    expect(setup.config.max_turns).toBe(name === "showcase" ? 100 : 250);
    expect(setup.names).toHaveLength(setup.config.player_count);
    expect(setup.kinds).toHaveLength(setup.config.player_count);
  });

  it("rejects booleans and unknown keys in integer settings", () => {
    expect(() => buildConfig("quick", "showcase", 2, { max_turns: true })).toThrow(
      "max_turns must be a positive integer",
    );
    expect(() => buildConfig("quick", "showcase", 2, { mystery: 1 })).toThrow(
      "unknown configuration keys",
    );
  });

  it("rejects invalid ranges and non-finite delays", () => {
    expect(() => buildConfig("quick", "showcase", 5)).toThrow("player_count must be 2, 3, or 4");
    expect(() => buildConfig("quick", "showcase", 2, { max_turns: 0 })).toThrow(
      "max_turns must be a positive integer",
    );
    expect(() => buildConfig("quick", "showcase", 2, { auto_delay: Number.NaN })).toThrow(
      "auto_delay must be a finite non-negative number",
    );
  });

  it("normalizes names and seat kinds", () => {
    expect(normalizePlayerNames([" Red ", "", "Red"], 3)).toEqual(["Red", "Player 2", "Red (3)"]);
    expect(normalizePlayerKinds(["bot"], 3, "human")).toEqual(["bot", "human", "human"]);
    expect(() => normalizePlayerKinds(["bot", "bot"], 1)).toThrow("too many seat kinds");
    expect(() => normalizePlayerKinds(["alien"], 2)).toThrow("seat kinds must be");
  });

  it("caps imported JSON before parsing", () => {
    expect(() => parseSetupJson(`{"padding":"${"x".repeat(65_536)}"}`)).toThrow("64 KiB");
    expect(() => parseSetupJson("{")).toThrow("could not load configuration");
  });
});
