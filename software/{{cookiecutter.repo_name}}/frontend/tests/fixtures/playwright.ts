// Every page collects its browser coverage, which scripts/coverage.mjs
// merges with the unit tests' and the Next server's.
import { mkdir, writeFile } from "node:fs/promises";

import { test as base } from "@playwright/test";

export const test = base.extend({
  page: async ({ page }, provide, testInfo) => {
    await page.coverage.startJSCoverage({ resetOnNavigation: false });
    await provide(page);
    const coverage = await page.coverage.stopJSCoverage();
    await mkdir("coverage/raw-browser", { recursive: true });
    await writeFile(
      `coverage/raw-browser/${testInfo.testId}.json`,
      JSON.stringify(coverage),
    );
  },
});

export { expect } from "@playwright/test";
