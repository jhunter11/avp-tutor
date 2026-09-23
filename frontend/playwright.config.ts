import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 8000 },
  use: {
    baseURL: "http://127.0.0.1:5175",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: "npm run dev -- --host 127.0.0.1 --port 5175 --strictPort",
    url: "http://127.0.0.1:5175",
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
    env: {
      VITE_DEV_API_TARGET:
        process.env.VITE_DEV_API_TARGET || "http://127.0.0.1:18080",
    },
  },
  projects: [
    {
      name: "ci",
      use: { browserName: "chromium" },
      testMatch: "**/*-mocked.spec.ts",
    },
    ...(process.env.E2E_LIVE
      ? [
          {
            name: "live",
            use: { browserName: "chromium" as const },
            testMatch: "**/chat.spec.ts",
          },
        ]
      : []),
  ],
});
