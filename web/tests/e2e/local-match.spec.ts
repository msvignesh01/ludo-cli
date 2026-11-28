import { expect, test } from "@playwright/test";

const quickMatch = "/?mode=quick&profile=classic&players=2&tokens=1&seed=42&max_turns=120";

test("keyboard user can roll and choose a legal token", async ({ page }) => {
  await page.goto(quickMatch);
  await page.getByRole("button", { name: "Start match" }).click();

  const roll = page.getByRole("button", { name: "Roll", exact: true });
  await roll.focus();
  await page.keyboard.press("Enter");
  const choice = page.getByRole("button", { name: /Move R1/ });
  await expect(choice).toBeVisible();
  await choice.focus();
  await page.keyboard.press("Enter");

  await expect(choice).toHaveCount(0);
  await expect(roll).toBeEnabled();
  await expect(page.getByTestId("dom-board")).toHaveAttribute("data-mode", "quick");
});

test("3D presentation stacks above fallback board tokens", async ({ page }) => {
  await page.goto(quickMatch);
  await page.getByRole("button", { name: "Start match" }).click();
  await expect(page.getByText("3D presentation", { exact: true })).toBeVisible();

  const layers = await page.evaluate(() => {
    const canvas = document.querySelector("canvas");
    const canvasLayer = canvas?.parentElement?.parentElement;
    const token = document.querySelector("[class*=token]");
    if (!(canvasLayer instanceof HTMLElement) || !(token instanceof HTMLElement)) {
      throw new Error("3D board layers are missing");
    }
    return {
      canvas: Number(getComputedStyle(canvasLayer).zIndex),
      token: Number(getComputedStyle(token).zIndex),
    };
  });
  expect(layers.canvas).toBeGreaterThan(layers.token);
});

test("four bots autoplay to a terminal result", async ({ page }) => {
  await page.goto(
    "/?mode=quick&profile=classic&players=4&tokens=1&seed=42&max_turns=80&autoplay=true&speed=fast",
  );
  await page.getByRole("button", { name: "Start match" }).click();

  await expect(page.getByRole("heading", { name: "Match result" })).toBeVisible({
    timeout: 20_000,
  });
  await expect(page.getByRole("button", { name: "Roll", exact: true })).toBeDisabled();
  await expect(page.getByTestId("turn-count")).not.toHaveText("0");
});

test("pause stops the timer and Step performs one action", async ({ page }) => {
  await page.goto(`${quickMatch}&seat=bot,bot&speed=fast`);
  await page.getByRole("button", { name: "Start match" }).click();
  const rollCount = page.getByTestId("roll-count");
  await expect(rollCount).not.toHaveText("0", { timeout: 10_000 });

  await page.getByRole("button", { name: "Pause", exact: true }).click();
  const pausedCount = await rollCount.textContent();
  await page.waitForTimeout(300);
  await expect(rollCount).toHaveText(pausedCount ?? "0");
  await page.getByRole("button", { name: "Step", exact: true }).click();
  await expect(rollCount).not.toHaveText(pausedCount ?? "0");
  await expect(page.getByRole("button", { name: "Resume", exact: true })).toBeVisible();
});

test("commentary mode changes the transcript without changing the turn", async ({ page }) => {
  await page.goto(quickMatch);
  await page.getByRole("button", { name: "Start match" }).click();
  await page.getByLabel("Commentary", { exact: true }).selectOption("code");
  await page.getByRole("button", { name: "Roll", exact: true }).click();

  await expect(page.getByTestId("commentary-log")).toContainText(
    "Web: rollDie(game) -> processRoll(game, roll=6)",
  );
  await expect(page.getByTestId("turn-count")).toHaveText("0");
});

test("draw decline resumes and mutual acceptance ends the match", async ({ page }) => {
  await page.goto(quickMatch);
  await page.getByRole("button", { name: "Start match" }).click();
  await page.getByRole("button", { name: "Draw", exact: true }).click();

  const dialog = page.getByRole("dialog", { name: "Confirm draw" });
  await expect(dialog).toContainText("Ada");
  await dialog.getByRole("button", { name: "Decline" }).click();
  await expect(dialog).toHaveCount(0);
  await expect(page.getByTestId("turn-count")).toHaveText("0");

  await page.getByRole("button", { name: "Draw", exact: true }).click();
  await dialog.getByRole("button", { name: "Accept" }).click();
  await expect(dialog).toContainText("Grace");
  await dialog.getByRole("button", { name: "Accept" }).click();

  await expect(page.getByRole("heading", { name: "Match result" })).toBeVisible();
  await expect(page.getByTestId("result-status")).toHaveText("Draw");
  await expect(page.getByTestId("result-reason")).toHaveText("Mutual agreement");
});

