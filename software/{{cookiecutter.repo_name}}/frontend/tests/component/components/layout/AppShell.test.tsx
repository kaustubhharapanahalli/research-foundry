import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AppShell } from "@/components/layout/AppShell";
import { NAVIGATION } from "@/config/navigation";

describe("AppShell", () => {
  it("frames the page with a skip link, the navigation and one main", () => {
    render(
      <AppShell title="Example">
        <p>content</p>
      </AppShell>,
    );
    expect(
      screen.getByRole("link", { name: "Skip to content" }),
    ).toHaveAttribute("href", "#main");
    const nav = screen.getByRole("navigation", { name: "Main" });
    for (const item of NAVIGATION) {
      expect(nav).toContainElement(
        screen.getByRole("link", { name: item.label }),
      );
    }
    expect(screen.getByRole("main")).toHaveTextContent("content");
    expect(screen.getByText("Example")).toBeInTheDocument();
  });
});
