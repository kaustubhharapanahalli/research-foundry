// The backend states the tests render, in one place.
import type { Health } from "@/types/health";

export const UP: Health = { state: "up" };
export const DOWN: Health = { state: "down", reason: "HTTP 502" };
