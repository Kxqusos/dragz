import Link from "next/link";
import styles from "./landing.module.css";

export default function HomePage() {
  return (
    <main className={styles.page}>
      <div className={styles.glow} />

      <section className={styles.hero}>
        <p className={styles.eyebrow}>Безрецептурная помощь</p>
        <h1 className={styles.title}>Быстро найти безрецептурный препарат и ближайшую аптеку.</h1>
        <p className={styles.subtitle}>
          Один продукт для двух сценариев: поиск аптек с маршрутом и AI-консультант, который
          помогает по симптомам и подсказывает безрецептурные препараты.
        </p>
        <div className={styles.ctaRow}>
          <Link href="/search" className={styles.primaryLink}>
            Начать поиск аптек
          </Link>
          <Link href="/ai-consult" className={styles.secondaryLink}>
            Получить совет от ИИ
          </Link>
        </div>
      </section>
    </main>
  );
}
