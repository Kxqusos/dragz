import assert from "node:assert/strict";
import test from "node:test";

import { proxyToBackend } from "./proxy.ts";

test("forwards cookie headers upstream and propagates set-cookie downstream", async () => {
  const originalFetch = global.fetch;
  let upstreamInit = null;

  global.fetch = async (url, init) => {
    upstreamInit = init;
    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: {
        "content-type": "application/json",
        "x-request-id": "req-123",
        "set-cookie": "tabletki_access_token=abc; Path=/; HttpOnly",
      },
    });
  };

  try {
    const request = new Request("http://127.0.0.1:3000/api/auth/login", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        cookie: "tabletki_anon_id=anon-1",
      },
      body: JSON.stringify({ email: "user@example.com" }),
    });

    const response = await proxyToBackend(request, "/api/auth/login");

    assert.equal(upstreamInit.headers.get("cookie"), "tabletki_anon_id=anon-1");
    assert.equal(response.headers.get("x-request-id"), "req-123");
    assert.equal(
      response.headers.get("set-cookie"),
      "tabletki_access_token=abc; Path=/; HttpOnly",
    );
  } finally {
    global.fetch = originalFetch;
  }
});
