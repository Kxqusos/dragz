const DEFAULT_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;

export function readJsonCookie<T>(name: string): T | null {
  if (typeof document === "undefined") {
    return null;
  }

  const cookiePrefix = `${encodeURIComponent(name)}=`;
  const rawCookie = document.cookie
    .split("; ")
    .find((entry) => entry.startsWith(cookiePrefix));

  if (!rawCookie) {
    return null;
  }

  const rawValue = rawCookie.slice(cookiePrefix.length);
  try {
    return JSON.parse(decodeURIComponent(rawValue)) as T;
  } catch {
    return null;
  }
}

export function writeJsonCookie(name: string, value: unknown, maxAgeSeconds = DEFAULT_MAX_AGE_SECONDS): void {
  if (typeof document === "undefined") {
    return;
  }

  document.cookie = [
    `${encodeURIComponent(name)}=${encodeURIComponent(JSON.stringify(value))}`,
    "Path=/",
    `Max-Age=${maxAgeSeconds}`,
    "SameSite=Lax",
  ].join("; ");
}

export function deleteCookie(name: string): void {
  if (typeof document === "undefined") {
    return;
  }

  document.cookie = [
    `${encodeURIComponent(name)}=`,
    "Path=/",
    "Max-Age=0",
    "SameSite=Lax",
  ].join("; ");
}
