import { test, expect } from "./local-fixture";
import { labFixture } from "../fixtures/lab-result";
const id = "c67a19b2-8e57-4a12-ae34-076e1d49e4aa";

test("simulation workbench submits, displays computed result, steps gaps and downloads PDFs", async ({ page }) => {
  const result = labFixture();
  let created = false;
  const job = () => ({ id, status: "SUCCEEDED", stage: "complete", created_at: result.generated_at, updated_at: result.generated_at, config: result.config, cancel_requested: false, completed: null, total: null, error: "", result });
  await page.route("**/api/lab/jobs", async route => {
    if (route.request().method() === "POST") {
      expect(route.request().headers()["x-csrf-token"]).toMatch(/^[a-f0-9]{64}$/);
      expect(route.request().postDataJSON()).toEqual({ config: result.config });
      created = true;
      await route.fulfill({ status: 201, json: job() });
    } else await route.fulfill({ json: { jobs: created ? [job()] : [] } });
  });
  await page.route(`**/api/lab/jobs/${id}`, route => route.fulfill({ json: job() }));
  await page.goto("/lab");
  await expect(page.getByText("Your first experiment starts here.")).toBeVisible();
  await page.getByRole("button", { name: "Generate, train & evaluate" }).click();
  await expect(page.getByRole("heading", { name: "Your experiment, explained" })).toBeVisible();
  await expect(page.getByText("Injected truth is hidden.", { exact: false })).toBeVisible();
  await page.getByLabel("Reveal injected scenario").check();
  await expect(page.getByText("Injected truth:", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Step forward" }).click();
  await page.getByRole("button", { name: "Step forward" }).click();
  await expect(page.locator(".lab-window-detail .lab-pill")).toHaveText("UNSCORED");
  await page.getByRole("button", { name: "Restart playback" }).click();
  await expect(page.getByText("Synthetic test explanation", { exact: false })).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download PDF" }).click();
  expect((await download).suggestedFilename()).toMatch(/netsentinel-lab-seed-42.pdf/);
  await page.setViewportSize({ width: 360, height: 800 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: "test-results/lab-mobile.png", fullPage: true });
});

test("running experiments show actual stage and explicit cancellation without invented results", async ({ page }) => {
  let cancelled = false;
  const result = labFixture();
  const job = () => ({ id, status: cancelled ? "CANCELLED" : "RUNNING", stage: "training", created_at: result.generated_at, updated_at: result.generated_at, config: result.config, cancel_requested: cancelled, completed: null, total: null, error: "" });
  await page.route("**/api/lab/jobs", route => route.fulfill({ json: { jobs: [job()] } }));
  await page.route(`**/api/lab/jobs/${id}`, route => route.fulfill({ json: job() }));
  await page.route(`**/api/lab/jobs/${id}/cancel`, route => { cancelled = true; return route.fulfill({ json: job() }); });
  await page.goto("/lab");
  await page.getByRole("button", { name: /Seed 42/ }).click();
  await expect(page.getByRole("progressbar")).not.toHaveAttribute("value");
  await page.getByRole("button", { name: "Cancel experiment" }).click();
  await expect(page.getByRole("heading", { name: "CANCELLED · training" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Your experiment, explained" })).toHaveCount(0);
});
