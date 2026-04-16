import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const source = readFileSync(join(import.meta.dirname, "page.tsx"), "utf8");

test("requires consent checkbox and links to terms and privacy pages", () => {
  assert.match(source, /type="checkbox"/);
  assert.match(source, /href="\/terms"/);
  assert.match(source, /href="\/privacy"/);
});

test("requires password confirmation and shows password requirements only for invalid passwords", () => {
  assert.match(source, /Повторите пароль/);
  assert.match(source, /Пароль должен содержать минимум 8 символов, маленькие и большие буквы, а также цифры/);
  assert.match(source, /confirmPassword/);
  assert.match(source, /const passwordRequirementsMismatch = password.length > 0 && !hasRequiredPasswordComplexity\(password\);/);
  assert.match(source, /passwordRequirementsMismatch \? <p className=\{styles\.error\}>/);
  assert.doesNotMatch(source, /<p className=\{styles\.meta\}>\s*\{PASSWORD_REQUIREMENTS_MESSAGE\}\s*<\/p>/);
  assert.doesNotMatch(source, /minLength={8}/);
});

test("does not keep the old registration intro paragraph", () => {
  assert.doesNotMatch(source, /Создайте аккаунт по email и паролю, затем подтвердите email кодом/);
});
