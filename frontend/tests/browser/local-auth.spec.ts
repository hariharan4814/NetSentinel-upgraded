import { test, expect } from "@playwright/test";
import { fixturePassword } from "./local-fixture";

test("private monitor requires sign-in, survives reload and logs out", async ({ page }) => {
  await page.goto("/local");
  await expect(page.getByRole("heading", { name: "Open your local monitor" })).toBeVisible();
  await expect(page.getByLabel("Monitoring session UUID")).toHaveCount(0);
  expect((await page.request.get("/api/backend/health")).status()).toBe(401);
  await page.getByLabel("Local operator password").fill(fixturePassword);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByLabel("Monitoring session UUID")).toBeVisible();
  const cookies = await page.context().cookies();
  const cookie = cookies.find((value) => value.name === "netsentinel_local_session")!;
  expect(cookie.httpOnly).toBe(true);
  expect(cookie.sameSite).toBe("Strict");
  await page.reload();
  await expect(page.getByLabel("Monitoring session UUID")).toBeVisible();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Open your local monitor" })).toBeVisible();
  expect((await page.request.get("/api/backend/health")).status()).toBe(401);
});
