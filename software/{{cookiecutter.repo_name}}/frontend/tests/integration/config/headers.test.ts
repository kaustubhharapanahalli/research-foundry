// next.config.ts wires config/security.ts to every route; this checks the
// wiring, and tests/unit/config/security.test.ts checks the values.
import { describe, expect, it } from "vitest";

import { securityHeaders } from "@/config/security";
import config from "@/next.config";

describe("next.config headers()", () => {
  it("sends every security header on every path", async () => {
    const rules = (await config.headers?.()) ?? [];
    expect(rules).toEqual([{ source: "/:path*", headers: securityHeaders }]);
  });

  it("does not announce the framework", () => {
    expect(config.poweredByHeader).toBe(false);
  });

  it("allows no remote images", () => {
    expect(config.images?.remotePatterns).toBeUndefined();
  });
});
