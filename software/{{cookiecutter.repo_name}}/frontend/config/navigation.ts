import type { Route } from "next";

/** One link in the site's main navigation. */
export interface NavigationItem {
  readonly href: Route;
  readonly label: string;
}

/**
 * The one list of routes the navigation shows. The accessibility sweep
 * visits every entry, so a new page is checked as soon as it is linked.
 */
export const NAVIGATION: readonly NavigationItem[] = [
  { href: "/", label: "Home" },
];
