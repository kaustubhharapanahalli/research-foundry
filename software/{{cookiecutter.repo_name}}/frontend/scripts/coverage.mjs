// Merge the unit, browser and Next-server coverage into one report, and
// fail below 90% on any measure: the frontend floor counts what the
// end-to-end tests reach as well as what the unit tests reach.
import { existsSync } from "node:fs";
import { readdir, readFile } from "node:fs/promises";
import { relative } from "node:path";

import { CoverageReport } from "monocart-coverage-reports";
import ts from "typescript";

import { clean, ours, SOURCE_DIRS } from "./coverage-sources.mjs";

const FLOOR = 90;
const MEASURES = ["statements", "branches", "functions", "lines"];
const shared = {
  sourceFilter: (path) => ours(clean(path)),
  sourcePath: (path) => clean(path),
  logging: "error",
};

// 1. Browser and Next-server V8 data, mapped through .next's source maps.
const e2e = new CoverageReport({
  ...shared,
  name: "e2e",
  outputDir: "coverage/e2e",
  reports: ["raw"],
  // Code lives in chunks; .next/server/app/*.js are loaders with no map.
  entryFilter: (entry) =>
    (entry.url.includes("/_next/static/chunks/") ||
      entry.url.includes("/.next/server/chunks/")) &&
    !entry.url.includes("_next-internal"),
  // Browser chunks name their maps by URL; read them from .next/ instead.
  sourceMapResolver: async (url, defaultResolver) => {
    const local = url.replace(/^https?:\/\/[^/]+\/_next\//, ".next/");
    if (local === url) return defaultResolver(url);
    try {
      return JSON.parse(await readFile(local, "utf8"));
    } catch {
      return null;
    }
  },
});
for (const file of await readdir("coverage/raw-browser")) {
  const data = await readFile(`coverage/raw-browser/${file}`, "utf8");
  await e2e.add(JSON.parse(data));
}
await e2e.addFromDir("coverage/raw-server");
await e2e.generate();

// 2. One report over everything, with one conversion.
const merged = new CoverageReport({
  ...shared,
  name: "frontend",
  inputDir: ["coverage/unit/raw", "coverage/e2e/raw"],
  outputDir: "coverage/merged",
  // A file no test reaches still counts, at zero. Monocart parses it as
  // JavaScript, so TypeScript compiles it first, with a map back to it.
  all: {
    dir: SOURCE_DIRS.filter((dir) => existsSync(dir)),
    filter: (path) => ours(relative(process.cwd(), path)),
    transformer: (entry) => {
      const original = entry.source;
      const output = ts.transpileModule(original, {
        fileName: entry.sourcePath,
        compilerOptions: {
          jsx: ts.JsxEmit.ReactJSX,
          module: ts.ModuleKind.ESNext,
          sourceMap: true,
          target: ts.ScriptTarget.ES2022,
        },
      });
      entry.source = output.outputText;
      // The map names the real file and carries its text, or Monocart
      // drops the file as one it cannot find.
      entry.sourceMap = {
        ...JSON.parse(output.sourceMapText),
        sources: [entry.url],
        sourcesContent: [original],
      };
    },
  },
  // The numbers printed are the numbers the floor below is checked on.
  reports: ["console-details", "lcovonly"],
});
const results = await merged.generate();

const below = MEASURES.filter((name) => results.summary[name].pct < FLOOR).map(
  (name) => `${name} ${results.summary[name].pct}%`,
);
if (below.length > 0) {
  console.error(`Frontend coverage below ${FLOOR}%: ${below.join(", ")}`);
  process.exit(1);
}
console.log(`Frontend coverage is at least ${FLOOR}% on every measure.`);
