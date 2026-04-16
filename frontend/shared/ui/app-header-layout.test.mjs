import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const source = readFileSync(join(import.meta.dirname, "app-header.module.css"), "utf8");

test("uses symmetric header columns so center navigation stays visually centered", () => {
  assert.match(source, /\.shell\s*\{[\s\S]*grid-template-columns:\s*minmax\(0,\s*1fr\)\s+auto\s+minmax\(0,\s*1fr\);/);
});

test("anchors side blocks to the grid edges and keeps nav centered", () => {
  assert.match(source, /\.brand\s*\{[\s\S]*justify-self:\s*start;/);
  assert.match(source, /\.nav\s*\{[\s\S]*justify-self:\s*center;/);
  assert.match(source, /\.utilityNav\s*\{[\s\S]*justify-self:\s*end;/);
});
