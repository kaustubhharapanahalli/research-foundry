import { defineConfig, devices } from "@playwright/test";

// End-to-end tests against `next build` and `next start`, with the Django
// backend running. NODE_V8_COVERAGE collects the Next server's coverage.
const FRONTEND = "http://127.0.0.1:3100";
const BACKEND = "http://127.0.0.1:8100";

export default defineConfig({
  // Behaviour in e2e/, the accessibility sweep in a11y/.
  testDir: "tests",
  testMatch: ["e2e/**/*.spec.ts", "a11y/**/*.spec.ts"],
  forbidOnly: !!process.env.CI,
  retries: 0,
  use: { baseURL: FRONTEND, trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `cd .. && uv run python backend/manage.py runserver ${BACKEND.replace("http://", "")} --noreload`,
      url: `${BACKEND}/health/`,
      reuseExistingServer: false,
    },
    {
      command: `NODE_V8_COVERAGE=coverage/raw-server BACKEND_URL=${BACKEND} pnpm exec next start -H 127.0.0.1 -p ${new URL(FRONTEND).port}`,
      url: FRONTEND,
      reuseExistingServer: false,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10_000 },
    },
  ],
});
