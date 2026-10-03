// Lint: Next's rules, accessibility, and the import boundaries of the web
// structure: app -> features -> components, hooks -> lib, types -> styles.
import { existsSync, readdirSync } from "node:fs";

import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import jsxA11y from "eslint-plugin-jsx-a11y";

const FEATURES = existsSync("features") ? readdirSync("features") : [];

const config = [
  ...nextVitals,
  ...nextTs,
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "coverage/**",
      "playwright-report/**",
      "test-results/**",
      "next-env.d.ts",
    ],
  },
  // eslint-config-next registers jsx-a11y with a few rules; this turns on
  // the plugin's whole recommended set.
  { rules: jsxA11y.flatConfigs.recommended.rules },
  {
    rules: {
      "import/no-restricted-paths": [
        "error",
        {
          zones: [
            ...FEATURES.map((name) => ({
              target: `./features/${name}`,
              from: "./features",
              except: [`./${name}`],
              message:
                "A feature may not import another feature; move the shared part to components/, hooks/ or lib/.",
            })),
            {
              target: ["./components", "./hooks", "./lib", "./types"],
              from: ["./features", "./app"],
              message: "Shared layers may not depend on a feature or a route.",
            },
            {
              target: ["./lib", "./types"],
              from: ["./components", "./hooks"],
              message: "lib/ and types/ hold no React.",
            },
            {
              target: ["./components", "./hooks", "./features"],
              from: "./lib/server",
              message:
                "lib/server is server-only; pass its data down as props.",
            },
          ],
        },
      ],
      "import/no-cycle": ["error", { maxDepth: 4 }],
      "import/no-default-export": "error",
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["../*", "../**"],
              message: "Use @/… to leave the folder.",
            },
          ],
        },
      ],
    },
  },
  {
    // Next requires default exports here, and so do the config files.
    files: ["app/**", "*.config.{ts,mjs}"],
    rules: { "import/no-default-export": "off" },
  },
];

export default config;
