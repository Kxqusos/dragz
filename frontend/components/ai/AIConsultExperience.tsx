"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { sendAIChat } from "@/lib/api/ai-chat";
import { deleteCookie, readJsonCookie, writeJsonCookie } from "@/lib/client/cookies";
import type { AIChatMessage, AIConversationItem, AIChatResponse } from "@/lib/ai-chat/types";
import styles from "./ai-consult.module.css";

const AI_CHAT_COOKIE_NAME = "tabletki_ai_chat_v1";
const MAX_PERSISTED_MESSAGES = 10;

export function AIConsultExperience() {
  const [conversation, setConversation] = useState<AIConversationItem[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const persistedConversation = readJsonCookie<AIConversationItem[]>(AI_CHAT_COOKIE_NAME);
    if (!persistedConversation) {
      return;
    }

    const validConversation = persistedConversation.filter(
      (item) =>
        item &&
        (item.role === "user" || item.role === "assistant") &&
        typeof item.content === "string"
    );

    if (validConversation.length > 0) {
      setConversation(validConversation.slice(-MAX_PERSISTED_MESSAGES));
    }
  }, []);

  useEffect(() => {
    if (conversation.length === 0) {
      deleteCookie(AI_CHAT_COOKIE_NAME);
      return;
    }

    writeJsonCookie(AI_CHAT_COOKIE_NAME, conversation.slice(-MAX_PERSISTED_MESSAGES));
  }, [conversation]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) {
      return;
    }

    const nextMessagesBase: AIChatMessage[] = [
      ...conversationToMessages(conversation),
      { role: "user", content: trimmed }
    ];
    const nextMessages: AIChatMessage[] = nextMessagesBase.slice(-MAX_PERSISTED_MESSAGES);
    const nextUserItem: AIConversationItem = { role: "user", content: trimmed };

    setConversation((current) => [...current, nextUserItem].slice(-MAX_PERSISTED_MESSAGES));
    setInput("");
    setIsLoading(true);

    try {
      const response = await sendAIChat(nextMessages);
      const nextAssistantItem: AIConversationItem = {
        role: "assistant",
        content: response.message,
        meta: {
          scopeStatus: response.scopeStatus,
          warnings: response.warnings,
          recommendedOTCDrugs: response.recommendedOTCDrugs,
          handoffCTA: response.handoffCTA
        }
      };
      setConversation((current) =>
        [
          ...current,
          nextAssistantItem
        ].slice(-MAX_PERSISTED_MESSAGES)
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className={styles.shell} data-testid="ai-chat-shell" data-chat-layout="wide">
      <p className={styles.disclaimer}>
        ИИ отвечает только по симптомам и безрецептурным препаратам. При тревожных симптомах он
        рекомендует обратиться к врачу.
      </p>

      <div className={styles.contentGrid}>
        <div className={styles.historyFrame}>
          <div className={styles.historyHeader}>
            <span className={styles.sectionEyebrow}>Диалог</span>
            <h2 className={styles.sectionTitle}>История консультации</h2>
          </div>

          <div className={styles.history} aria-live="polite" role="region" aria-label="История диалога">
            {conversation.length === 0 ? (
              <p className={styles.emptyState}>
                Опишите симптом простыми словами, например: «болит горло» или «болит голова».
              </p>
            ) : null}

            {conversation.map((item, index) =>
              item.role === "user" ? (
                <article key={`${item.role}-${index}`} className={styles.userMessage}>
                  <span className={styles.messageEyebrow}>Ваш запрос</span>
                  <div className={styles.userBubble}>
                    <p>{item.content}</p>
                  </div>
                </article>
              ) : (
                <article key={`${item.role}-${index}`} className={styles.assistantMessage}>
                  <span className={styles.messageEyebrow}>Ответ консультанта</span>
                  <div className={styles.assistantCard}>
                    <div className={styles.assistantBody}>
                      <p>{item.content}</p>
                    </div>

                    {item.meta.recommendedOTCDrugs.length > 0 || item.meta.handoffCTA ? (
                      <aside className={styles.assistantSidebar}>
                        <span className={styles.sidebarEyebrow}>
                          Подобранные безрецептурные варианты
                        </span>

                        {item.meta.recommendedOTCDrugs.length > 0 ? (
                          <div className={styles.recommendations}>
                            {item.meta.recommendedOTCDrugs.map((drug) => (
                              <div key={drug.title} className={styles.recommendationCard}>
                                <strong>{drug.title}</strong>
                                <p>{drug.rationale}</p>
                                <Link
                                  href={`/search?query=${encodeURIComponent(drug.title)}`}
                                  className={styles.recommendationLink}
                                >
                                  Выбрать {drug.title}
                                </Link>
                              </div>
                            ))}
                          </div>
                        ) : null}

                        {item.meta.handoffCTA ? (
                          <Link
                            href={`/search?query=${encodeURIComponent(item.meta.handoffCTA.query)}`}
                            className={styles.searchLink}
                          >
                            {item.meta.handoffCTA.label}
                          </Link>
                        ) : null}
                      </aside>
                    ) : null}
                  </div>
                </article>
              )
            )}
          </div>
        </div>

        <aside className={styles.composerFrame}>
          <div className={styles.composerHeader}>
            <span className={styles.sectionEyebrow}>Новый вопрос</span>
            <h2 className={styles.sectionTitle}>Сообщение консультанту</h2>
          </div>

          <form className={styles.form} onSubmit={handleSubmit}>
            <label className={styles.label} htmlFor="ai-consult-input">
              Сообщение консультанту
            </label>
            <textarea
              id="ai-consult-input"
              aria-label="Сообщение консультанту"
              className={styles.input}
              rows={6}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Опишите симптом и уточните, что нужна помощь с безрецептурным препаратом."
            />
            <button className={styles.submit} type="submit" disabled={isLoading}>
              {isLoading ? "Отправляем…" : "Отправить"}
            </button>
          </form>
        </aside>
      </div>
    </section>
  );
}

function conversationToMessages(conversation: AIConversationItem[]): AIChatMessage[] {
  return conversation.map((item) => ({
    role: item.role,
    content: item.content,
  }));
}
