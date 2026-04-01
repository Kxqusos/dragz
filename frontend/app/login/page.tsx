"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";
import { buildGuestMergePayload, clearGuestState } from "@/lib/auth/guest-state";
import { loginUser, mergeGuestState } from "@/lib/auth/client";
import styles from "../auth.module.css";

export default function LoginPage() {
  return (
    <Suspense fallback={<main className={styles.page}><section className={styles.card}><p className={styles.subtitle}>Загрузка формы входа…</p></section></main>}>
      <LoginPageContent />
    </Suspense>
  );
}

function LoginPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState(searchParams.get("email") ?? "");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      await loginUser(email, password);
      const payload = buildGuestMergePayload();
      await mergeGuestState(payload);
      clearGuestState();
      router.push("/account");
      router.refresh();
    } catch {
      setError("Не удалось выполнить вход.");
    }
  }

  return (
    <main className={styles.page}>
      <section className={styles.card}>
        <h1 className={styles.title}>Вход</h1>
        <p className={styles.subtitle}>Войдите, чтобы сохранить корзину, историю поиска и историю чата.</p>
        <form className={styles.form} onSubmit={handleSubmit}>
          <label className={styles.label}>
            Email
            <input className={styles.input} type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label className={styles.label}>
            Пароль
            <input className={styles.input} type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>
          {error ? <p className={styles.error}>{error}</p> : null}
          <button className={styles.button} type="submit">Войти</button>
        </form>
        <p className={styles.meta}>
          Забыли пароль? <Link href="/forgot-password">Сбросить</Link>. Нет аккаунта? <Link href="/register">Зарегистрироваться</Link>.
        </p>
      </section>
    </main>
  );
}
