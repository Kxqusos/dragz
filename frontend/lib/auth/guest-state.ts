import type { AIConversationItem } from "@/lib/ai-chat/types";
import type { CartItem } from "@/lib/mvp/types";
import type { GuestMergePayload, SearchHistoryEntry } from "@/lib/auth/types";
import { deleteCookie, readJsonCookie, writeJsonCookie } from "@/lib/client/cookies";

export const CART_COOKIE_NAME = "tabletki_cart_v1";
export const AI_CHAT_COOKIE_NAME = "tabletki_ai_chat_v1";
export const SEARCH_HISTORY_STORAGE_KEY = "tabletki_search_history_v1";

export function readGuestCart(): CartItem[] {
  return readJsonCookie<CartItem[]>(CART_COOKIE_NAME) ?? [];
}

export function writeGuestCart(items: CartItem[]): void {
  if (items.length === 0) {
    deleteCookie(CART_COOKIE_NAME);
    return;
  }
  writeJsonCookie(CART_COOKIE_NAME, items);
}

export function readGuestAIConversation(): AIConversationItem[] {
  return readJsonCookie<AIConversationItem[]>(AI_CHAT_COOKIE_NAME) ?? [];
}

export function writeGuestAIConversation(items: AIConversationItem[]): void {
  if (items.length === 0) {
    deleteCookie(AI_CHAT_COOKIE_NAME);
    return;
  }
  writeJsonCookie(AI_CHAT_COOKIE_NAME, items);
}

export function readGuestSearchHistory(): SearchHistoryEntry[] {
  if (typeof window === "undefined") {
    return [];
  }
  try {
    const raw = window.localStorage.getItem(SEARCH_HISTORY_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as SearchHistoryEntry[]) : [];
  } catch {
    return [];
  }
}

export function appendGuestSearchHistory(query: string): void {
  if (typeof window === "undefined") {
    return;
  }
  const current = readGuestSearchHistory();
  const next = [
    { query, createdAt: new Date().toISOString(), metadata: {} },
    ...current.filter((item) => item.query !== query),
  ].slice(0, 20);
  window.localStorage.setItem(SEARCH_HISTORY_STORAGE_KEY, JSON.stringify(next));
}

export function clearGuestState(): void {
  deleteCookie(CART_COOKIE_NAME);
  deleteCookie(AI_CHAT_COOKIE_NAME);
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(SEARCH_HISTORY_STORAGE_KEY);
  }
}

export function buildGuestMergePayload(): GuestMergePayload {
  return {
    cartItems: readGuestCart(),
    searchHistory: readGuestSearchHistory(),
    aiConversation: readGuestAIConversation(),
  };
}
