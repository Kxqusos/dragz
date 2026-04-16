import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const source = readFileSync(join(import.meta.dirname, "AppHeader.tsx"), "utf8");

test("keeps login entry in header and moves registration out of it", () => {
  assert.match(source, /href="\/login"/);
  assert.doesNotMatch(source, /href="\/register"/);
  assert.match(source, /Личный кабинет/);
});

test("shows personal account in auth area and removes cabinet from main sections", () => {
  assert.match(source, /href="\/account"/);
  assert.match(source, /Личный кабинет/);
  assert.doesNotMatch(source, /\{\s*href:\s*"\/account",\s*label:\s*"Кабинет"\s*\}/);
});

test("includes admin navigation and logout action for authenticated users", () => {
  assert.match(source, /href="\/admin"/);
  assert.match(source, /logout/i);
});

test("keeps brand metadata but removes the primary search action", () => {
  assert.doesNotMatch(source, /Найти сейчас/);
  assert.match(source, /Безрецептурный навигатор/);
});

test("keeps the header concise without extra helper copy", () => {
  assert.doesNotMatch(source, /Разделы сервиса/);
  assert.doesNotMatch(source, /Поиск аптек и ИИ-консультация собраны в одном ритме без лишних переходов/);
  assert.doesNotMatch(source, /Сравните аптеки, сохраните корзину и переключайтесь между поиском и OTC-консультацией без потери истории/);
  assert.doesNotMatch(source, /Войдите, чтобы сохранить корзину, историю поиска и чат/);
});
