import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const source = readFileSync(join(import.meta.dirname, "auth.module.css"), "utf8");

test("keeps shared auth cards centered for standalone pages", () => {
  assert.match(source, /\.card\s*\{[\s\S]*max-width:\s*560px;/);
  assert.match(source, /\.card\s*\{[\s\S]*margin:\s*0 auto;/);
});

test("does not keep obsolete login split-layout overrides", () => {
  assert.doesNotMatch(source, /\.authSplit\s*>\s*\.card\s*\{/);
});
