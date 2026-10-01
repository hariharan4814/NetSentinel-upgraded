import { test, expect } from "@playwright/test";

test("live integration with Session 4 against running backend", async ({ page }) => {
  test.skip(process.env.NETSENTINEL_LIVE_SMOKE !== "1", "Opt-in: requires the operator’s existing local server and private Session 4 data.");
  // Directly hit the live server without page.route mocks
  await page.goto("http://127.0.0.1:3000/local");

  await page.getByLabel("Monitoring session UUID").fill("59673d80-de26-4f31-a828-d91d97664cf8");
  await page.getByLabel("Provenance").selectOption("LIVE");
  await page.getByRole("button", { name: "View session" }).click();

  // Verify backend reachable and session details loaded
  await expect(page.locator(".connection")).toHaveText("Backend reachable", { timeout: 10000 });
  await expect(page.locator("#session")).toContainText("Ethernet 3", { timeout: 10000 });

  // Verify Anomaly Detection panel loads without errors
  const anomalySection = page.locator("#anomaly");
  await expect(anomalySection).toBeVisible({ timeout: 10000 });
  await expect(anomalySection).toContainText("Anomaly Detection");
  await expect(anomalySection).not.toContainText("Refresh failed");

  // Verify latest anomaly status
  await expect(anomalySection.locator(".anomaly-status-card")).toContainText("NORMAL");
  await expect(anomalySection).toContainText("Threshold 0.7191");
  await expect(anomalySection).toContainText("505fdd6c");

  // Verify mandatory disclaimer
  await expect(anomalySection).toContainText(
    "Anomaly indicates statistical deviation from the learned baseline, not confirmed malicious activity."
  );

  // Expand the history table
  await anomalySection.locator("summary").click();
  const table = anomalySection.locator("table");
  await expect(table).toBeVisible();

  // Find the known ANOMALOUS record (score ~0.7314, threshold 0.7191)
  const anomalousRow = anomalySection.locator("tr.anomalous-row");
  await expect(anomalousRow).toBeVisible();
  await expect(anomalousRow).toContainText("ANOMALOUS");
  await expect(anomalousRow).toContainText("0.7314");
  await expect(anomalousRow).toContainText("0.7191");
  await expect(anomalousRow).toContainText("Observed throughput");
  await expect(anomalousRow).toContainText("packet rate");
  await expect(anomalousRow).toContainText("Unique remote peer count");
});
