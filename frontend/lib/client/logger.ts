type LogPayload = Record<string, unknown>;

export function logUiEvent(event: string, payload: LogPayload = {}): void {
  const timestamp = new Date().toISOString();
  console.info(`[tabletki-ui] ${timestamp} ${event}`, payload);
}
