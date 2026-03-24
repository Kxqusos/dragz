"use client";

import { startTransition, useMemo, useState } from "react";
import type { DrugSuggestion, PharmacyOffer, RouteStop } from "@/lib/mvp/types";
import { hasRouteableSelection } from "@/lib/mvp/types";
import { demoOffers, demoSuggestions, type RoutePreview } from "@/lib/mvp/demo";
import { PharmacyResults } from "@/components/mvp/PharmacyResults";
import { RouteMap } from "@/components/mvp/RouteMap";
import { RouteSummary } from "@/components/mvp/RouteSummary";
import { SelectedDrugList } from "@/components/mvp/SelectedDrugList";
import styles from "./search-experience.module.css";

type SearchExperienceProps = {
  suggestions: DrugSuggestion[];
  offers: PharmacyOffer[];
};

function buildDemoRoute(pharmacies: PharmacyOffer[]): RoutePreview {
  return {
    totalDurationMinutes: 12 + pharmacies.length * 3,
    totalDistanceKm: Number((2.4 + pharmacies.length * 1.1).toFixed(1)),
    orderedStops: [
      {
        pharmacyId: "origin",
        label: "Ваше местоположение",
        lat: 47.222,
        lon: 39.718,
        order: 0
      },
      ...pharmacies.map((pharmacy, index) => ({
        pharmacyId: pharmacy.pharmacyId,
        label: pharmacy.pharmacyName,
        lat: pharmacy.lat,
        lon: pharmacy.lon,
        order: index + 1
      }))
    ]
  };
}

