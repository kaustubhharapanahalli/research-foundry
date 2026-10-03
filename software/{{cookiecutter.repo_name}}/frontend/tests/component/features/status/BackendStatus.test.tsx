import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { BackendStatus } from "@/features/status/components/BackendStatus";
import { DOWN, UP } from "@/tests/fixtures/health";

vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh: vi.fn() }) }));

describe("BackendStatus", () => {
  it("shows an up backend", () => {
    render(<BackendStatus health={UP} />);
    expect(
      screen.getByRole("heading", { name: "Backend: up" }),
    ).toBeInTheDocument();
  });

  it("shows a down backend and the reason", () => {
    render(<BackendStatus health={DOWN} />);
    expect(
      screen.getByRole("heading", { name: "Backend: down" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/HTTP 502/)).toBeInTheDocument();
  });
});
