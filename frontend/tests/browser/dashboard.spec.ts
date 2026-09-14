import { test, expect, type Page, type Route } from "@playwright/test";
const session = "11111111-1111-1111-1111-111111111111";
const run = "33333333-3333-3333-3333-333333333333";

async function mockReply(route: Route, options: Parameters<Route["fulfill"]>[0]) {
  const url = new URL(route.request().url());
  if (!options?.status || options.status === 200) {
    if (url.pathname.endsWith("capture-status") || url.pathname.endsWith("anomaly-results")) {
      options = { json: { next: null, results: [] } };
    }
    if (url.pathname.endsWith("monitoring-sessions")) {
      options = {
        json: {
          session_id: session,
          run_id: run,
          source_id: "44444444-4444-4444-4444-444444444444",
          interface_name: "fixture",
          mode: url.searchParams.get("mode"),
          started_at: "2026-09-13T00:00:00Z",
          received_at: "2026-09-13T00:00:01Z",
          observation_profile: "browser-fixture",
          schema_version: "backend-v1",
        },
      };
    }
  }
  return route.fulfill(options);
}

async function select(page: Page, mode = "SIMULATION") {
  await page.getByLabel("Monitoring session UUID").fill(session);
  await page.getByLabel("Provenance").selectOption(mode);
  await page.getByRole("button", { name: "View session" }).click();
}

