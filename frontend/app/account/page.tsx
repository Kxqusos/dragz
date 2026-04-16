"use client";

import { useEffect, useState } from "react";
import { getCurrentUser, loadAIHistory, loadCart, loadSearchHistory } from "@/lib/auth/client";
import type { AuthUser, SearchHistoryEntry } from "@/lib/auth/types";
import type { AIConversationPayload } from "@/lib/ai-chat/types";
import type { CartItem } from "@/features/search/model/types";
import styles from "../auth.module.css";

export default function AccountPage() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [searchHistory, setSearchHistory] = useState<SearchHistoryEntry[]>([]);
  const [aiHistory, setAIHistory] = useState<AIConversationPayload[]>([]);

  useEffect(() => {
    void getCurrentUser().then((currentUser) => {
      setUser(currentUser);
      if (!currentUser) {
        return;
      }
      void loadCart().then(setCartItems);
      void loadSearchHistory().then(setSearchHistory);
      void loadAIHistory().then(setAIHistory);
    });
  }, []);

  if (!user) {
    return (
      <main className={styles.page}>
        <section className={styles.card}>
          <h1 className={styles.title}>Кабинет</h1>
          <p className={styles.subtitle}>Войдите в аккаунт, чтобы увидеть корзину и историю.</p>
        </section>
      </main>
    );
  }

  return (
    <main className={styles.page}>
      <div className={styles.grid}>
        <section className={styles.panel}>
          <h1 className={styles.title}>Кабинет</h1>
          <p className={styles.subtitle}>{user.email}</p>
          <p className={styles.meta}>Роль: {user.role}. Email подтверждён: {user.isEmailVerified ? "да" : "нет"}.</p>
        </section>

        <section className={styles.panel}>
          <h2 className={styles.title}>Корзина</h2>
          <div className={styles.list}>
            {cartItems.length === 0 ? <p className={styles.meta}>Пока пусто.</p> : null}
            {cartItems.map((item) => (
              <article key={`${item.pharmacyId}-${item.matchedDrug}`} className={styles.listItem}>
                <strong>{item.matchedDrug}</strong>
                <p className={styles.meta}>{item.pharmacyName} • {item.address} • {item.price} ₽</p>
              </article>
            ))}
          </div>
        </section>

        <section className={styles.panel}>
          <h2 className={styles.title}>История поиска</h2>
          <div className={styles.list}>
            {searchHistory.length === 0 ? <p className={styles.meta}>Запросов пока нет.</p> : null}
            {searchHistory.map((item) => (
              <article key={`${item.query}-${item.createdAt ?? ""}`} className={styles.listItem}>
                <strong>{item.query}</strong>
                <p className={styles.meta}>{item.createdAt ?? "Только что"}</p>
              </article>
            ))}
          </div>
        </section>

        <section className={styles.panel}>
          <h2 className={styles.title}>История AI-консультаций</h2>
          <div className={styles.list}>
            {aiHistory.length === 0 ? <p className={styles.meta}>Диалогов пока нет.</p> : null}
            {aiHistory.map((conversation) => (
              <article key={conversation.id} className={styles.listItem}>
                {conversation.messages.map((message, index) => (
                  <p key={`${conversation.id}-${index}`} className={styles.meta}>
                    <strong>{message.role === "assistant" ? "Консультант" : "Вы"}:</strong> {message.content}
                  </p>
                ))}
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
