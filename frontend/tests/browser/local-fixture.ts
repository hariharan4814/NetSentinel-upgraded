import { test as base, expect, type Page } from "@playwright/test";

// Public test fixture secrets. They exist only in the isolated browser-test server.
export const fixturePassword = "browser-fixture-operator-not-for-runtime";
export const fixtureReadToken = "browser-fixture-read-token-not-for-runtime";
export async function signIn(page: Page) {
  const response = await page.request.post("/api/local-auth", {
    headers: { origin: "http://127.0.0.1:3100", "x-netsentinel-request": "local-ui-v1" },
    data: { password: fixturePassword },
  });
  expect(response.status()).toBe(200);
}
export const test = base.extend({ page: async ({ page }, run) => {
  await signIn(page);
  await run(page);
} });
export { expect };
