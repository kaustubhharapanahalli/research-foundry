import "server-only";

import type { Health } from "@/types/health";

import { requiredEnv } from "./env";

const TIMEOUT_MS = 2000;

/**
 * Read the backend's address at request time, never at build time, so one
 * image runs in every environment.
 */
export function backendUrl(): string {
  return requiredEnv("BACKEND_URL").replace(/\/+$/, "");
}

/** Ask the backend whether it and its database are up. */
export async function fetchHealth(): Promise<Health> {
  try {
    const response = await fetch(`${backendUrl()}/health/`, {
      cache: "no-store",
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    if (!response.ok) {
      return { state: "down", reason: `HTTP ${response.status}` };
    }
    const body: unknown = await response.json();
    if (
      typeof body === "object" &&
      body !== null &&
      "status" in body &&
      body.status === "ok"
    ) {
      return { state: "up" };
    }
    return { state: "down", reason: "unexpected answer" };
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error);
    return { state: "down", reason };
  }
}
