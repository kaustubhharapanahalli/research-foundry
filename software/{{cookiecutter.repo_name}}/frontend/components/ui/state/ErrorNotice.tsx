"use client";

import styles from "./ErrorNotice.module.css";

/** A failure the reader can act on: what happened, and a way to retry. */
export function ErrorNotice({
  title = "Something went wrong",
  onRetry,
}: {
  title?: string;
  onRetry: () => void;
}) {
  return (
    <section role="alert" className={styles.notice}>
      <h1>{title}</h1>
      <button type="button" onClick={() => onRetry()}>
        Try again
      </button>
    </section>
  );
}
