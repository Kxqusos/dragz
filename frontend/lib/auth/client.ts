import type { AIConversationPayload } from "@/lib/ai-chat/types";
import type { CartItem } from "@/features/search/model/types";
import type { AuthUser, DebugEvent, GuestMergePayload, SearchHistoryEntry, SiteSettingItem } from "@/lib/auth/types";
import { getBackendUrl } from "@/lib/api/base-url";

function apiUrl(path: string): string {
  return `${getBackendUrl()}${path}`;
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function getCurrentUser(): Promise<AuthUser | null> {
  const response = await fetch(apiUrl("/api/me"), {
    credentials: "include",
    cache: "no-store",
  });
  if (response.status === 401) {
    return null;
  }
  const data = await parseResponse<{
    id: string;
    email: string;
    role: "user" | "admin";
    is_blocked: boolean;
    is_email_verified: boolean;
    created_at: string;
  }>(response);
  return {
    id: data.id,
    email: data.email,
    role: data.role,
    isBlocked: data.is_blocked,
    isEmailVerified: data.is_email_verified,
    createdAt: data.created_at,
  };
}

export async function registerUser(email: string, password: string, acceptedTerms: boolean): Promise<void> {
  await parseResponse(
    await fetch(apiUrl("/api/auth/register"), {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, acceptedTerms }),
    }),
  );
}

export async function verifyEmailCode(email: string, code: string): Promise<void> {
  await parseResponse(
    await fetch(apiUrl("/api/auth/verify-email"), {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code }),
    }),
  );
}

export async function resendVerificationCode(email: string): Promise<void> {
  await parseResponse(
    await fetch(apiUrl("/api/auth/resend-verification-code"), {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    }),
  );
}

export async function loginUser(email: string, password: string): Promise<void> {
  await parseResponse(
    await fetch(apiUrl("/api/auth/login"), {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    }),
  );
}

export async function logoutUser(): Promise<void> {
  await parseResponse(
    await fetch(apiUrl("/api/auth/logout"), {
      method: "POST",
      credentials: "include",
    }),
  );
}

export async function forgotPassword(email: string): Promise<void> {
  await parseResponse(
    await fetch(apiUrl("/api/auth/forgot-password"), {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    }),
  );
}

export async function resetPassword(email: string, code: string, password: string): Promise<void> {
  await parseResponse(
    await fetch(apiUrl("/api/auth/reset-password"), {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code, password }),
    }),
  );
}

export async function mergeGuestState(payload: GuestMergePayload): Promise<void> {
  const isEmpty =
    payload.cartItems.length === 0 &&
    payload.searchHistory.length === 0 &&
    payload.aiConversation.length === 0;
  if (isEmpty) {
    return;
  }
  await parseResponse(
    await fetch(apiUrl("/api/state/merge-guest"), {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  );
}

export async function loadCart(): Promise<CartItem[]> {
  const data = await parseResponse<{
    items: Array<{
      pharmacy_id: string;
      pharmacy_name: string;
      address: string;
      lat: number;
      lon: number;
      price: number;
      in_stock: boolean;
      quantity_label: string;
      matched_drug: string;
    }>;
  }>(
    await fetch(apiUrl("/api/cart"), {
      credentials: "include",
      cache: "no-store",
    }),
  );
  return data.items.map((item) => ({
    pharmacyId: item.pharmacy_id,
    pharmacyName: item.pharmacy_name,
    address: item.address,
    lat: item.lat,
    lon: item.lon,
    price: item.price,
    inStock: item.in_stock,
    quantityLabel: item.quantity_label,
    matchedDrug: item.matched_drug,
  }));
}

export async function saveCart(items: CartItem[]): Promise<void> {
  await parseResponse(
    await fetch(apiUrl("/api/cart"), {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cartItems: items }),
    }),
  );
}

export async function loadSearchHistory(): Promise<SearchHistoryEntry[]> {
  const data = await parseResponse<{ items: Array<{ query: string; created_at: string; metadata: Record<string, unknown> }> }>(
    await fetch(apiUrl("/api/history/search"), {
      credentials: "include",
      cache: "no-store",
    }),
  );
  return data.items.map((item) => ({
    query: item.query,
    createdAt: item.created_at,
    metadata: item.metadata,
  }));
}

export async function loadAIHistory(): Promise<AIConversationPayload[]> {
  const data = await parseResponse<{ items: AIConversationPayload[] }>(
    await fetch(apiUrl("/api/history/ai"), {
      credentials: "include",
      cache: "no-store",
    }),
  );
  return data.items;
}

export async function loadAdminUsers(): Promise<AuthUser[]> {
  const data = await parseResponse<{ items: Array<{ id: string; email: string; role: "user" | "admin"; is_blocked: boolean; is_email_verified: boolean; created_at: string }> }>(
    await fetch(apiUrl("/api/admin/users"), {
      credentials: "include",
      cache: "no-store",
    }),
  );
  return data.items.map((item) => ({
    id: item.id,
    email: item.email,
    role: item.role,
    isBlocked: item.is_blocked,
    isEmailVerified: item.is_email_verified,
    createdAt: item.created_at,
  }));
}

export async function loadAdminSettings(): Promise<SiteSettingItem[]> {
  const data = await parseResponse<{ items: SiteSettingItem[] }>(
    await fetch(apiUrl("/api/admin/settings"), {
      credentials: "include",
      cache: "no-store",
    }),
  );
  return data.items;
}

export async function updateAdminSettings(items: SiteSettingItem[]): Promise<SiteSettingItem[]> {
  const data = await parseResponse<{ items: SiteSettingItem[] }>(
    await fetch(apiUrl("/api/admin/settings"), {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items }),
    }),
  );
  return data.items;
}

export async function loadDebugEvents(): Promise<DebugEvent[]> {
  const data = await parseResponse<{ items: Array<{
    id: number;
    event: string;
    route: string | null;
    request_id: string | null;
    user_agent: string | null;
    ip_hash: string | null;
    anonymous_id: string | null;
    metadata: Record<string, unknown>;
    created_at: string;
  }> }>(
    await fetch(apiUrl("/api/admin/debug-events"), {
      credentials: "include",
      cache: "no-store",
    }),
  );
  return data.items.map((item) => ({
    id: item.id,
    event: item.event,
    route: item.route,
    requestId: item.request_id,
    userAgent: item.user_agent,
    ipHash: item.ip_hash,
    anonymousId: item.anonymous_id,
    metadata: item.metadata,
    createdAt: item.created_at,
  }));
}
