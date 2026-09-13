import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests/browser",
  testMatch: "gateway-live.spec.ts",
  // Reuse the operator's dev server without stopping it; otherwise start a local test server.
  use: { baseURL: "http://127.0.0.1:3000", channel: "msedge", headless: true },
  webServer: { command: "npm run dev -- --port 3000", url: "http://127.0.0.1:3000", reuseExistingServer: true, timeout: 60000,
    env: { BACKEND_API_BASE_URL: "http://127.0.0.1:3103/api/v1/" } },
});
