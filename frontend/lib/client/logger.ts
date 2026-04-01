type LogPayload = Record<string, unknown>;

export function logUiEvent(event: string, payload: LogPayload = {}): void {
  const timestamp = new Date().toISOString();
  console.info(`[tabletki-ui] ${timestamp} ${event}`, payload);

  if (typeof window === "undefined") {
    return;
  }

  void fetch("/api/debug-events", {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      event,
      route: window.location.pathname,
      metadata: sanitizePayload(payload)
    })
  }).catch(() => {});
}

function sanitizePayload(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => sanitizePayload(item));
  }
  if (!value || typeof value !== "object") {
    return value;
  }

  return Object.fromEntries(
    Object.entries(value).map(([key, entryValue]) => {
      if (/password|token|cookie|secret|code/i.test(key)) {
        return [key, "[redacted]"];
      }
      return [key, sanitizePayload(entryValue)];
    })
  );
}
