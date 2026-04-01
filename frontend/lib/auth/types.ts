import type { AIConversationItem } from "@/lib/ai-chat/types";
import type { CartItem } from "@/lib/mvp/types";

export type AuthUser = {
  id: string;
  email: string;
  role: "user" | "admin";
  isBlocked: boolean;
  isEmailVerified: boolean;
  createdAt: string;
};

export type SearchHistoryEntry = {
  query: string;
  createdAt?: string;
  metadata?: Record<string, unknown>;
};

export type GuestMergePayload = {
  cartItems: CartItem[];
  searchHistory: SearchHistoryEntry[];
  aiConversation: AIConversationItem[];
};

export type DebugEvent = {
  id: number;
  event: string;
  route: string | null;
  requestId: string | null;
  userAgent: string | null;
  ipHash: string | null;
  anonymousId: string | null;
  metadata: Record<string, unknown>;
  createdAt: string;
};

export type SiteSettingItem = {
  key: string;
  value: unknown;
};
