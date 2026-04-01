"use client";

import { FormEvent, useState } from "react";
import { forgotPassword } from "@/lib/auth/client";
import styles from "../auth.module.css";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      await forgotPassword(email);
      setMessage("Если email зарегистрирован, код сброса отправлен.");
    } catch {
      setError("Не удалось запросить сброс пароля.");
    }
  }

  return (
    <main className={styles.page}>
      <section className={styles.card}>
        <h1 className={styles.title}>Сброс пароля</h1>
        <p className={styles.subtitle}>Введите email, затем перейдите на страницу установки нового пароля с кодом из письма.</p>
        <form className={styles.form} onSubmit={handleSubmit}>
          <label className={styles.label}>
            Email
            <input className={styles.input} type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          {message ? <p className={styles.success}>{message}</p> : null}
          {error ? <p className={styles.error}>{error}</p> : null}
          <button className={styles.button} type="submit">Запросить код</button>
        </form>
      </section>
    </main>
  );
}
