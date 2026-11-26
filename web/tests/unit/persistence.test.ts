import { describe, expect, it } from "vitest";
import { buildConfig } from "../../src/game/config";
import { MatchController } from "../../src/match/controller";
import {
  MATCH_STORAGE_KEY,
  MAX_EXPORT_BYTES,
  MAX_SAVE_BYTES,
  clearMatch,
  exportMatch,
  importMatch,
  loadMatch,
  saveMatch,
} from "../../src/match/persistence";
import type { SavedMatch } from "../../src/match/persistence";

class MemoryStorage implements Storage {
  private readonly values = new Map<string, string>();

  get length(): number {
    return this.values.size;
  }

  clear(): void {
    this.values.clear();
  }

  getItem(key: string): string | null {
    return this.values.get(key) ?? null;
  }

  key(index: number): string | null {
    return Array.from(this.values.keys())[index] ?? null;
  }

  removeItem(key: string): void {
    this.values.delete(key);
  }

  setItem(key: string, value: string): void {
    this.values.set(key, value);
  }
}

function makeController(): MatchController {
  const config = buildConfig("quick", "classic", 2, { seed: 42 });
  return new MatchController(config, ["Ada", "Grace"], 42n, ["human", "bot"]);
}

function validResult(result: ReturnType<typeof loadMatch>): SavedMatch {
  if (result.status !== "valid")
    throw new Error(`Expected a valid save, received ${result.status}`);
  return result.match;
}

function changedJson(saved: SavedMatch, change: (value: Record<string, unknown>) => void): string {
  const value = JSON.parse(JSON.stringify(saved)) as Record<string, unknown>;
  change(value);
  return JSON.stringify(value);
}

