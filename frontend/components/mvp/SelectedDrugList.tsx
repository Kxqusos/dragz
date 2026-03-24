import type { DrugSuggestion } from "@/lib/mvp/types";
import styles from "./search-experience.module.css";

type SelectedDrugListProps = {
  selectedDrugs: DrugSuggestion[];
};

export function SelectedDrugList({
  selectedDrugs
}: SelectedDrugListProps) {
  if (selectedDrugs.length === 0) {
    return (
      <p className={styles.emptyState}>
        Пока пусто. Добавьте препарат из предложений, чтобы продолжить сравнение.
      </p>
    );
  }

  return (
    <ul className={styles.selectedList}>
      {selectedDrugs.map((drug) => (
        <li key={drug.id} className={styles.selectedItem}>
          <strong>{drug.title}</strong>
          <span>{Math.round(drug.confidence * 100)}% уверенность модели</span>
        </li>
      ))}
    </ul>
  );
}
