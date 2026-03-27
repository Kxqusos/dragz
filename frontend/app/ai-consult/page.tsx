import styles from "../page.module.css";
import { AIConsultExperience } from "@/components/ai/AIConsultExperience";

export default function AIConsultPage() {
  return (
    <main className={styles.page}>
      <div className={styles.glow} />

      <section className={styles.hero}>
        <p className={styles.eyebrow}>AI OTC-консультация</p>
        <h1 className={styles.title}>ИИ-консультант по безрецептурным препаратам.</h1>
        <p className={styles.subtitle}>
          Опишите симптом, получите безопасную OTC-подсказку и при необходимости перейдите в
          поиск аптек по рекомендованному препарату.
        </p>
      </section>

      <AIConsultExperience />
    </main>
  );
}
