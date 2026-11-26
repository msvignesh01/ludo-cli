import { describe, expect, it } from "vitest";
import fixture from "../../fixtures/geometry.json";
import { buildConfig } from "../../src/game/config";
import { buildBoardGeometry } from "../../src/game/geometry";

const cases = [
  ["quick", 2, "quick2p"],
  ["quick", 3, "quick3p"],
  ["quick", 4, "quick4p"],
  ["classic", 2, "classic2p"],
  ["classic", 3, "classic3p"],
  ["classic", 4, "classic4p"],
] as const;

describe("locked geometry", () => {
  it.each(cases)("matches the Python %s %iP board", (mode, count, key) => {
    const config = buildConfig(mode, "classic", count);
    expect(buildBoardGeometry(config)).toEqual(fixture[key]);
  });

  it("derives every route cell from the active track length", () => {
    for (const [mode, count] of cases) {
      const geometry = buildBoardGeometry(buildConfig(mode, "classic", count));
      expect(geometry.track_cells).toHaveLength(buildConfig(mode, "classic", count).track_len);
      expect(geometry.home_cells).toHaveLength(count);
      expect(geometry.yard_boxes).toHaveLength(count);
    }
  });
});
