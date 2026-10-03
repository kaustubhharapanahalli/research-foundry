import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

import { unitCoverage } from "./scripts/coverage-sources.mjs";

// Unit and component tests. Coverage is collected raw, then merged with the
// end-to-end run's by scripts/coverage.mjs, which applies the 90% floor.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": import.meta.dirname,
      // Next resolves server-only to an empty module on the server; tests
      // import server code directly, so they get the empty module too.
      "server-only": "next/dist/compiled/server-only/empty.js",
    },
  },
  test: {
    environment: "jsdom",
    include: ["tests/{unit,component,integration}/**/*.test.{ts,tsx}"],
    setupFiles: ["tests/setup.ts"],
    coverage: {
      enabled: true,
      provider: "custom",
      customProviderModule: "vitest-monocart-coverage",
      reportsDirectory: "coverage/unit",
      // @ts-expect-error -- vitest-monocart-coverage reads this key.
      coverageReportOptions: unitCoverage,
    },
  },
});
