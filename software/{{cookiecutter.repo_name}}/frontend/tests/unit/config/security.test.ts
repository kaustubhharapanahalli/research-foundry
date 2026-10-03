import { describe, expect, it } from "vitest";

import { securityHeaders } from "@/config/security";

const header = (key: string) =>
  securityHeaders.find((item) => item.key === key)?.value ?? "";

describe("the security headers", () => {
  it("forbid framing and object embedding in the CSP", () => {
    const csp = header("Content-Security-Policy");
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).toContain("object-src 'none'");
    expect(csp).toContain("default-src 'self'");
  });

  it("turn off content sniffing and framing", () => {
    expect(header("X-Content-Type-Options")).toBe("nosniff");
    expect(header("X-Frame-Options")).toBe("DENY");
  });
});
