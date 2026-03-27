import styles from "@/app/page.module.css";
import { SearchExperience } from "@/components/mvp/SearchExperience";

export function SearchPageView({
  initialQuery = ""
}: {
  initialQuery?: string;
}) {
  return (
    <main className={styles.page}>
      <div className={styles.glow} />

      <section className={styles.hero}>
        <p className={styles.eyebrow}>Поиск аптек</p>
        <h1 className={styles.title}>Найти препарат, увидеть аптеки, быстро собрать маршрут.</h1>
        <p className={styles.subtitle}>
          Введите название препарата и получите список аптек, карту точек и быстрый маршрут.
        </p>
      </section>

      <SearchExperience initialQuery={initialQuery} />
    </main>
  );
}
