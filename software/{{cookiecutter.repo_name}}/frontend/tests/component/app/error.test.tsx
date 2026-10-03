import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import GlobalError from "@/app/global-error";
import RouteError from "@/app/error";

describe("the error boundaries", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("logs the error and retries on request", () => {
    const log = vi.spyOn(console, "error").mockImplementation(() => {});
    const retry = vi.fn();
    const error = new Error("boom");
    render(<RouteError error={error} retry={retry} />);
    expect(log).toHaveBeenCalledWith(error);
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(retry).toHaveBeenCalledOnce();
  });

  it("replaces the root layout and retries on request", () => {
    // GlobalError renders its own <html>, which React warns about inside
    // the test's <div>; the warning is expected here.
    vi.spyOn(console, "error").mockImplementation(() => {});
    const retry = vi.fn();
    render(<GlobalError retry={retry} />);
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(retry).toHaveBeenCalledOnce();
  });
});
