import { proxyToBackend } from "@/app/api/_lib/proxy";

export async function GET(request: Request): Promise<Response> {
  return proxyToBackend(request, "/api/me");
}
