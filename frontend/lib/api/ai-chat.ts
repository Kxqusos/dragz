import type { AIChatMessage, AIChatResponse } from "@/lib/ai-chat/types";
import { logUiEvent } from "@/lib/client/logger";

const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";

function getBackendUrl(): string {
  return process.env.NEXT_PUBLIC_BACKEND_URL ?? DEFAULT_BACKEND_URL;
}

export async function sendAIChat(messages: AIChatMessage[]): Promise<AIChatResponse> {
  logUiEvent("ai_chat_request", { messageCount: messages.length });

  const response = await fetch(`${getBackendUrl()}/api/ai-chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ messages })
  });

  if (!response.ok) {
    logUiEvent("ai_chat_error", { status: response.status });
    throw new Error(`AI chat request failed with status ${response.status}`);
  }

  const data = (await response.json()) as {
    scope_status: AIChatResponse["scopeStatus"];
    message: string;
    warnings?: string[];
    recommended_otc_drugs?: Array<{ title: string; rationale: string }>;
    handoff_cta?: { label: string; query: string } | null;
  };

  return {
    scopeStatus: data.scope_status,
    message: data.message,
    warnings: data.warnings ?? [],
    recommendedOTCDrugs: data.recommended_otc_drugs ?? [],
    handoffCTA: data.handoff_cta ?? null
  };
}
