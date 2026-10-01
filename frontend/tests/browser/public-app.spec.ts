import { test, expect } from "@playwright/test";

test("public homepage is useful without the backend and a real local check is labelled correctly", async ({ page }) => {
  const backend: string[] = [];
  page.on("request", request => { if (request.url().includes("/api/backend/")) backend.push(request.url()); });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Let’s check your connection." })).toBeVisible();
  await expect(page.getByText("Your results will appear after a check")).toBeVisible();
  await page.getByRole("button", { name: "Run connection check", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Local check complete", exact: true })).toBeVisible({ timeout: 15000 });
  await expect(page.locator(".ns-metric").last()).toContainText("8 / 8");
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Save report", exact: true }).click();
  expect((await download).suggestedFilename()).toMatch(/^netsentinel-check-.*\.txt$/);
  expect(backend).toEqual([]);
});

test("failures remain missing, cancellation saves no partial check", async ({ page }) => {
  await page.route("**/connection-check.json?*", route => route.fulfill({ status: 503, body: "Unavailable" }));
  await page.goto("/");
  await page.getByRole("button", { name: "Run connection check", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Local check complete", exact: true })).toBeVisible({ timeout: 15000 });
  await expect(page.locator(".ns-metric").last()).toContainText("0 / 8");
  await expect(page.locator(".ns-metric").first()).toContainText("—");
  await page.getByRole("button", { name: "Check again", exact: true }).click();
  await page.getByRole("button", { name: "Cancel check", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("No partial result was saved");
  await expect(page.locator(".ns-metric").last()).toContainText("—");
});

test("opt-in history survives reload and can be deleted", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Recent checks", exact: true }).click();
  await expect(page.getByRole("checkbox")).not.toBeChecked();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Overview", exact: true }).click();
  await page.getByRole("button", { name: "Run connection check", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Local check complete", exact: true })).toBeVisible({ timeout: 15000 });
  await page.reload();
  await page.getByRole("button", { name: "Recent checks", exact: true }).click();
  await expect(page.locator(".ns-history-list article")).toHaveCount(1);
  await page.getByRole("button", { name: "Delete all", exact: true }).click();
  await expect(page.locator(".ns-history-list article")).toHaveCount(0);
  await expect(page.getByText("Your next check is a fresh start.")).toBeVisible();
});

test("mobile troubleshooting, planner validation and guide work without overflow", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("button", { name: "Fix a problem", exact: true }).click();
  await page.getByRole("checkbox").first().check();
  await expect(page.getByText("1 of 4 tried")).toBeVisible();
  await page.getByRole("button", { name: "Random disconnections", exact: true }).click();
  await expect(page.getByText("0 of 4 tried")).toBeVisible();
  await page.getByRole("button", { name: "Download planner", exact: true }).click();
  await page.getByLabel("Download speed (Mbps)").fill("0");
  await expect(page.getByRole("heading", { name: "Check your numbers" })).toBeVisible();
  await page.getByLabel("Download speed (Mbps)").fill("50");
  await expect(page.getByRole("heading", { name: "3 minutes" })).toBeVisible();
  await page.getByRole("button", { name: "How it works", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Less technical. More helpful." })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
