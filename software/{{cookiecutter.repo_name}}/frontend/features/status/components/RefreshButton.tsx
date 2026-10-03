"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";

/** Re-render the page on the server, so the health check runs again. */
export function RefreshButton() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  return (
    <button
      type="button"
      disabled={pending}
      onClick={() => startTransition(() => router.refresh())}
    >
      {pending ? "Checking…" : "Check again"}
    </button>
  );
}
