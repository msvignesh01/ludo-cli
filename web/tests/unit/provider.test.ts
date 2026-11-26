import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { buildConfig } from "../../src/game/config";
import { MatchController } from "../../src/match/controller";
import { MatchProvider, useMatch } from "../../src/match/MatchProvider";

function Consumer() {
  const { controller, revision } = useMatch();
  return createElement("span", null, `${revision}:${controller.getSnapshot().status}`);
}

describe("MatchProvider", () => {
  it("provides the active controller and its current revision", () => {
    const config = buildConfig("quick", "classic", 2, { seed: 42 });
    const controller = new MatchController(config, ["Ada", "Grace"], 42n);
    const markup = renderToStaticMarkup(
      createElement(MatchProvider, { controller }, createElement(Consumer)),
    );

    expect(markup).toBe("<span>0:PLAYING</span>");
  });
});
