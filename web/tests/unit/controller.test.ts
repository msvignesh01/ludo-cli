import { describe, expect, it, vi } from "vitest";
import { buildConfig } from "../../src/game/config";
import type { CommentaryMode, PlayerKind, Speed } from "../../src/game/types";
import { MatchController } from "../../src/match/controller";

function makeController(
  kinds: PlayerKind[] = ["human", "human"],
  options: {
    autoplay?: boolean;
    paused?: boolean;
    speed?: Speed;
    commentary?: CommentaryMode;
    reducedMotion?: boolean;
  } = {},
): MatchController {
  const config = buildConfig("quick", "classic", 2, { seed: 42 });
  return new MatchController(config, ["Ada", "Grace"], 42n, kinds, options);
}

describe("MatchController", () => {
  it("waits for a human to roll instead of advancing automatically", () => {
    const controller = makeController();

    expect(controller.runAutomatedTurn()).toBe(false);
    expect(controller.getSnapshot().turn_count).toBe(0);
    expect(controller.getSnapshot().events.map((event) => event.type)).toEqual(["GAME_STARTED"]);
    expect(controller.getPendingRoll()).toBeNull();
    expect(controller.getValidMoves()).toEqual([]);
  });

  it("exposes only legal token previews after a human roll", () => {
    const controller = makeController();

    expect(controller.rollHuman()).toEqual({ event: "SELECT_MOVE", valid_moves: [0, 1] });
    expect(controller.getPendingRoll()).toBe(6);
    expect(controller.getValidMoves()).toEqual([0, 1]);
    expect(controller.getPreviews().map((preview) => preview.legal)).toEqual([true, true]);
    expect(controller.getPreviews().map((preview) => preview.legal && preview.token_idx)).toEqual([
      0, 1,
    ]);
    expect(controller.getSnapshot().turn_count).toBe(0);
  });

  it("rejects an illegal token choice without mutating the match", () => {
    const controller = makeController();
    controller.rollHuman();
    const before = controller.getSnapshot();

    expect(controller.selectMove(9)).toBeNull();
    expect(controller.getSnapshot()).toEqual(before);
    expect(controller.getPendingRoll()).toBe(6);
  });

  it("performs exactly one deterministic bot roll, decision, and move", () => {
    const controller = makeController(["bot", "human"]);

    expect(controller.runAutomatedTurn()).toBe(true);
    const snapshot = controller.getSnapshot();
    expect(snapshot.events.map((event) => event.type)).toEqual([
      "GAME_STARTED",
      "DICE_ROLLED",
      "BOT_DECISION",
      "TOKEN_MOVED",
      "BONUS_TURN",
    ]);
    expect(snapshot.players[0]!.tokens[0]!.steps).toBe(0);
    expect(snapshot.current_player).toBe(0);
    expect(snapshot.turn_count).toBe(0);
    expect(controller.getPendingRoll()).toBeNull();
    expect(controller.getValidMoves()).toEqual([]);
  });

  it("autoplays a human seat without changing its player kind", () => {
    const controller = makeController(["human", "human"], { autoplay: true });

    expect(controller.runAutomatedTurn()).toBe(true);
    expect(controller.getSnapshot().players[0]!.kind).toBe("human");
    expect(controller.getSnapshot().events.some((event) => event.type === "BOT_DECISION")).toBe(
      true,
    );
  });

  it("blocks automated scheduling while paused but allows one manual step", () => {
    const controller = makeController(["bot", "human"], { paused: true });
    const before = controller.getSnapshot();

    expect(controller.runAutomatedTurn()).toBe(false);
    expect(controller.getSnapshot()).toEqual(before);
    expect(controller.step()).toBe(true);
    expect(controller.getSnapshot().events.at(-1)!.type).toBe("BONUS_TURN");
    expect(controller.isPaused()).toBe(true);
  });

  it("does not force a choice for a human seat through Step", () => {
    const controller = makeController();
    controller.rollHuman();

    expect(controller.step()).toBe(false);
    expect(controller.getPendingRoll()).toBe(6);
  });

  it("changes speed without changing canonical game state", () => {
    const controller = makeController(["bot", "human"]);
    const before = controller.getSnapshot();

    expect(controller.getScheduleDelayMs()).toBe(350);
    controller.setSpeed("fast");
    expect(controller.getScheduleDelayMs()).toBe(50);
    controller.setSpeed("slow");
    expect(controller.getScheduleDelayMs()).toBe(800);
    expect(controller.getSnapshot()).toEqual(before);
  });

  it("disables every turn action after a terminal draw", () => {
    const controller = makeController();
    controller.rollHuman();

    controller.declareDraw();
    const snapshot = controller.getSnapshot();
    expect(snapshot.status).toBe("DRAW");
    expect(snapshot.draw_reason).toBe("Mutual agreement");
    expect(snapshot.events.at(-1)).toMatchObject({
      type: "GAME_DRAW",
      data: { reason: "Mutual agreement" },
    });
    expect(controller.getPendingRoll()).toBeNull();
    expect(controller.getValidMoves()).toEqual([]);
    expect(controller.rollHuman()).toBeNull();
    expect(controller.selectMove(0)).toBeNull();
    expect(controller.runAutomatedTurn()).toBe(false);
    expect(controller.step()).toBe(false);
  });

  it("ends cleanly on quit and ignores later turn actions", () => {
    const controller = makeController(["bot", "human"]);
    controller.quit();
    const before = controller.getSnapshot();

    expect(before.status).toBe("QUIT");
    expect(before.last_event).toBe("Game quit.");
    expect(before.events.at(-1)).toEqual({
      type: "GAME_QUIT",
      turn: 0,
      player: null,
      data: {},
    });
    expect(controller.runAutomatedTurn()).toBe(false);
    expect(controller.step()).toBe(false);
    expect(controller.getSnapshot()).toEqual(before);
  });

  it("switches and drains commentary without changing canonical state", () => {
    const controller = makeController(["human", "human"], { commentary: "gameplay" });
    expect(controller.drainCommentary()).toEqual(["Match started."]);

    const before = controller.getSnapshot();
    controller.setCommentary("code");
    expect(controller.getSnapshot()).toEqual(before);
    controller.cycleCommentary();
    expect(controller.getCommentaryMode()).toBe("both");
    controller.rollHuman();
    expect(controller.drainCommentary()).toEqual([
      "[Gameplay] Ada rolls 6.",
      "[Code] Web: rollDie(game) -> processRoll(game, roll=6)",
    ]);

    controller.setCommentary("off");
    expect(controller.drainCommentary()).toEqual([]);
    expect(() => controller.setCommentary("invalid" as CommentaryMode)).toThrow("Commentary");
  });

  it("returns defensive snapshots and previews", () => {
    const controller = makeController();
    controller.rollHuman();
    const snapshot = controller.getSnapshot();
    const previews = controller.getPreviews();

    snapshot.players[0]!.tokens[0]!.steps = 99;
    const legal = previews[0]!;
    if (legal.legal) legal.captured.push("changed");
    expect(controller.getSnapshot().players[0]!.tokens[0]!.steps).toBe(-1);
    expect(controller.getPreviews()[0]).not.toEqual(legal);
  });

  it("notifies subscribers once per successful revision", () => {
    const controller = makeController();
    const listener = vi.fn();
    const unsubscribe = controller.subscribe(listener);

    controller.setSpeed("fast");
    controller.rollHuman();
    expect(listener).toHaveBeenCalledTimes(2);
    expect(controller.getRevision()).toBe(2);
    unsubscribe();
    controller.setSpeed("slow");
    expect(listener).toHaveBeenCalledTimes(2);
  });

  it("restores the same canonical state and resumes a pending choice", () => {
    const controller = makeController(["human", "bot"], {
      autoplay: true,
      speed: "fast",
      commentary: "both",
      reducedMotion: true,
    });
    controller.rollHuman();
    const config = controller.getSnapshot().config;
    const rng = controller.getRngState();
    const restored = MatchController.restore({
      schema: 1,
      saved_at: new Date().toISOString(),
      config,
      snapshot: controller.getSnapshot(),
      rng,
      pending_roll: controller.getPendingRoll(),
      valid_moves: controller.getValidMoves(),
      previews: controller.getPreviews(),
      preferences: {
        paused: false,
        autoplay: true,
        speed: "fast",
        commentary: "both",
        reduced_motion: true,
      },
    });

    expect(restored.getSnapshot()).toEqual(controller.getSnapshot());
    expect(restored.getPendingRoll()).toBe(6);
    expect(restored.getValidMoves()).toEqual([0, 1]);
    expect(restored.getScheduleDelayMs()).toBe(50);
    expect(restored.getCommentaryMode()).toBe("both");
    expect(restored.getAutoplay()).toBe(true);
    expect(restored.getReducedMotion()).toBe(true);

    expect(restored.selectMove(0)).toEqual(controller.selectMove(0));
    expect(restored.getSnapshot()).toEqual(controller.getSnapshot());
    expect(restored.rollHuman()).toEqual(controller.rollHuman());
    expect(restored.getSnapshot()).toEqual(controller.getSnapshot());
  });
});
