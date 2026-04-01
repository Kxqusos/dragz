import { proxyToBackend } from "@/app/api/_lib/proxy";

function toPath(pathSegments: string[] | undefined): string {
  return `/api/admin/${(pathSegments ?? []).join("/")}`;
}

export async function GET(
  request: Request,
  context: { params: Promise<{ path?: string[] }> },
): Promise<Response> {
  const { path } = await context.params;
  return proxyToBackend(request, toPath(path));
}

export async function PUT(
  request: Request,
  context: { params: Promise<{ path?: string[] }> },
): Promise<Response> {
  const { path } = await context.params;
  return proxyToBackend(request, toPath(path));
}

export async function PATCH(
  request: Request,
  context: { params: Promise<{ path?: string[] }> },
): Promise<Response> {
  const { path } = await context.params;
  return proxyToBackend(request, toPath(path));
}
