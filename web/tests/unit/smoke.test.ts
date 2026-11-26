import { describe, expect, it } from "vitest";
import { PLAYER_SPECS } from "../../src/game/presets";

describe("web scaffold", () => {
  it("exposes four labeled player seats", () => {
    expect(PLAYER_SPECS.map((spec) => spec.prefix)).toEqual(["R", "G", "Y", "B"]);
  });
});
