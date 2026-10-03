/** What the frontend knows about the backend after one health check. */
export type Health = { state: "up" } | { state: "down"; reason: string };
