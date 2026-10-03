import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AppShell } from "@/components/layout/AppShell";

import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "{{ cookiecutter.project_name }}",
  description: "{{ cookiecutter.description }}",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppShell title="{{ cookiecutter.project_name }}">{children}</AppShell>
      </body>
    </html>
  );
}
