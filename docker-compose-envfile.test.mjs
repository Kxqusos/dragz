import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

const composeSource = readFileSync(new URL("./docker-compose.yml", import.meta.url), "utf8");

test("backend loads variables from backend/.env", () => {
  assert.match(
    composeSource,
    /backend:\n(?:.*\n)*?\s+env_file:\n\s+- \.\/backend\/\.env/
  );
});

test("geocode-refresh loads variables from backend/.env", () => {
  assert.match(
    composeSource,
    /geocode-refresh:\n(?:.*\n)*?\s+env_file:\n\s+- \.\/backend\/\.env/
  );
});
