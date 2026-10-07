import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";

test("public external tools require explicit consent; lookup and mobile PDF redaction work with labelled fixture data", async ({ page }) => {
  const external: string[] = [];
  page.on("request", request => { if (/speed\.cloudflare\.com|ipwho\.is/.test(request.url())) external.push(request.url()); });
  await page.route("https://ipwho.is/**", route => route.fulfill({ contentType: "application/json", headers: { "access-control-allow-origin": "*" }, body: JSON.stringify({ success: true, ip: "192.0.2.40", city: "Example City", region: "Example Region", country: "Example Country", connection: { asn: 64500, org: "SIMULATION NETWORK FIXTURE" } }) }));
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("button", { name: "Speed test", exact: true }).click();
  await expect(page.getByRole("button", { name: "Start speed test", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Network details", exact: true }).click();
  await expect(page.getByRole("button", { name: "Look up my network", exact: true })).toBeDisabled();
  expect(external).toEqual([]);
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Look up my network", exact: true }).click();
  await expect(page.getByText("192.0.2.40", { exact: true })).toBeVisible();
  await expect(page.getByText("AS64500", { exact: true })).toBeVisible();
  expect(external).toHaveLength(1);
  await page.getByRole("button", { name: "Create a redacted PDF", exact: true }).click();
  await page.getByLabel(/Network details \(/).check();
  await expect(page.getByLabel("Include my public IP address")).not.toBeChecked();
  await expect(page.getByLabel("Include approximate location")).not.toBeChecked();
  const downloadEvent = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download PDF", exact: true }).click();
  const download = await downloadEvent;
  expect(download.suggestedFilename()).toMatch(/netsentinel-report-.*\.pdf$/);
  const bytes = await readFile((await download.path())!);
  expect(bytes.subarray(0, 5).toString()).toBe("%PDF-");
  const text = bytes.toString("latin1"); expect(text).toContain("Hidden by default"); expect(text).not.toContain("192.0.2.40"); expect(text).not.toContain("Example City");
  expect(external).toHaveLength(1);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("speed test completion and optional history use the real engine against controlled responses", async ({ page }) => {
  test.setTimeout(45000);
  let requests = 0;
  await page.route("https://speed.cloudflare.com/**", async route => {
    requests++;
    const url = new URL(route.request().url());
    expect(["/__down", "/__up"]).toContain(url.pathname);
    const bytes = route.request().method() === "POST" ? 0 : Number(url.searchParams.get("bytes") ?? 0);
    await new Promise(resolve => setTimeout(resolve, 30));
    await route.fulfill({ status: 200, body: Buffer.alloc(bytes, 48), headers: { "content-type": "application/octet-stream", "cache-control": "no-store", "access-control-allow-origin": "*", "timing-allow-origin": "*", "server-timing": "cfRequestDuration;dur=1" } });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Speed test", exact: true }).click();
  await page.getByLabel(/Use Cloudflare/).check();
  await page.getByLabel("Keep speed-test history on this device").check();
  await page.getByRole("button", { name: "Start speed test", exact: true }).click();
  await expect(page.getByText(/Finished .*complete/)).toBeVisible({ timeout: 30000 });
  expect(requests).toBeGreaterThanOrEqual(8); expect(requests).toBeLessThanOrEqual(12);
  await expect(page.locator(".ns-public-table tbody tr")).toHaveCount(1);
  await page.reload();
  await page.getByRole("button", { name: "Speed test", exact: true }).click();
  await expect(page.locator(".ns-public-table tbody tr")).toHaveCount(1);
  await page.getByLabel("Keep speed-test history on this device").uncheck();
  await expect(page.getByText("No saved speed tests yet.")).toBeVisible();
});

test("speed failures and lookup limits remain unavailable and do not silently retry lookup", async ({ page }) => {
  let lookups = 0;
  await page.route("https://speed.cloudflare.com/**", route => route.abort("failed"));
  await page.route("https://ipwho.is/**", route => { lookups++; return route.fulfill({ status: 429, body: "limit", headers: { "access-control-allow-origin": "*" } }); });
  await page.goto("/");
  await page.getByRole("button", { name: "Speed test", exact: true }).click();
  await page.getByLabel(/Use Cloudflare/).check();
  await page.getByRole("button", { name: "Start speed test", exact: true }).click();
  await expect(page.getByText(/Test could not finish/)).toBeVisible();
  await expect(page.getByText("No saved speed tests yet.")).toBeVisible();
  await page.getByRole("button", { name: "Network details", exact: true }).click();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Look up my network", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("daily limit");
  expect(lookups).toBe(1);
});

test("unpublished companion is explained without a broken installer link", async ({ page }) => {
  await page.route("**/companion-release.json", route => route.fulfill({ json: { available: false, version: "0.2.0" } }));
  await page.goto("/");
  await page.getByRole("button", { name: "Windows companion", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Meet your Windows companion." })).toBeVisible();
  await expect(page.getByRole("status")).toContainText("verified download has not been published");
  await expect(page.getByRole("link", { name: /Download Windows companion/ })).toHaveCount(0);
});
