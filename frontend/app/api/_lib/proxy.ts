const DEFAULT_BACKEND_INTERNAL_URL = "http://127.0.0.1:8000";

function getBackendInternalUrl(): string {
  return (process.env.BACKEND_INTERNAL_URL?.trim() || DEFAULT_BACKEND_INTERNAL_URL).replace(/\/+$/, "");
}

export async function proxyToBackend(request: Request, path: string): Promise<Response> {
  const upstreamUrl = `${getBackendInternalUrl()}${path}`;
  const body = await request.text();
  const headers = new Headers();
  const contentType = request.headers.get("content-type");

  if (contentType) {
    headers.set("content-type", contentType);
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

  return new Response(await upstreamResponse.arrayBuffer(), {
    status: upstreamResponse.status,
    headers: responseHeaders,
  });
}
