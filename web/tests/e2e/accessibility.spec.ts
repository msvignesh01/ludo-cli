import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

const quickMatch = "/?mode=quick&profile=classic&players=2&tokens=1&seed=42&max_turns=120";

async function expectAccessible(page: Page): Promise<void> {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(
    results.violations.map((violation) => ({
      id: violation.id,
      impact: violation.impact,
      nodes: violation.nodes.map((node) => ({
        target: node.target,
        summary: node.failureSummary,
      })),
    })),
  ).toEqual([]);
}

function channels(color: string): number[] {
  const values = color.match(/[\d.]+/g)?.map(Number) ?? [];
  if (values.length < 3) throw new Error(`Could not read color: ${color}`);
  return values.slice(0, 3);
}

function luminance(color: string): number {
  const linear = channels(color).map((value) => {
    const channel = value / 255;
    return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * linear[0]! + 0.7152 * linear[1]! + 0.0722 * linear[2]!;
}

function contrast(foreground: string, background: string): number {
  const first = luminance(foreground);
  const second = luminance(background);
  return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
}

test("setup has no automated WCAG A/AA violations", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Start match" })).toBeEnabled();
  await expectAccessible(page);
});

test("match board and controls have no automated WCAG A/AA violations", async ({ page }) => {
  await page.goto(quickMatch);
  await page.getByRole("button", { name: "Start match" }).click();
  await expect(page.getByTestId("dom-board")).toBeVisible();
  await expectAccessible(page);
});

test("draw dialog has no automated WCAG A/AA violations", async ({ page }) => {
  await page.goto(quickMatch);
  await page.getByRole("button", { name: "Start match" }).click();
  await page.getByRole("button", { name: "Draw", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Confirm draw" })).toBeVisible();
  await expectAccessible(page);
});

test("native dialog traps focus and restores it after Escape", async ({ page }) => {
  await page.goto(quickMatch);
  await page.getByRole("button", { name: "Start match" }).click();
  const trigger = page.getByRole("button", { name: "Draw", exact: true });
  await trigger.focus();
  await page.keyboard.press("Enter");

  const dialog = page.getByRole("dialog", { name: "Confirm draw" });
  await expect(dialog).toBeVisible();
  for (let index = 0; index < 6; index += 1) {
    await page.keyboard.press("Tab");
    const active = await page.evaluate(() => {
      const element = document.activeElement;
      return element ? `${element.tagName}.${element.className}` : "none";
    });
    expect(
      await dialog.evaluate((element) => element.contains(document.activeElement)),
      `Tab ${index + 1} focused ${active}`,
    ).toBe(true);
  }
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(trigger).toBeFocused();
});

test("keyboard focus indicator meets non-text contrast", async ({ page }) => {
  await page.goto("/");
  const start = page.getByRole("button", { name: "Start match" });
  await expect(start).toBeEnabled();
  let keyboardFocused = false;
  for (let index = 0; index < 40; index += 1) {
    await page.keyboard.press("Tab");
    if (await start.evaluate((element) => element === document.activeElement)) {
      keyboardFocused = true;
      break;
    }
  }
  expect(keyboardFocused).toBe(true);
  const focus = await start.evaluate((element) => {
    const style = getComputedStyle(element);
    return {
      color: style.outlineColor,
      style: style.outlineStyle,
      width: Number.parseFloat(style.outlineWidth),
    };
  });
  expect(focus.style).not.toBe("none");
  expect(focus.width).toBeGreaterThanOrEqual(2);
  expect(contrast(focus.color, "rgb(255, 253, 248)")).toBeGreaterThanOrEqual(3);
});

test("fallback token labels meet text contrast", async ({ page }) => {
  await page.goto("/?mode=quick&profile=classic&players=4&tokens=1&seed=42&max_turns=120");
  await page.getByRole("button", { name: "Start match" }).click();
  const tokens = page.getByTestId("dom-board").locator("[class*=token]");
  await expect(tokens).toHaveCount(4);
  for (let index = 0; index < 4; index += 1) {
    const colors = await tokens.nth(index).evaluate((element) => {
      const style = getComputedStyle(element);
      return { foreground: style.color, background: style.backgroundColor };
    });
    expect(contrast(colors.foreground, colors.background)).toBeGreaterThanOrEqual(4.5);
  }
});

test("configuration errors are associated with the JSON field", async ({ page }) => {
  await page.goto("/");
  const input = page.getByRole("textbox", { name: "Configuration JSON", exact: true });
  await input.fill("{");
  await page.getByRole("button", { name: "Load configuration" }).click();
  const alert = page.getByRole("alert").filter({ hasText: "could not load configuration" });
  await expect(alert).toBeVisible();
  await expect(input).toHaveAttribute("aria-invalid", "true");
  const describedBy = await input.getAttribute("aria-describedby");
  expect(describedBy).toBeTruthy();
  await expect(page.locator(`#${describedBy}`)).toHaveText(/could not load configuration/);
});

test("draw handoff announces the next player", async ({ page }) => {
  await page.goto(quickMatch);
  await page.getByRole("button", { name: "Start match" }).click();
  await page.getByRole("button", { name: "Draw", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Confirm draw" });
  const announcement = dialog.locator("[aria-live='polite']");
  await expect(announcement).toContainText("Ada");
  await dialog.getByRole("button", { name: "Accept" }).click();
  await expect(announcement).toContainText("Grace");
});

test("terminal result is announced as a status", async ({ page }) => {
  await page.goto(quickMatch);
  await page.getByRole("button", { name: "Start match" }).click();
  await page.getByRole("button", { name: "Draw", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Confirm draw" });
  await dialog.getByRole("button", { name: "Accept" }).click();
  await dialog.getByRole("button", { name: "Accept" }).click();
  await expect(page.getByRole("status")).toContainText("Draw");
  await expect(page.getByRole("status")).toContainText("Mutual agreement");
});

test("reduced-motion preference removes interface transitions", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.getByLabel("Reduce motion", { exact: true })).toBeChecked();
  await page.getByRole("button", { name: "Start match" }).click();
  await expect(page.getByLabel("Reduce motion", { exact: true })).toBeChecked();
  const duration = await page
    .getByRole("button", { name: "Roll", exact: true })
    .evaluate((element) => getComputedStyle(element).transitionDuration);
  expect(Number.parseFloat(duration)).toBeLessThanOrEqual(0.001);
});

test("WebGL failure keeps the semantic board usable", async ({ page }) => {
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (
      this: HTMLCanvasElement,
      type: string,
      ...args: unknown[]
    ) {
      if (type === "webgl" || type === "webgl2" || type === "experimental-webgl") return null;
      return original.call(this, type, ...args);
    } as typeof HTMLCanvasElement.prototype.getContext;
  });
  await page.goto(quickMatch);
  await page.getByRole("button", { name: "Start match" }).click();
  await expect(page.getByText("Accessible board", { exact: true })).toBeVisible();
  await expect(page.getByTestId("dom-board")).toBeVisible();
  await expect(page.locator("canvas")).toHaveCount(0);
  await expectAccessible(page);
});
