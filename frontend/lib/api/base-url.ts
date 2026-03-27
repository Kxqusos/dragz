const DEFAULT_LOCAL_BACKEND_URL = "http://127.0.0.1:8000";

function normalizeBackendUrl(value: string): string {
  return value.replace(/\/+$/, "");
}

export function getBackendUrl(): string {
  const configuredUrl = process.env.NEXT_PUBLIC_BACKEND_URL?.trim();
  if (configuredUrl) {
    return normalizeBackendUrl(configuredUrl);
  }

  if (typeof window !== "undefined") {
    const { hostname } = window.location;
    if (hostname !== "localhost" && hostname !== "127.0.0.1") {
      return "";
    }
  }

  return DEFAULT_LOCAL_BACKEND_URL;
}
