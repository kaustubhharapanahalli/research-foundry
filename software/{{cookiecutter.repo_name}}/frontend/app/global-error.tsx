"use client";

import { ErrorNotice } from "@/components/ui/state/ErrorNotice";

import "@/styles/globals.css";

export default function GlobalError({ retry }: { retry: () => void }) {
  // Replaces the root layout when it fails, so it renders its own <html>
  // and has no AppShell to sit in.
  return (
    <html lang="en">
      <body>
        <main>
          <ErrorNotice onRetry={retry} />
        </main>
      </body>
    </html>
  );
}
