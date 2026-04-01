"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";
import { resendVerificationCode, verifyEmailCode } from "@/lib/auth/client";
import styles from "../auth.module.css";

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<main className={styles.page}><section className={styles.card}><p className={styles.subtitle}>Загрузка формы подтверждения…</p></section></main>}>
      <VerifyEmailPageContent />
    </Suspense>
  );
}

function VerifyEmailPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState(searchParams.get("email") ?? "");
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      await verifyEmailCode(email, code);
      router.push(`/login?email=${encodeURIComponent(email)}`);
    } catch {
      setError("Код подтверждения недействителен.");
    }
  }

  return (
    <main className={styles.page}>
      <section className={styles.card}>
        <h1 className={styles.title}>Подтверждение email</h1>
        <p className={styles.subtitle}>Введите код из письма. При необходимости можно отправить новый код.</p>
        <form className={styles.form} onSubmit={handleSubmit}>
          <label className={styles.label}>
            Email
            <input className={styles.input} type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <div className={styles.codeRow}>
            <label className={styles.label}>
              Код
              <input className={styles.input} inputMode="numeric" value={code} onChange={(event) => setCode(event.target.value)} required />
            </label>
            <button
              className={styles.secondaryButton}
              type="button"
              onClick={async () => {
                try {
                  await resendVerificationCode(email);
                  setMessage("Новый код отправлен.");
                  setError("");
                } catch {
                  setError("Не удалось отправить код повторно.");
                }
              }}
            >
              Отправить заново
            </button>
          </div>
          {message ? <p className={styles.success}>{message}</p> : null}
          {error ? <p className={styles.error}>{error}</p> : null}
          <button className={styles.button} type="submit">Подтвердить</button>
        </form>
      </section>
    </main>
  );
}
