import { proxyToBackend } from "@/app/api/_lib/proxy";

export async function GET(request: Request): Promise<Response> {
  return proxyToBackend(request, "/api/cart");
}

export async function PUT(request: Request): Promise<Response> {
  return proxyToBackend(request, "/api/cart");
}
