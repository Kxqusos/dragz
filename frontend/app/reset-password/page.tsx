"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";
import { resetPassword } from "@/lib/auth/client";
import styles from "../auth.module.css";

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<main className={styles.page}><section className={styles.card}><p className={styles.subtitle}>Загрузка формы смены пароля…</p></section></main>}>
      <ResetPasswordPageContent />
    </Suspense>
  );
}

function ResetPasswordPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState(searchParams.get("email") ?? "");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      await resetPassword(email, code, password);
      router.push(`/login?email=${encodeURIComponent(email)}`);
    } catch {
      setError("Не удалось обновить пароль.");
    }
  }

  return (
    <main className={styles.page}>
      <section className={styles.card}>
        <h1 className={styles.title}>Новый пароль</h1>
        <p className={styles.subtitle}>Введите email, код из письма и новый пароль.</p>
        <form className={styles.form} onSubmit={handleSubmit}>
          <label className={styles.label}>
            Email
            <input className={styles.input} type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label className={styles.label}>
            Код
            <input className={styles.input} inputMode="numeric" value={code} onChange={(event) => setCode(event.target.value)} required />
          </label>
          <label className={styles.label}>
            Новый пароль
            <input className={styles.input} type="password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>
          {error ? <p className={styles.error}>{error}</p> : null}
          <button className={styles.button} type="submit">Сохранить пароль</button>
        </form>
      </section>
    </main>
  );
}
