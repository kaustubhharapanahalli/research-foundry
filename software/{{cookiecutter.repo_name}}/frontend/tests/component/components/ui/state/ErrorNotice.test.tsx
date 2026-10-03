import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ErrorNotice } from "@/components/ui/state/ErrorNotice";

describe("ErrorNotice", () => {
  it("alerts with a default title and retries on request", () => {
    const retry = vi.fn();
    render(<ErrorNotice onRetry={retry} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Something went wrong");
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(retry).toHaveBeenCalledOnce();
  });

  it("shows the title it is given", () => {
    render(<ErrorNotice title="The backend is down" onRetry={vi.fn()} />);
    expect(
      screen.getByRole("heading", { name: "The backend is down" }),
    ).toBeInTheDocument();
  });
});
