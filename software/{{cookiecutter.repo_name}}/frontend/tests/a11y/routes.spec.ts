// axe on every route the navigation lists, and on the not-found page. A
// page added to config/navigation.ts is checked without a new test.
import AxeBuilder from "@axe-core/playwright";

import { NAVIGATION } from "@/config/navigation";
import { expect, test } from "@/tests/fixtures/playwright";

const ROUTES = [...NAVIGATION.map((item) => item.href), "/no-such-page"];

for (const route of ROUTES) {
  test(`${route} has no detectable accessibility violations`, async ({
    page,
  }) => {
    await page.goto(route);
    // A page that waits on the backend streams its loading state first, and
    // that state has no heading. Check the page itself, which has one.
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });
}
