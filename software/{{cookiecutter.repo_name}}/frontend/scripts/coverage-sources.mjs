// Which sources the frontend's coverage counts, shared by the unit run
// (vitest.config.ts) and the merge (scripts/coverage.mjs).
export const SOURCE_DIRS = [
  "app",
  "features",
  "components",
  "hooks",
  "lib",
  "config",
];
const SOURCE = new RegExp(`^(${SOURCE_DIRS.join("|")})/.*\\.tsx?$`);
export const ours = (path) =>
  SOURCE.test(path) && !path.includes("__nextjs-internal");

// Turbopack names sources "[project]/<path>".
export const clean = (path) => path.replace(/^\[project\]\//, "");

export const unitCoverage = {
  name: "unit",
  outputDir: "coverage/unit",
  reports: ["raw"],
  sourceFilter: (path) => ours(clean(path)),
  sourcePath: (path) => clean(path),
  logging: "error",
};
