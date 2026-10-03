import type { Health } from "@/types/health";

import { describeHealth } from "@/features/status/model/describe";

import styles from "./BackendStatus.module.css";
import { RefreshButton } from "./RefreshButton";

export function BackendStatus({ health }: { health: Health }) {
  const view = describeHealth(health);
  return (
    <section className={styles.panel} aria-labelledby="backend-status">
      <h2 id="backend-status" className={styles[view.tone]}>
        {view.label}
      </h2>
      <p>{view.detail}</p>
      <RefreshButton />
    </section>
  );
}
