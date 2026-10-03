import styles from "./Pending.module.css";

/** A wait the reader can see and a screen reader announces. */
export function Pending({ label = "Loading…" }: { label?: string }) {
  return (
    <p role="status" className={styles.pending}>
      {label}
    </p>
  );
}
