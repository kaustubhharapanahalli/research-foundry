import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { backendUrl, fetchHealth } from "@/lib/server/backend";

const answer = (status: number, body: unknown) =>
  vi.fn(async () => new Response(JSON.stringify(body), { status }));

describe("the backend client", () => {
  beforeEach(() => {
    vi.stubEnv("BACKEND_URL", "http://backend.test/");
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("reads the address at call time, without a trailing slash", () => {
    expect(backendUrl()).toBe("http://backend.test");
  });

  it("refuses to guess an address that is not set", () => {
    vi.stubEnv("BACKEND_URL", "");
    expect(() => backendUrl()).toThrow("BACKEND_URL must be set");
  });

  it("reports up when the backend says ok", async () => {
    const fetch = answer(200, { status: "ok" });
    vi.stubGlobal("fetch", fetch);
    await expect(fetchHealth()).resolves.toEqual({ state: "up" });
    expect(fetch).toHaveBeenCalledWith(
      "http://backend.test/health/",
      expect.objectContaining({ cache: "no-store" }),
    );
  });

  it("reports down with the status code on an error answer", async () => {
    vi.stubGlobal("fetch", answer(503, {}));
    await expect(fetchHealth()).resolves.toEqual({
      state: "down",
      reason: "HTTP 503",
    });
  });

  it("reports down on an answer it does not recognise", async () => {
    vi.stubGlobal("fetch", answer(200, { status: "starting" }));
    await expect(fetchHealth()).resolves.toEqual({
      state: "down",
      reason: "unexpected answer",
    });
  });

  it("reports down when the backend cannot be reached", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("fetch failed");
      }),
    );
    await expect(fetchHealth()).resolves.toEqual({
      state: "down",
      reason: "fetch failed",
    });
  });

  it("reports down when something other than an Error is thrown", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw "offline";
      }),
    );
    await expect(fetchHealth()).resolves.toEqual({
      state: "down",
      reason: "offline",
    });
  });
});
