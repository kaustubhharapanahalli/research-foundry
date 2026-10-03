import { afterEach, describe, expect, it, vi } from "vitest";

import { requiredEnv } from "@/lib/server/env";

describe("requiredEnv", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("returns the value the environment holds", () => {
    vi.stubEnv("EXAMPLE_SETTING", "value");
    expect(requiredEnv("EXAMPLE_SETTING")).toBe("value");
  });

  describe("refuses", () => {
    it("a setting that is empty", () => {
      vi.stubEnv("EXAMPLE_SETTING", "");
      expect(() => requiredEnv("EXAMPLE_SETTING")).toThrow(
        "EXAMPLE_SETTING must be set in the environment.",
      );
    });

    it("a setting that is missing", () => {
      expect(() => requiredEnv("EXAMPLE_SETTING_NEVER_SET")).toThrow(
        "EXAMPLE_SETTING_NEVER_SET must be set",
      );
    });
  });
});
