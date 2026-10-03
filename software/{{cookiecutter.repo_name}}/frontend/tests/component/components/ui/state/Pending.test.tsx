import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Pending } from "@/components/ui/state/Pending";

describe("Pending", () => {
  it("announces a default wait", () => {
    render(<Pending />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading…");
  });

  it("announces the wait it is given", () => {
    render(<Pending label="Checking the backend…" />);
    expect(screen.getByRole("status")).toHaveTextContent(
      "Checking the backend…",
    );
  });
});