test("quit asks for confirmation and emits a terminal result", async ({ page }) => {
  await page.goto(quickMatch);
  await page.getByRole("button", { name: "Start match" }).click();
  await page.getByRole("button", { name: "Quit", exact: true }).click();

  const dialog = page.getByRole("dialog", { name: "Quit match?" });
  await dialog.getByRole("button", { name: "Keep playing" }).click();
  await expect(dialog).toHaveCount(0);
  await page.getByRole("button", { name: "Quit", exact: true }).click();
  await dialog.getByRole("button", { name: "Quit match", exact: true }).click();

  await expect(page.getByTestId("result-status")).toHaveText("Quit");
  await expect(page.getByTestId("result-reason")).toHaveText("Game quit.");
});

test("JSON import keeps URL settings at higher precedence", async ({ page }) => {
  await page.goto(quickMatch);
  await page.getByLabel("Configuration JSON", { exact: true }).fill(
    JSON.stringify({
      mode: "classic",
      profile: "classic",
      player_count: 2,
      tokens_per_player: 1,
      seed: 7,
      max_turns: 120,
    }),
  );
  await page.getByRole("button", { name: "Load configuration" }).click();

  await expect(page.getByTestId("resolved-mode")).toHaveText("Quick");
  await page.getByRole("button", { name: "Start match" }).click();
  await expect(page.getByTestId("dom-board")).toHaveAttribute("data-mode", "quick");
});

test("a pending choice survives a browser reload", async ({ page }) => {
  await page.goto(quickMatch);
  await page.getByRole("button", { name: "Start match" }).click();
  await page.getByRole("button", { name: "Roll", exact: true }).click();
  await expect(page.getByRole("button", { name: /Move R1/ })).toBeVisible();
  await expect
    .poll(() => page.evaluate(() => localStorage.getItem("ludo-showcase:match:v1") !== null))
    .toBe(true);

  await page.reload();
  await page.getByRole("button", { name: "Resume match" }).click();
  await expect(page.getByRole("button", { name: /Move R1/ })).toBeVisible();
  await expect(page.getByTestId("roll-count")).toHaveText("1");
});

test("corrupt saved data is explained and can be reset", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("ludo-showcase:match:v1", "{broken");
  });
  await page.goto("/");

  const appAlert = page.getByRole("main").getByRole("alert");
  await expect(appAlert).toContainText(/saved match/i);
  await page.getByRole("button", { name: "Reset saved data" }).click();
  await expect(appAlert).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Start match" })).toBeVisible();
});

test("result actions export the match and return to setup", async ({ page }) => {
  await page.goto(quickMatch);
  await page.getByRole("button", { name: "Start match" }).click();
  await page.getByRole("button", { name: "Draw", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Confirm draw" });
  await dialog.getByRole("button", { name: "Accept" }).click();
  await dialog.getByRole("button", { name: "Accept" }).click();

  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export match" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("ludo-match.json");
  await page.getByRole("button", { name: "New match" }).click();
  await expect(page.getByRole("button", { name: "Start match" })).toBeVisible();
});

test("mobile match layout does not overflow horizontally", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(quickMatch);
  await page.getByRole("button", { name: "Start match" }).click();

  await expect(page.getByTestId("dom-board")).toBeVisible();
  const sizes = await page.evaluate(() => ({
    viewport: window.innerWidth,
    content: document.documentElement.scrollWidth,
  }));
  expect(sizes.content).toBeLessThanOrEqual(sizes.viewport);
});

test("starting immediately honors URL setup", async ({ page }) => {
  await page.addInitScript(() => {
    const pending: Array<() => void> = [];
    const runMicrotask = window.queueMicrotask.bind(window);
    window.queueMicrotask = (callback) => {
      if (callback.toString().includes("setupFromUrl")) pending.push(callback);
      else runMicrotask(callback);
    };
    Object.defineProperty(window, "__ludoPendingMicrotasks", { value: () => pending.length });
    Object.defineProperty(window, "__flushLudoMicrotasks", {
      value: () => {
        for (const callback of pending.splice(0)) runMicrotask(callback);
      },
    });
  });
  await page.goto(quickMatch, { waitUntil: "domcontentloaded" });

  const start = page.getByRole("button", { name: "Start match" });
  const click = start.click();
  await expect
    .poll(() =>
      page.evaluate(() => {
        const target = window as unknown as { __ludoPendingMicrotasks: () => number };
        return target.__ludoPendingMicrotasks();
      }),
    )
    .toBeGreaterThan(0);
  await page.evaluate(() => {
    const target = window as unknown as { __flushLudoMicrotasks: () => void };
    target.__flushLudoMicrotasks();
  });
  await click;

  await expect(page.getByTestId("dom-board")).toBeVisible();
  await expect(page.getByText("Turn 0 / 120", { exact: true })).toBeVisible();
  await expect(page.getByTestId("dom-board").getByText("R2", { exact: true })).toHaveCount(0);
});

test("invalid URL input is explained instead of crashing", async ({ page }) => {
  await page.goto("/?mode=quick&players=9");
  await expect(page.getByRole("main").getByRole("alert")).toContainText("player_count");
  await expect(page.getByRole("button", { name: "Start match" })).toBeVisible();
});