export function SearchExperience({
  suggestions,
  offers
}: SearchExperienceProps) {
  const [query, setQuery] = useState("");
  const [locationEnabled, setLocationEnabled] = useState(false);
  const [visibleSuggestions, setVisibleSuggestions] = useState(suggestions);
  const [visibleOffers, setVisibleOffers] = useState<PharmacyOffer[]>([]);
  const [selectedDrugs, setSelectedDrugs] = useState<DrugSuggestion[]>([]);
  const [selectedPharmacies, setSelectedPharmacies] = useState<PharmacyOffer[]>([]);
  const [route, setRoute] = useState<RoutePreview | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const statusLabel = locationEnabled
    ? "Геолокация сохранена, можно искать препарат."
    : "Сначала разрешите геолокацию для сортировки аптек по времени.";

  const selectedIds = useMemo(
    () => new Set(selectedPharmacies.map((item) => item.pharmacyId)),
    [selectedPharmacies]
  );

  const handleSearch = async () => {
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) {
      setVisibleSuggestions(suggestions);
      setVisibleOffers([]);
      setRoute(null);
      return;
    }

    if (normalizedQuery.includes("головной") || normalizedQuery.includes("боли")) {
      setIsLoading(true);

      try {
        const response = await fetch("/api/search", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            query,
            cityId: "0",
            areaId: "0"
          })
        });
        const data = (await response.json()) as {
          suggestions?: DrugSuggestion[];
          offers?: PharmacyOffer[];
        };

        startTransition(() => {
          setVisibleSuggestions(data.suggestions ?? suggestions);
          setVisibleOffers(data.offers ?? []);
          setRoute(null);
        });
      } catch {
        setVisibleSuggestions(suggestions);
        setVisibleOffers([]);
        setRoute(null);
      } finally {
        setIsLoading(false);
      }
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch("/api/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          query,
          cityId: "0",
          areaId: "0"
        })
      });
      const data = (await response.json()) as {
        suggestions?: DrugSuggestion[];
        offers?: PharmacyOffer[];
      };

      startTransition(() => {
        setVisibleSuggestions(data.suggestions ?? []);
        setVisibleOffers(data.offers?.length ? data.offers : offers);
        setRoute(null);
      });
    } catch {
      setVisibleSuggestions([]);
      setVisibleOffers(offers);
      setRoute(null);
    } finally {
      setIsLoading(false);
    }
  };

  const addDrug = (suggestion: DrugSuggestion) => {
    setSelectedDrugs((current) =>
      current.some((item) => item.id === suggestion.id) ? current : [...current, suggestion]
    );
    setVisibleOffers(offers.filter((offer) => offer.matchedDrug === suggestion.title));
  };

  const togglePharmacy = (offer: PharmacyOffer) => {
    setSelectedPharmacies((current) => {
      if (current.some((item) => item.pharmacyId === offer.pharmacyId)) {
        return current.filter((item) => item.pharmacyId !== offer.pharmacyId);
      }

      return [...current, offer];
    });
    setRoute(null);
  };

  return (
    <section className={styles.shell}>
      <div className={styles.topGrid}>
        <article className={styles.locationCard}>
          <p className={styles.kicker}>Шаг 1</p>
          <h2 className={styles.cardTitle}>Локация пользователя</h2>
          <p className={styles.cardText}>{statusLabel}</p>
          <button
            className={styles.primaryButton}
            type="button"
            onClick={() => setLocationEnabled(true)}
          >
            Разрешить геолокацию
          </button>
        </article>

        <article className={styles.searchCard}>
          <p className={styles.kicker}>Шаг 2</p>
          <h2 className={styles.cardTitle}>Поиск препарата</h2>
          <div className={styles.searchRow}>
            <label className={styles.searchLabel} htmlFor="drug-query">
              Поиск препарата
            </label>
            <input
              id="drug-query"
              aria-label="Поиск препарата"
              className={styles.searchInput}
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Препарат от головной боли"
            />
            <button className={styles.primaryButton} type="button" onClick={handleSearch}>
              Показать предложения
            </button>
          </div>
          <p className={styles.hint}>
            Можно искать по симптому или точному названию. Симптомный запрос уходит в LLM,
            точное название идет в поиск аптек напрямую.
          </p>
          {isLoading ? <p className={styles.loading}>Идет запрос к серверному пайплайну…</p> : null}
        </article>
      </div>

      <div className={styles.contentGrid}>
        <article className={styles.panel}>
          <p className={styles.kicker}>Шаг 3</p>
          <h2 className={styles.cardTitle}>Предложения от LLM</h2>
          <div className={styles.suggestionList}>
            {visibleSuggestions.map((suggestion) => (
              <div key={suggestion.id} className={styles.suggestionCard}>
                <div>
                  <strong>{suggestion.title}</strong>
                  <p>{suggestion.rationale}</p>
                </div>
                <button
                  className={styles.secondaryButton}
                  type="button"
                  onClick={() => addDrug(suggestion)}
                  aria-label={`Добавить ${suggestion.title}`}
                >
                  Добавить {suggestion.title}
                </button>
              </div>
            ))}
          </div>
        </article>

        <article className={styles.panel}>
          <p className={styles.kicker}>Шаг 4</p>
          <h2 className={styles.cardTitle}>Список выбранных препаратов</h2>
          <SelectedDrugList selectedDrugs={selectedDrugs} />
        </article>
      </div>

      <div className={styles.contentGrid}>
        <article className={styles.panel}>
          <p className={styles.kicker}>Шаг 5</p>
          <h2 className={styles.cardTitle}>Подходящие аптеки</h2>
          <PharmacyResults
            offers={visibleOffers}
            selectedIds={selectedIds}
            onToggle={togglePharmacy}
          />
        </article>

        <article className={styles.panel}>
          <p className={styles.kicker}>Шаг 6</p>
          <h2 className={styles.cardTitle}>Самый быстрый маршрут</h2>
          {hasRouteableSelection(selectedPharmacies) ? (
            <>
              <button
                className={styles.primaryButton}
                type="button"
                onClick={async () => {
                  try {
                    const response = await fetch("/api/route", {
                      method: "POST",
                      headers: {
                        "Content-Type": "application/json"
                      },
                      body: JSON.stringify({
                        origin: {
                          lat: 47.222,
                          lon: 39.718
                        },
                        pharmacies: selectedPharmacies
                      })
                    });
                    const data = (await response.json()) as RoutePreview;
                    setRoute(data);
                  } catch {
                    setRoute(buildDemoRoute(selectedPharmacies));
                  }
                }}
              >
                Построить самый быстрый маршрут
              </button>
              {route ? (
                <>
                  <RouteSummary route={route} />
                  <RouteMap route={route} />
                </>
              ) : null}
            </>
          ) : (
            <p className={styles.cardText}>
              Добавьте минимум две аптеки, чтобы построить маршрут по всем точкам.
            </p>
          )}
        </article>
      </div>
    </section>
  );
}
