import type { NextConfig } from "next";

import { securityHeaders } from "./config/security";

// `make frontend-coverage` builds with COVERAGE=1: source maps on and
// minification off, so end-to-end coverage maps back to each source line.
// The production image is built without it.
const coverage = process.env.COVERAGE === "1";

const config: NextConfig = {
  output: "standalone",
  // This folder is its own pnpm project: trace from here, not from a
  // lockfile Next might find further up.
  outputFileTracingRoot: import.meta.dirname,
  typedRoutes: true,
  poweredByHeader: false,
  productionBrowserSourceMaps: coverage,
  experimental: {
    serverSourceMaps: coverage,
    turbopackMinify: !coverage,
    serverMinification: !coverage,
  },
  // No images.remotePatterns: remote images stay off until a project needs
  // them and reviews the risk.
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default config;
