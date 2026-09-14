import { test, expect } from "@playwright/test";

for (const historical of [false, true]) {
  test(`outage retains selection and ${historical ? "stale" : "initially fresh"} records, then recovers automatically`, async ({ page }) => {
    let unavailable = false;
    let profile = "before-outage";
    const observed = new Date(Date.now() - (historical ? 60000 : 0)).toISOString();
    const session = "11111111-1111-1111-1111-111111111111";
    const identity = { id: "22222222-2222-2222-2222-222222222222", session_id: session,
      run_id: "33333333-3333-3333-3333-333333333333", mode: "SIMULATION", interface_name: "retained-fixture" };
    await page.route("**/api/backend/**", (route) => {
      if (unavailable) return route.fulfill({ status: 503, json: { error: "Backend unavailable or request timed out." } });
      const path = new URL(route.request().url()).pathname;
      let json: unknown = { status: "ok", database: "reachable" };
      if (path.endsWith("monitoring-sessions")) json = { ...identity, source_id: "44444444-4444-4444-4444-444444444444",
        started_at: observed, received_at: observed, observation_profile: profile, schema_version: "backend-v1" };
      if (path.endsWith("telemetry")) json = { next: null, results: [{ ...identity, observed_at: observed, valid: true,
        reason: null, upload_bytes_per_second: 1024, download_bytes_per_second: 0, packets_sent: 12, packets_received: 8 }] };
      if (path.endsWith("windows")) json = { next: null, results: [{ ...identity, start: observed, end: observed,
        valid: false, partial: true, reason: "retained-partial-fixture", packets: 7, ip_bytes: 400, tcp_packets: 7, udp_packets: 0, flow_count: 1 }] };
      if (path.endsWith("capture-status")) json = { next: null, results: [{ ...identity, received_at: observed,
        observed_at: observed, state: "RUNNING", valid: true, reason: null, loss_started_at: null, gap_ended_at: null,
        monitoring_gap_seconds: 0, recovery_attempts: 0 }] };
      if (path.endsWith("anomaly-results")) json = { next: null, results: [] };
      return route.fulfill({ json });
    });
    await page.goto("/");
    await page.getByLabel("Monitoring session UUID").fill(session);
    await page.getByLabel("Provenance").selectOption("SIMULATION");
    await page.getByRole("button", { name: "View session" }).click();
    await expect(page.locator("#session")).toContainText("before-outage");
    await page.getByText("Inspect returned samples (1)").click();
    if (historical) await expect(page.locator(".metric").first()).toContainText("Unavailable");
    else await expect(page.locator(".metric").first()).toContainText("1.00 KiB/s");

    unavailable = true;
    await expect(page.locator(".connection")).toHaveText("Backend unavailable", { timeout: 10000 });
    await expect(page.getByLabel("Monitoring session UUID")).toHaveValue(session);
    await expect(page.getByLabel("Provenance")).toHaveValue("SIMULATION");
    await expect(page.locator("#session")).toContainText("before-outage");
    await expect(page.locator("#windows")).toContainText("retained-partial-fixture");
    await expect(page.locator("#capture")).toContainText("RUNNING");
    await expect(page.locator("#telemetry table")).toContainText("1.00 KiB/s");
    for (const panel of ["#telemetry", "#windows", "#capture", "#session"])
      await expect(page.locator(panel)).toContainText("Refresh failed");
    await expect(page.locator(".metric").first()).toContainText("Unavailable");

    profile = "after-outage"; unavailable = false;
    await expect(page.locator("#session")).toContainText("after-outage", { timeout: 15000 });
    await expect(page.locator(".connection")).toHaveText("Backend reachable");
    await expect(page.getByLabel("Monitoring session UUID")).toHaveValue(session);
    await expect(page.getByLabel("Provenance")).toHaveValue("SIMULATION");
    await expect(page.getByText("Refresh failed", { exact: false })).toHaveCount(0);
    // Re-fetching the same timestamp must not make an old observation fresh.
    await expect(page.locator(".metric").first()).toContainText("Unavailable");
    await expect(page.locator(".metric").last()).toContainText("Stale observation");
  });
}
