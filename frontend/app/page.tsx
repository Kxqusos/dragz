import styles from "./page.module.css";
import { SearchExperience } from "@/components/mvp/SearchExperience";
import { demoOffers, demoSuggestions } from "@/lib/mvp/demo";

export default function HomePage() {
  return (
    <main className={styles.page}>
      <div className={styles.glow} />

      <section className={styles.hero}>
        <p className={styles.eyebrow}>MVP для показа сценария</p>
        <h1 className={styles.title}>Поиск препарата по симптому, подбор аптек и быстрый маршрут.</h1>
        <p className={styles.subtitle}>
          Пользователь разрешает геолокацию, вводит запрос вроде
          {" "}
          <strong>“Препарат от головной боли”</strong>
          , получает предложения через LLM,
          добавляет нужные позиции в список и строит самый быстрый маршрут по аптекам.
        </p>
      </section>

      <SearchExperience
        suggestions={demoSuggestions}
        offers={demoOffers}
      />
    </main>
  );
}
