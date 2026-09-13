import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests/browser",
  fullyParallel: false,
  use: { baseURL: "http://127.0.0.1:3100", channel: "msedge", headless: true },
  webServer: { command: "npm run start -- --port 3100", url: "http://127.0.0.1:3100", reuseExistingServer: false, timeout: 60000,
    env: { BACKEND_API_BASE_URL: "http://127.0.0.1:3103/api/v1/" } },
});
