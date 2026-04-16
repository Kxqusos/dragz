"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { registerUser } from "@/lib/auth/client";
import styles from "../auth.module.css";

const PASSWORD_REQUIREMENTS_MESSAGE = "Пароль должен содержать минимум 8 символов, маленькие и большие буквы, а также цифры.";

function hasRequiredPasswordComplexity(password: string): boolean {
  return password.length >= 8 && /[a-z]/.test(password) && /[A-Z]/.test(password) && /\d/.test(password);
}

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [error, setError] = useState("");
  const passwordRequirementsMismatch = password.length > 0 && !hasRequiredPasswordComplexity(password);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (passwordRequirementsMismatch) {
      return;
    }
    if (password !== confirmPassword) {
      setError("Пароли не совпадают.");
      return;
    }
    try {
      await registerUser(email, password, acceptedTerms);
      router.push(`/verify-email?email=${encodeURIComponent(email)}`);
    } catch {
      setError("Не удалось отправить код подтверждения.");
    }
  }

  return (
    <main className={styles.page}>
      <section className={styles.card}>
        <h1 className={styles.title}>Регистрация</h1>
        <form className={styles.form} onSubmit={handleSubmit}>
          <label className={styles.label}>
            Email
            <input className={styles.input} type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label className={styles.label}>
            Пароль
            <input
              className={styles.input}
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          {passwordRequirementsMismatch ? <p className={styles.error}>{PASSWORD_REQUIREMENTS_MESSAGE}</p> : null}
          <label className={styles.label}>
            Повторите пароль
            <input
              className={styles.input}
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              required
            />
          </label>
          <label className={styles.checkboxLabel}>
            <input
              className={styles.checkbox}
              type="checkbox"
              checked={acceptedTerms}
              onChange={(event) => setAcceptedTerms(event.target.checked)}
              required
            />
            <span>
              Я принимаю <Link href="/terms">пользовательское соглашение</Link> и <Link href="/privacy">политику конфиденциальности</Link>.
            </span>
          </label>
          {error ? <p className={styles.error}>{error}</p> : null}
          <button className={styles.button} type="submit">Продолжить</button>
        </form>
      </section>
    </main>
  );
}
