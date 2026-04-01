import styles from "../auth.module.css";

export default function PrivacyPage() {
  return (
    <main className={styles.page}>
      <section className={styles.card}>
        <h1 className={styles.title}>Политика конфиденциальности</h1>
        <p className={styles.subtitle}>
          Черновик страницы. Здесь будут описаны категории собираемых данных, анонимный debug,
          cookie-политика, сроки хранения и способы связи по вопросам персональных данных.
        </p>
      </section>
    </main>
  );
}
