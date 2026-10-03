import { describe, expect, it } from "vitest";

import { describeHealth } from "@/features/status/model/describe";

describe("describeHealth", () => {
  it("says the backend is up", () => {
    expect(describeHealth({ state: "up" })).toEqual({
      label: "Backend: up",
      detail: "The API and its database answer.",
      tone: "ok",
    });
  });

  it("says why the backend is down", () => {
    const view = describeHealth({ state: "down", reason: "HTTP 500" });
    expect(view.tone).toBe("danger");
    expect(view.detail).toContain("HTTP 500");
  });
});
