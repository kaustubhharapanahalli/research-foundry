import { expect, test } from "@/tests/fixtures/playwright";

test("the home page shows the backend as up", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Backend: up" }),
  ).toBeVisible();
});

test("checking again renders the page on the server again", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Check again" }).click();
  await expect(page.getByRole("button", { name: "Check again" })).toBeEnabled();
  await expect(
    page.getByRole("heading", { name: "Backend: up" }),
  ).toBeVisible();
});

test("every response carries the security headers", async ({ page }) => {
  const response = await page.goto("/");
  const headers = response?.headers() ?? {};
  expect(headers["content-security-policy"]).toContain(
    "frame-ancestors 'none'",
  );
  expect(headers["x-content-type-options"]).toBe("nosniff");
  expect(headers["x-powered-by"]).toBeUndefined();
});

test("an unknown path shows the not-found page", async ({ page }) => {
  const response = await page.goto("/no-such-page");
  expect(response?.status()).toBe(404);
  await expect(
    page.getByRole("heading", { name: "Page not found" }),
  ).toBeVisible();
});
