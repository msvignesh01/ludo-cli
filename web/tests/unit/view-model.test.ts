import { describe, expect, it } from "vitest";
import fixture from "../../fixtures/geometry.json";
import { buildGuiViewModel } from "../../src/game/view-model";
import type { CanonicalSnapshot } from "../../src/game/types";

const snapshot = fixture.snapshot as unknown as CanonicalSnapshot;

describe("GUI view model", () => {
  it("matches the complete Python presentation model", () => {
    expect(buildGuiViewModel(snapshot)).toEqual(fixture.view_model);
  });

  it("preserves distinct identities for stacked track markers", () => {
    const model = buildGuiViewModel(snapshot);
    const stacked = model.markers.filter(
      (marker) => marker.location === "track" && marker.global_pos === 0,
    );
    expect(stacked.map((marker) => [marker.player_index, marker.token_idx, marker.cell])).toEqual([
      [0, 1, [0, 3]],
      [1, 0, [0, 3]],
    ]);
  });

  it("maps base, private-home, and finished tokens to distinct locations", () => {
    const model = buildGuiViewModel(snapshot);
    expect(new Set(model.markers.map((marker) => marker.location))).toEqual(
      new Set(["base", "track", "home", "finished"]),
    );
    expect(model.safe_tiles).toEqual(snapshot.config.safe_tiles);
    expect(model.start_tiles).toEqual([0, 7, 14]);
    expect(model.current_player).toBe(1);
    expect(model.turn_count).toBe(7);
    expect(model.last_event).toBe("Geometry fixture.");
  });
});