test("renders sticky top header navigation and footer without sidebar", async ({ page }) => {
  await page.route("**/api/backend/**", (route) =>
    mockReply(route, { json: route.request().url().includes("health") ? { status: "ok", database: "reachable" } : { next: null, results: [] } })
  );
  await page.goto("/");

  // 1. Verify Top Header is present and sticky
  const header = page.locator("header.top-nav");
  await expect(header).toBeVisible();
  await expect(header.locator(".brand")).toContainText("NetSentinel");
  await expect(header.locator(".brand-badge")).toHaveText("Local");

  // 2. Verify Left Sidebar is completely removed
  await expect(page.locator("aside.sidebar")).toHaveCount(0);

  // 3. Verify all 6 Top Navigation links render
  const nav = page.locator(".desktop-nav");
  await expect(nav.getByRole("link", { name: "Overview" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Anomaly Detection" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Live Telemetry" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Traffic Windows" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Capture & Interface" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Session Summary" })).toBeVisible();

  // 4. Verify Header status indicator & mode badge
  await expect(header.locator(".badge")).toHaveText("LIVE");
  await expect(header.locator(".status-indicator")).toContainText("Backend reachable");

  // 5. Verify Footer renders with branding, tech stack, and scientific disclaimer
  const footer = page.locator("footer.app-footer");
  await expect(footer).toBeVisible();
  await expect(footer).toContainText("NetSentinel");
  await expect(footer).toContainText("Intelligent Network Monitoring & Anomaly Detection");
  await expect(footer).toContainText("Own-host observation");
  await expect(footer).toContainText("Next.js · Django · PostgreSQL · Isolation Forest");
  await expect(footer).toContainText("Anomalies indicate statistical deviation, not confirmed malicious activity.");
});

test("mobile responsive header opens hamburger menu and closes on selection", async ({ page }) => {
  await page.route("**/api/backend/**", (route) =>
    mockReply(route, { json: route.request().url().includes("health") ? { status: "ok", database: "reachable" } : { next: null, results: [] } })
  );
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");

  // Verify desktop nav is hidden and hamburger button is visible
  await expect(page.locator(".desktop-nav")).not.toBeVisible();
  const toggleBtn = page.getByRole("button", { name: /toggle navigation menu/i });
  await expect(toggleBtn).toBeVisible();

  // Open mobile drawer
  await toggleBtn.click();
  const mobileNav = page.locator(".mobile-nav");
  await expect(mobileNav).toBeVisible();
  await expect(mobileNav.getByRole("link", { name: "Anomaly Detection" })).toBeVisible();

  // Clicking link in mobile menu closes drawer
  await mobileNav.getByRole("link", { name: "Overview" }).click();
  await expect(page.locator(".mobile-nav")).toHaveCount(0);
});

test("empty states, local navigation and mobile layout", async ({ page }, testInfo) => {
  await page.route("**/api/backend/**", (route) =>
    mockReply(route, { json: route.request().url().includes("health") ? { status: "ok", database: "reachable" } : { next: null, results: [] } })
  );
  await page.goto("/");
  await expect(page.getByText("Ready when your data is.")).toBeVisible();
  await select(page);
  await expect(page.getByText("No recent telemetry for this session", { exact: false })).toBeVisible();
  await expect(page.getByText("No recent windows for this session", { exact: false })).toBeVisible();
  await expect(page.getByText("No recent capture status for this session", { exact: false })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("desktop.png"), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath("mobile.png"), fullPage: true });
});

test("loading state is visible until API replies", async ({ page }) => {
  let release!: () => void;
  const pending = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/backend/**", async (route) => {
    await pending;
    await mockReply(route, { json: route.request().url().includes("health") ? { status: "ok", database: "reachable" } : { next: null, results: [] } });
  });
  await page.goto("/");
  await select(page);
  await expect(page.getByText("Loading telemetry…", { exact: true })).toBeVisible();
  release();
  await expect(page.getByText("No recent telemetry for this session", { exact: false })).toBeVisible();
});

test("previous mode requests cannot repopulate the new selection", async ({ page }) => {
  let release!: () => void;
  const pending = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/backend/**", async (route) => {
    const old = new URL(route.request().url()).searchParams.get("mode") === "SIMULATION";
    if (old) await pending;
    await mockReply(route, { json: route.request().url().includes("health") ? { status: "ok", database: "reachable" } : { next: null, results: [] } }).catch(() => {});
  });
  await page.goto("/");
  await select(page);
  await expect(page.getByText("Loading telemetry…", { exact: true })).toBeVisible();
  await select(page, "REPLAY");
  release();
  await expect(page.locator(".status-strip .badge")).toHaveText("REPLAY");
  await expect(page.locator("header.top-nav .badge")).toHaveText("REPLAY");
  await expect(page.getByText("No recent telemetry for this session", { exact: false })).toBeVisible();
});

test("measured zero, partial windows and mode switching without old data", async ({ page }) => {
  await page.route("**/api/backend/**", (route) => {
    const url = new URL(route.request().url());
    const identity = { id: "22222222-2222-2222-2222-222222222222", session_id: session, run_id: run, interface_name: "simulation-fixture", mode: "SIMULATION" };
    const sample = { ...identity, observed_at: new Date().toISOString(), valid: true, reason: null, upload_bytes_per_second: 1024, download_bytes_per_second: 0, packets_sent: 10, packets_received: 0 };
    const window = { ...identity, start: new Date(Date.now() - 10000).toISOString(), end: new Date().toISOString(), valid: false, partial: true, reason: "fixture_missing_coverage", packets: 0, ip_bytes: 0, tcp_packets: 0, udp_packets: 0, flow_count: 0 };
    return mockReply(route, { json: url.pathname.endsWith("health") ? { status: "ok", database: "reachable" } : { next: null, results: url.searchParams.get("mode") !== "SIMULATION" ? [] : [url.pathname.endsWith("telemetry") ? sample : window] } });
  });
  await page.goto("/");
  await select(page);
  await expect(page.getByText("1.00 KiB/s", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("0.0 B/s", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("Partial · invalid", { exact: true })).toBeVisible();
  await select(page, "REPLAY");
  await expect(page.getByText("No recent telemetry for this session", { exact: false })).toBeVisible();
  await expect(page.getByText("simulation-fixture")).toHaveCount(0);
});

test("backend errors never become zero rates", async ({ page }) => {
  await page.route("**/api/backend/**", (route) => mockReply(route, { status: 503, json: { error: "Backend unavailable or request timed out." } }));
  await page.goto("/");
  await select(page);
  await expect(page.getByText("Backend unavailable", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("0.0 B/s", { exact: true })).toHaveCount(0);
  await expect(page.locator(".metric").first()).toContainText("Unavailable");
});

test("stale and invalid observations keep rates unavailable", async ({ page }) => {
  await page.route("**/api/backend/**", (route) => {
    const url = route.request().url();
    return mockReply(route, {
      json: url.includes("health")
        ? { status: "ok", database: "reachable" }
        : {
            next: null,
            results: url.includes("telemetry")
              ? [
                  {
                    id: "22222222-2222-2222-2222-222222222222",
                    session_id: session,
                    run_id: run,
                    interface_name: "fixture",
                    mode: "SIMULATION",
                    observed_at: new Date(Date.now() - 60000).toISOString(),
                    valid: false,
                    reason: "counter_gap",
                    upload_bytes_per_second: null,
                    download_bytes_per_second: null,
                    packets_sent: 10,
                    packets_received: 0,
                  },
                ]
              : [],
          },
    });
  });
  await page.goto("/");
  await select(page);
  await expect(page.getByText("Invalid observation", { exact: true })).toBeVisible();
  await expect(page.locator(".metric").first()).toContainText("Unavailable");
  await expect(page.getByText("counter_gap", { exact: false }).first()).toBeVisible();
});

test("renders anomaly detection section with evidence-based explanation and disclaimer", async ({ page }) => {
  const anomalyRecord = {
    id: "22222222-2222-2222-2222-222222222222",
    session_id: session,
    run_id: run,
    interface_name: "fixture",
    mode: "SIMULATION",
    window_id: "55555555-5555-5555-5555-555555555555",
    model_version_id: "66666666-6666-6666-6666-666666666666",
    observed_at: new Date().toISOString(),
    scored_at: new Date().toISOString(),
    anomaly_score: 0.7314,
    label: "ANOMALOUS",
    explanation: "Observed throughput (701.9 KiB/s) and packet rate (892.3 pkt/s) is higher than the learned baseline range.",
    deviating_features: ["ip_bytes_per_second", "packets_per_second"],
  };

  await page.route("**/api/backend/**", (route) => {
    const url = route.request().url();
    if (url.includes("anomaly-results")) {
      return route.fulfill({ json: { next: null, results: [anomalyRecord] } });
    }
    return mockReply(route, { json: url.includes("health") ? { status: "ok", database: "reachable" } : { next: null, results: [] } });
  });

  await page.goto("/");
  await select(page);

  // 1. Verify Anomaly section is rendered
  await expect(page.locator("#anomaly")).toBeVisible();
  await expect(page.locator("#anomaly")).toContainText("ANOMALOUS");
  await expect(page.locator("#anomaly")).toContainText("0.7314");
  await expect(page.locator("#anomaly")).toContainText("Observed throughput (701.9 KiB/s)");

  // 2. Verify deviating feature tags
  await expect(page.locator(".deviating-tag").first()).toContainText("ip_bytes_per_second");

  // 3. Verify mandatory scientific disclaimer
  await expect(
    page.locator("#anomaly").getByText("Anomaly indicates statistical deviation from the learned baseline, not confirmed malicious activity.")
  ).toBeVisible();

  // 4. Verify no attack words
  const text = await page.locator("#anomaly").innerText();
  expect(text.toLowerCase()).not.toContain("attack");
  expect(text.toLowerCase()).not.toContain("malware");
  expect(text.toLowerCase()).not.toContain("intrusion");

  // 5. Verify Copy button works
  await page.locator("#anomaly").getByRole("button", { name: /copy/i }).first().click();
  await expect(page.locator("#anomaly").getByRole("button", { name: /copied/i }).first()).toBeVisible();
});

for (const state of ["RUNNING", "INTERFACE_LOST", "RECOVERING", "STOPPED"]) {
  test(`stored ${state} status and full session metadata`, async ({ page }) => {
    await page.route("**/api/backend/**", (route) => {
      if (route.request().url().includes("capture-status")) {
        return route.fulfill({
          json: {
            next: null,
            results: [
              {
                id: "22222222-2222-2222-2222-222222222222",
                session_id: session,
                run_id: run,
                mode: "SIMULATION",
                interface_name: "fixture",
                received_at: new Date().toISOString(),
                observed_at: new Date().toISOString(),
                state,
                valid: state === "RUNNING",
                reason: state === "RUNNING" ? null : "fixture_gap",
                loss_started_at: null,
                gap_ended_at: null,
                monitoring_gap_seconds: state === "RUNNING" ? 0 : 12.5,
                recovery_attempts: state === "RUNNING" ? 0 : 2,
              },
            ],
          },
        });
      }
      return mockReply(route, { json: route.request().url().includes("health") ? { status: "ok", database: "reachable" } : { next: null, results: [] } });
    });
    await page.goto("/");
    await select(page);
    await expect(page.locator("#capture")).toContainText(state);
    await expect(page.locator("#capture")).toContainText(state === "RUNNING" ? "0 s" : "12.5 s");
    await expect(page.locator("#capture dl > div").filter({ hasText: "Interface link state" })).toContainText("Unavailable");
    await expect(page.locator("#session")).toContainText("44444444-4444-4444-4444-444444444444");
    await expect(page.locator("#session")).toContainText("browser-fixture");
    await expect(page.locator("#session")).toContainText("2026-09-13 00:00:00 UTC");
  });
}

test("stale status and unknown session remain explicit", async ({ page }) => {
  await page.route("**/api/backend/**", (route) => {
    if (route.request().url().includes("monitoring-sessions")) {
      return route.fulfill({ status: 404, json: { error: "Session unavailable: no matching session and mode." } });
    }
    if (route.request().url().includes("capture-status")) {
      return route.fulfill({
        json: {
          next: null,
          results: [
            {
              id: "22222222-2222-2222-2222-222222222222",
              session_id: session,
              run_id: run,
              mode: "SIMULATION",
              interface_name: "fixture",
              received_at: new Date().toISOString(),
              observed_at: new Date(Date.now() - 60000).toISOString(),
              state: "RUNNING",
              valid: true,
              reason: null,
              loss_started_at: null,
              gap_ended_at: null,
              monitoring_gap_seconds: 0,
              recovery_attempts: 0,
            },
          ],
        },
      });
    }
    return mockReply(route, { json: route.request().url().includes("health") ? { status: "ok", database: "reachable" } : { next: null, results: [] } });
  });
  await page.goto("/");
  await select(page);
  await expect(page.locator("#capture")).toContainText("Stale report");
  await expect(page.locator("#capture")).toContainText("current state unavailable");
  await expect(page.locator("#session")).toContainText("Session unavailable:");
});

test("a newer loss event suppresses current rates without altering historical samples", async ({ page }) => {
  const observed = Date.now();
  const identity = { id: "22222222-2222-2222-2222-222222222222", session_id: session, run_id: run, mode: "SIMULATION", interface_name: "fixture" };
  await page.route("**/api/backend/**", (route) => {
    if (route.request().url().includes("capture-status")) {
      return route.fulfill({
        json: {
          next: null,
          results: [
            {
              ...identity,
              received_at: new Date(observed).toISOString(),
              observed_at: new Date(observed).toISOString(),
              state: "INTERFACE_LOST",
              valid: false,
              reason: "fixture_loss",
              loss_started_at: new Date(observed).toISOString(),
              gap_ended_at: null,
              monitoring_gap_seconds: 0,
              recovery_attempts: 0,
            },
          ],
        },
      });
    }
    if (route.request().url().includes("telemetry")) {
      return route.fulfill({
        json: {
          next: null,
          results: [
            {
              ...identity,
              observed_at: new Date(observed - 100).toISOString(),
              valid: true,
              reason: null,
              upload_bytes_per_second: 0,
              download_bytes_per_second: 0,
              packets_sent: 10,
              packets_received: 0,
            },
          ],
        },
      });
    }
    return mockReply(route, { json: route.request().url().includes("health") ? { status: "ok", database: "reachable" } : { next: null, results: [] } });
  });
  await page.goto("/");
  await select(page);
  await expect(page.locator("#capture")).toContainText("INTERFACE_LOST");
  await page.getByText("Inspect returned samples (1)").click();
  await expect(page.locator("#telemetry table")).toContainText("0.0 B/s");
});

test("supports prefers-reduced-motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.route("**/api/backend/**", (route) =>
    mockReply(route, { json: route.request().url().includes("health") ? { status: "ok", database: "reachable" } : { next: null, results: [] } })
  );
  await page.goto("/");
  await select(page);
  await expect(page.locator("#anomaly")).toBeVisible();
});
