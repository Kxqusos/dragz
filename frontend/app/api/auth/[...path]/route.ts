import { proxyToBackend } from "@/app/api/_lib/proxy";

function toPath(pathSegments: string[] | undefined): string {
  return `/api/auth/${(pathSegments ?? []).join("/")}`;
}

export async function POST(
  request: Request,
  context: { params: Promise<{ path?: string[] }> },
): Promise<Response> {
  const { path } = await context.params;
  return proxyToBackend(request, toPath(path));
}
