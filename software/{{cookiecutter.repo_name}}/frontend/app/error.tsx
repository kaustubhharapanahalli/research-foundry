"use client";

import { useEffect } from "react";

import { ErrorNotice } from "@/components/ui/state/ErrorNotice";

export default function RouteError({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return <ErrorNotice onRetry={retry} />;
}
