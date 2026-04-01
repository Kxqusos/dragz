import styles from "../auth.module.css";

export default function TermsPage() {
  return (
    <main className={styles.page}>
      <section className={styles.card}>
        <h1 className={styles.title}>Пользовательское соглашение</h1>
        <p className={styles.subtitle}>
          Черновик страницы. Здесь будут описаны правила использования сервиса, ограничения AI-консультации,
          порядок регистрации и ответственность сторон.
        </p>
      </section>
    </main>
  );
}
