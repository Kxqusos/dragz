"use client";

import { FormEvent, useEffect, useState } from "react";
import { getCurrentUser, loadAdminSettings, loadAdminUsers, loadDebugEvents, updateAdminSettings } from "@/lib/auth/client";
import type { AuthUser, DebugEvent, SiteSettingItem } from "@/lib/auth/types";
import styles from "../auth.module.css";

export default function AdminPage() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [settings, setSettings] = useState<SiteSettingItem[]>([]);
  const [debugEvents, setDebugEvents] = useState<DebugEvent[]>([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    void getCurrentUser().then((currentUser) => {
      setUser(currentUser);
      if (!currentUser || currentUser.role !== "admin") {
        return;
      }
      void loadAdminUsers().then(setUsers);
      void loadAdminSettings().then(setSettings);
      void loadDebugEvents().then(setDebugEvents);
    });
  }, []);

  if (!user || user.role !== "admin") {
    return (
      <main className={styles.page}>
        <section className={styles.card}>
          <h1 className={styles.title}>Админка</h1>
          <p className={styles.subtitle}>Доступ только для администраторов.</p>
        </section>
      </main>
    );
  }

  return (
    <main className={styles.page}>
      <div className={styles.grid}>
        <section className={styles.panel}>
          <h1 className={styles.title}>Пользователи</h1>
          <div className={styles.list}>
            {users.map((item) => (
              <article key={item.id} className={styles.listItem}>
                <strong>{item.email}</strong>
                <p className={styles.meta}>Роль: {item.role}. Подтверждён: {item.isEmailVerified ? "да" : "нет"}.</p>
              </article>
            ))}
          </div>
        </section>

        <section className={styles.panel}>
          <h2 className={styles.title}>Настройки сайта</h2>
          <form
            className={styles.form}
            onSubmit={async (event: FormEvent<HTMLFormElement>) => {
              event.preventDefault();
              const nextSettings = await updateAdminSettings(settings);
              setSettings(nextSettings);
              setMessage("Настройки сохранены.");
            }}
          >
            {settings.map((item, index) => (
              <label key={item.key} className={styles.label}>
                {item.key}
                <input
                  className={styles.input}
                  value={String(item.value ?? "")}
                  onChange={(event) => {
                    setSettings((current) =>
                      current.map((setting, currentIndex) =>
                        currentIndex === index ? { ...setting, value: event.target.value } : setting
                      )
                    );
                  }}
                />
              </label>
            ))}
            {message ? <p className={styles.success}>{message}</p> : null}
            <button className={styles.button} type="submit">Сохранить настройки</button>
          </form>
        </section>

        <section className={styles.panel}>
          <h2 className={styles.title}>Анонимный debug</h2>
          <div className={styles.list}>
            {debugEvents.map((event) => (
              <article key={event.id} className={styles.listItem}>
                <strong>{event.event}</strong>
                <p className={styles.meta}>{event.route ?? "route:n/a"} • {event.createdAt}</p>
                <p className={styles.meta}>IP hash: {event.ipHash ?? "n/a"}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
