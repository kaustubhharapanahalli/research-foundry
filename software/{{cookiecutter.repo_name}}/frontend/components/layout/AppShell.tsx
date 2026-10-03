import Link from "next/link";
import type { ReactNode } from "react";

import { NAVIGATION } from "@/config/navigation";

import styles from "./AppShell.module.css";

/** The frame around every page: skip link, header, navigation and main. */
export function AppShell({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <>
      <a className={styles.skip} href="#main">
        Skip to content
      </a>
      <header className={styles.header}>
        <span className={styles.title}>{title}</span>
        <nav aria-label="Main">
          <ul className={styles.links}>
            {NAVIGATION.map((item) => (
              <li key={item.href}>
                <Link href={item.href}>{item.label}</Link>
              </li>
            ))}
          </ul>
        </nav>
      </header>
      <main id="main" className={styles.main}>
        {children}
      </main>
    </>
  );
}
