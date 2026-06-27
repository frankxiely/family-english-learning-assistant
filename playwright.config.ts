import { defineConfig, devices } from "@playwright/test";

const e2eApiBase = "http://127.0.0.1:18000";
const e2eWebBase = "http://127.0.0.1:15173";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 90_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: e2eWebBase,
    extraHTTPHeaders: {
      "x-e2e-api-base": e2eApiBase,
    },
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "scripts/start_e2e_api.sh",
      url: `${e2eApiBase}/api/health`,
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: "scripts/start_e2e_web.sh",
      url: `${e2eWebBase}/login`,
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
  projects: [
    {
      name: "mobile-chromium",
      use: {
        ...devices["Pixel 5"],
      },
    },
  ],
});
