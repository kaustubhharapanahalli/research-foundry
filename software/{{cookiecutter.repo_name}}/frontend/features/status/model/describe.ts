import type { Health } from "@/types/health";

/** The words and tone the status panel shows for a health check. */
export type StatusView = {
  label: string;
  detail: string;
  tone: "ok" | "danger";
};

export function describeHealth(health: Health): StatusView {
  if (health.state === "up") {
    return {
      label: "Backend: up",
      detail: "The API and its database answer.",
      tone: "ok",
    };
  }
  return {
    label: "Backend: down",
    detail: `The API did not answer (${health.reason}).`,
    tone: "danger",
  };
}