describe("versioned match persistence", () => {
  it("saves and restores a pending human choice with the exact RNG stream", () => {
    const storage = new MemoryStorage();
    const controller = makeController();
    controller.rollHuman();
    controller.setSpeed("fast");
    controller.setCommentary("both");
    controller.setReducedMotion(true);

    const saved = saveMatch(controller, storage);
    expect(storage.getItem(MATCH_STORAGE_KEY)).not.toBeNull();
    expect(saved.schema).toBe(1);
    expect(saved.config).toEqual(controller.getSnapshot().config);
    expect(saved.snapshot.players.map((player) => [player.name, player.kind])).toEqual([
      ["Ada", "human"],
      ["Grace", "bot"],
    ]);

    const loaded = validResult(loadMatch(storage));
    const restored = MatchController.restore(loaded);
    expect(restored.getSnapshot()).toEqual(controller.getSnapshot());
    expect(restored.getPendingRoll()).toBe(6);
    expect(restored.getValidMoves()).toEqual([0, 1]);
    expect(restored.getPreviews()).toEqual(controller.getPreviews());
    expect(restored.getScheduleDelayMs()).toBe(50);
    expect(restored.getCommentaryMode()).toBe("both");
    expect(restored.getReducedMotion()).toBe(true);

    expect(restored.selectMove(0)).toEqual(controller.selectMove(0));
    expect(restored.getSnapshot()).toEqual(controller.getSnapshot());
    expect(restored.rollHuman()).toEqual(controller.rollHuman());
    expect(restored.getSnapshot()).toEqual(controller.getSnapshot());
  });

  it("round-trips the same validated record through export and import", () => {
    const controller = makeController();
    controller.rollHuman();
    const text = exportMatch(controller);
    const result = importMatch(text);

    expect(result.status).toBe("valid");
    if (result.status !== "valid") return;
    const restored = MatchController.restore(result.match);
    expect(restored.getSnapshot()).toEqual(controller.getSnapshot());
    expect(restored.getPendingRoll()).toBe(6);
  });

  it("reports an empty store without throwing", () => {
    expect(loadMatch(new MemoryStorage())).toEqual({ status: "empty" });
  });

  it("rejects an incompatible schema", () => {
    const saved = saveMatch(makeController(), new MemoryStorage());
    const result = importMatch(changedJson(saved, (value) => (value.schema = 2)));

    expect(result.status).toBe("invalid");
    if (result.status === "invalid") expect(result.reason).toContain("schema");
  });

  it("rejects invalid RNG words", () => {
    const saved = saveMatch(makeController(), new MemoryStorage());
    const result = importMatch(
      changedJson(saved, (value) => {
        const rng = value.rng as { words: number[] };
        rng.words[0] = -1;
      }),
    );

    expect(result.status).toBe("invalid");
    if (result.status === "invalid") expect(result.reason).toContain("RNG");
  });

  it("rejects a malformed configuration", () => {
    const saved = saveMatch(makeController(), new MemoryStorage());
    const result = importMatch(
      changedJson(saved, (value) => {
        const config = value.config as Record<string, unknown>;
        config.mode = "broken";
      }),
    );

    expect(result.status).toBe("invalid");
    if (result.status === "invalid") expect(result.reason).toContain("configuration");
  });

  it("rejects a snapshot that disagrees with its configuration", () => {
    const saved = saveMatch(makeController(), new MemoryStorage());
    const result = importMatch(
      changedJson(saved, (value) => {
        const snapshot = value.snapshot as { config: Record<string, unknown> };
        snapshot.config.player_count = 4;
      }),
    );

    expect(result.status).toBe("invalid");
  });

  it("rejects pending choices that do not match the restored rules", () => {
    const controller = makeController();
    controller.rollHuman();
    const saved = saveMatch(controller, new MemoryStorage());
    const result = importMatch(
      changedJson(saved, (value) => {
        const previews = value.previews as Array<Record<string, unknown>>;
        previews[0]!.new_steps = 99;
      }),
    );

    expect(result.status).toBe("invalid");
    if (result.status === "invalid") expect(result.reason).toContain("pending");
  });

  it("rejects a pending roll that has no legal choice", () => {
    const config = buildConfig("quick", "classic", 2, { seed: 0 });
    const controller = new MatchController(config, ["Ada", "Grace"], 0n, ["human", "bot"]);
    controller.rollHuman();
    const saved = saveMatch(controller, new MemoryStorage());
    const result = importMatch(changedJson(saved, (value) => (value.pending_roll = 4)));

    expect(result.status).toBe("invalid");
    if (result.status === "invalid") expect(result.reason).toContain("pending");
  });

  it("rejects corrupt JSON and oversized imports without throwing", () => {
    const storage = new MemoryStorage();
    storage.setItem(MATCH_STORAGE_KEY, "{not json");
    expect(loadMatch(storage).status).toBe("invalid");

    const oversized = importMatch(" ".repeat(MAX_EXPORT_BYTES + 1));
    expect(oversized.status).toBe("invalid");
    if (oversized.status === "invalid") expect(oversized.reason).toContain("64 KiB");
  });

  it("rejects an oversized browser save", () => {
    const storage = new MemoryStorage();
    storage.setItem(MATCH_STORAGE_KEY, " ".repeat(MAX_SAVE_BYTES + 1));
    const result = loadMatch(storage);

    expect(result.status).toBe("invalid");
    if (result.status === "invalid") expect(result.reason).toContain("oversized");
  });

  it("clears only its own saved match", () => {
    const storage = new MemoryStorage();
    storage.setItem("unrelated", "keep");
    saveMatch(makeController(), storage);

    clearMatch(storage);
    expect(storage.getItem(MATCH_STORAGE_KEY)).toBeNull();
    expect(storage.getItem("unrelated")).toBe("keep");
  });

  it("contains browser storage access failures", () => {
    const controller = makeController();
    const unavailable = {
      getItem(): string {
        throw new Error("storage denied");
      },
      setItem(): void {
        throw new Error("storage denied");
      },
    } as unknown as Storage;

    expect(() => saveMatch(controller, unavailable)).not.toThrow();
    const result = loadMatch(unavailable);
    expect(result.status).toBe("invalid");
    if (result.status === "invalid") expect(result.reason).toContain("storage");
  });
});
