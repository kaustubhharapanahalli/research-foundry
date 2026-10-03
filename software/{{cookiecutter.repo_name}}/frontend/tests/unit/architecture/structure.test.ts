// The naming and styling rules of the web structure, which no lint rule
// covers: component names, module stylesheets, and where colours live.
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const ROOT = path.join(import.meta.dirname, "..", "..", "..");
const SOURCES = [
  "app",
  "features",
  "components",
  "hooks",
  "lib",
  "config",
  "styles",
  "types",
];

function walk(dir: string): string[] {
  let entries: string[];
  try {
    entries = readdirSync(dir);
  } catch {
    return [];
  }
  return entries.flatMap((name) => {
    const full = path.join(dir, name);
    return statSync(full).isDirectory() ? walk(full) : [full];
  });
}

const files = SOURCES.flatMap((dir) => walk(path.join(ROOT, dir))).map((file) =>
  path.relative(ROOT, file),
);

describe("the source tree", () => {
  it("names every component file in PascalCase", () => {
    const components = files.filter(
      (file) => file.includes("/components/") && file.endsWith(".tsx"),
    );
    expect(components.length).toBeGreaterThan(0);
    for (const file of components) {
      expect(path.basename(file)).toMatch(/^[A-Z][A-Za-z0-9]*\.tsx$/);
    }
  });

  it("puts every module stylesheet beside its component", () => {
    for (const file of files.filter((name) => name.endsWith(".module.css"))) {
      const component = file.replace(/\.module\.css$/, ".tsx");
      expect(files, file).toContain(component);
    }
  });

  it("keeps raw colours in styles/tokens.css only", () => {
    const hex = /#[0-9a-fA-F]{3,8}\b/;
    for (const file of files.filter((name) => /\.(css|tsx?)$/.test(name))) {
      if (file === path.join("styles", "tokens.css")) continue;
      expect(readFileSync(path.join(ROOT, file), "utf8"), file).not.toMatch(
        hex,
      );
    }
  });
});
