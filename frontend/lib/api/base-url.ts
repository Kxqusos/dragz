function normalizeBackendUrl(value: string): string {
  return value.replace(/\/+$/, "");
}

export function getBackendUrl(): string {
  const configuredUrl = process.env.NEXT_PUBLIC_BACKEND_URL?.trim();
  if (configuredUrl) {
    return normalizeBackendUrl(configuredUrl);
  }
  return "";
}
