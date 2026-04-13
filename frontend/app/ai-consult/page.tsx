import styles from "../page.module.css";
import { AIConsultExperience } from "@/components/ai/AIConsultExperience";

export default function AIConsultPage() {
  return (
    <main className={styles.page}>
      <div className={styles.glow} />

      <section className={styles.hero}>
        <h1 className={styles.title}>ИИ-консультант по безрецептурным препаратам.</h1>
        <p className={styles.subtitle}>
          ИИ отвечает только по симптомам и безрецептурным препаратам. При тревожных симптомах он рекомендует обратиться к врачу.
        </p>
      </section>

      <AIConsultExperience />
    </main>
  );
}
