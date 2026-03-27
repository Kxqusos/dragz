import { proxyToBackend } from "@/app/api/_lib/proxy";

export async function POST(request: Request): Promise<Response> {
  return proxyToBackend(request, "/api/search");
}
