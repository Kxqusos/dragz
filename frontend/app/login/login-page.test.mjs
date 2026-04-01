import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const source = readFileSync(join(import.meta.dirname, "page.tsx"), "utf8");

test("surfaces registration as a simple inline link instead of a separate side block", () => {
  assert.match(source, /href="\/register"/);
  assert.match(source, /Нет аккаунта\?/);
  assert.match(source, /Зарегистрироваться/);
  assert.doesNotMatch(source, /Создать аккаунт/);
  assert.doesNotMatch(source, /styles\.sideCardOffset/);
  assert.doesNotMatch(source, /styles\.textLink/);
});

test("keeps password recovery available from the login page", () => {
  assert.match(source, /href="\/forgot-password"/);
});
