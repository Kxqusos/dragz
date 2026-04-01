import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const source = readFileSync(join(import.meta.dirname, "page.tsx"), "utf8");

test("does not show the reset-form shortcut copy", () => {
  assert.doesNotMatch(source, /Уже получили код\?/);
  assert.doesNotMatch(source, /Открыть форму смены пароля/);
});
