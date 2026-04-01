const DEFAULT_BACKEND_INTERNAL_URL = "http://127.0.0.1:8000";

function getBackendInternalUrl(): string {
  return (process.env.BACKEND_INTERNAL_URL?.trim() || DEFAULT_BACKEND_INTERNAL_URL).replace(/\/+$/, "");
}

export async function proxyToBackend(request: Request, path: string): Promise<Response> {
  const upstreamUrl = `${getBackendInternalUrl()}${path}`;
  const body = await request.text();
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const cookie = request.headers.get("cookie");

  if (contentType) {
    headers.set("content-type", contentType);
  }
  if (cookie) {
    headers.set("cookie", cookie);
  }

  const upstreamResponse = await fetch(upstreamUrl, {
    method: request.method,
    headers,
    body: body.length > 0 ? body : undefined,
    cache: "no-store",
  });

  const responseHeaders = new Headers();
  const upstreamContentType = upstreamResponse.headers.get("content-type");
  const upstreamRequestId = upstreamResponse.headers.get("x-request-id");

  if (upstreamContentType) {
    responseHeaders.set("content-type", upstreamContentType);
  }
  if (upstreamRequestId) {
    responseHeaders.set("x-request-id", upstreamRequestId);
  }
  const setCookieHeaders = typeof upstreamResponse.headers.getSetCookie === "function"
    ? upstreamResponse.headers.getSetCookie()
    : [];
  if (setCookieHeaders.length > 0) {
    for (const setCookieHeader of setCookieHeaders) {
      responseHeaders.append("set-cookie", setCookieHeader);
    }
  } else {
    const setCookieHeader = upstreamResponse.headers.get("set-cookie");
    if (setCookieHeader) {
      responseHeaders.set("set-cookie", setCookieHeader);
    }
  }

  return new Response(await upstreamResponse.arrayBuffer(), {
    status: upstreamResponse.status,
    headers: responseHeaders,
  });
}
