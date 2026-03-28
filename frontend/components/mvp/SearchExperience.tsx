"use client";

import { startTransition, useEffect, useMemo, useRef, useState } from "react";
import type { CartItem, PharmacyOffer, RoutePreview } from "@/lib/mvp/types";
import { getUniquePharmacyCount, hasRouteableSelection } from "@/lib/mvp/types";
import { buildRoute, searchBackend } from "@/lib/api/backend";
import { logUiEvent } from "@/lib/client/logger";
import { deleteCookie, readJsonCookie, writeJsonCookie } from "@/lib/client/cookies";
import { buildRoutePharmaciesFromCart } from "@/lib/mvp/cart";
import { CartPanel } from "@/components/mvp/CartPanel";
import { PharmacyResults } from "@/components/mvp/PharmacyResults";
import { RouteMap } from "@/components/mvp/RouteMap";
import { RouteSummary } from "@/components/mvp/RouteSummary";
import styles from "./search-experience.module.css";

type OfferSort = "distance" | "price";
const OFFER_SORT_STORAGE_KEY = "tabletki.offerSort";
const CART_COOKIE_NAME = "tabletki_cart_v1";

export function SearchExperience({
  initialQuery = ""
}: {
  initialQuery?: string;
}) {
  const [query, setQuery] = useState(initialQuery);
  const [locationEnabled, setLocationEnabled] = useState(false);
  const [visibleOffers, setVisibleOffers] = useState<PharmacyOffer[]>([]);
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [route, setRoute] = useState<RoutePreview | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [location, setLocation] = useState<{ lat: number; lon: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [offerSort, setOfferSort] = useState<OfferSort>("distance");
  const searchCacheRef = useRef(new Map<string, Promise<Awaited<ReturnType<typeof searchBackend>>>>());
  const initialQueryHandledRef = useRef(false);

  const locationStatus = locationEnabled
    ? "Геолокация получена, можно сортировать аптеки и строить маршрут."
    : "Определяем геолокацию через браузер для сортировки аптек и карты.";

  const selectedIds = useMemo(
    () => new Set(cartItems.map((item) => item.pharmacyId)),
    [cartItems]
  );

  const routePharmacies = useMemo(() => buildRoutePharmaciesFromCart(cartItems), [cartItems]);
  const uniquePharmacyCount = useMemo(() => getUniquePharmacyCount(cartItems), [cartItems]);

  const sortedOffers = useMemo(() => {
    const next = [...visibleOffers];

    next.sort((left, right) => {
      if (offerSort === "price") {
        return left.price - right.price;
      }

      const leftDistance = calculateDistanceKm(location, left);
      const rightDistance = calculateDistanceKm(location, right);
      return leftDistance - rightDistance;
    });

    return next;
  }, [location, offerSort, visibleOffers]);

  const handleSearch = async (rawQuery = query) => {
    const normalizedQuery = rawQuery.trim().toLowerCase();

    if (!normalizedQuery) {
      setQuery(rawQuery);
      setVisibleOffers([]);
      setRoute(null);
      setError(null);
      return;
    }

    setQuery(rawQuery);
    setIsLoading(true);
    setError(null);
    logUiEvent("search_submit", { query: rawQuery, offerSort, hasLocation: Boolean(location) });

    try {
      const data = await getCachedSearchResult(rawQuery);

      startTransition(() => {
        setVisibleOffers(data.offers ?? []);
        setRoute(null);
        setError(null);
      });
      logUiEvent("search_success", {
        query: rawQuery,
        offers: data.offers.length,
        warnings: data.warnings
      });
    } catch {
      logUiEvent("search_failure", { query: rawQuery });
      setVisibleOffers([]);
      setRoute(null);
      setError("Не удалось получить данные от backend.");
    } finally {
      setIsLoading(false);
    }
  };

  const toggleCartItem = (offer: PharmacyOffer) => {
    logUiEvent("cart_toggle", {
      pharmacyId: offer.pharmacyId,
      pharmacyName: offer.pharmacyName,
      matchedDrug: offer.matchedDrug,
      wasSelected: cartItems.some((item) => item.pharmacyId === offer.pharmacyId)
    });
    setCartItems((current) => {
      if (current.some((item) => item.pharmacyId === offer.pharmacyId)) {
        return current.filter((item) => item.pharmacyId !== offer.pharmacyId);
      }

      return [...current, offer];
    });
    setRoute(null);
  };

  const removeCartItem = (itemToRemove: CartItem) => {
    logUiEvent("cart_remove", {
      pharmacyId: itemToRemove.pharmacyId,
      matchedDrug: itemToRemove.matchedDrug,
    });
    setCartItems((current) => current.filter((item) => item.pharmacyId !== itemToRemove.pharmacyId));
    setRoute(null);
  };

  const clearCart = () => {
    logUiEvent("cart_clear", { itemCount: cartItems.length });
    setCartItems([]);
    setRoute(null);
  };

  const requestBrowserGeolocation = () => {
    if (!navigator.geolocation) {
      logUiEvent("geolocation_unsupported");
      setError("Браузер не поддерживает геолокацию.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        logUiEvent("geolocation_success", {
          lat: position.coords.latitude,
          lon: position.coords.longitude
        });
        setLocationEnabled(true);
        setLocation({
          lat: position.coords.latitude,
          lon: position.coords.longitude
        });
        setError(null);
      },
      () => {
        logUiEvent("geolocation_failure");
        setError("Не удалось получить геолокацию.");
      }
    );
  };

  useEffect(() => {
    requestBrowserGeolocation();
    // Intentional one-shot browser geolocation prompt on initial load.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const savedSort = window.localStorage.getItem(OFFER_SORT_STORAGE_KEY);
    if (savedSort === "distance" || savedSort === "price") {
      logUiEvent("offer_sort_restored", { offerSort: savedSort });
      setOfferSort(savedSort);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(OFFER_SORT_STORAGE_KEY, offerSort);
    logUiEvent("offer_sort_changed", { offerSort });
  }, [offerSort]);

  useEffect(() => {
    const persistedCart = readJsonCookie<CartItem[]>(CART_COOKIE_NAME);
    if (!persistedCart) {
      return;
    }

    const validCartItems = persistedCart.filter((item) => item?.pharmacyId && item?.matchedDrug);
    if (validCartItems.length > 0) {
      setCartItems(validCartItems);
    }
  }, []);

  useEffect(() => {
    if (cartItems.length === 0) {
      deleteCookie(CART_COOKIE_NAME);
      return;
    }

    writeJsonCookie(CART_COOKIE_NAME, cartItems);
  }, [cartItems]);

  useEffect(() => {
    if (!initialQuery.trim() || initialQueryHandledRef.current) {
      return;
    }

    initialQueryHandledRef.current = true;
    void handleSearch(initialQuery);
  }, [initialQuery]);

  const offerDistanceKmById = useMemo(
    () =>
      new Map(
        visibleOffers.map((offer) => [offer.pharmacyId, calculateDistanceKm(location, offer)])
      ),
    [location, visibleOffers]
  );

  const getCachedSearchResult = (searchQuery: string) => {
    const cacheKey = `${searchQuery.trim().toLowerCase()}::${location?.lat ?? "na"}::${location?.lon ?? "na"}`;
    const cached = searchCacheRef.current.get(cacheKey);

    if (cached) {
      logUiEvent("search_cache_hit", { cacheKey });
      return cached;
    }
    logUiEvent("search_cache_miss", { cacheKey });

    const request = searchBackend({
      query: searchQuery,
      cityId: "0",
      areaId: "0",
      lat: location?.lat,
      lon: location?.lon
    }).catch((fetchError) => {
      searchCacheRef.current.delete(cacheKey);
      throw fetchError;
    });

    searchCacheRef.current.set(cacheKey, request);
    return request;
  };

  return (
    <section className={styles.shell}>
      <div className={styles.topGrid}>
        <article className={styles.searchCard}>
          <div className={styles.locationInline}>
            <span className={styles.locationDot} />
            <p className={styles.locationStatus}>{locationStatus}</p>
            {!locationEnabled ? (
              <button
                className={styles.inlineButton}
                type="button"
                onClick={requestBrowserGeolocation}
              >
                Повторить запрос
              </button>
            ) : null}
          </div>
          <p className={styles.kicker}>Шаг 1</p>
          <h2 className={styles.cardTitle}>Поиск препарата</h2>
          <p className={styles.cardIntro}>
            Один прямой поток: вводите препарат, сразу получаете аптеки на карте и собираете маршрут.
          </p>
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
              placeholder="Например, Ибупрофен 200 мг"
            />
            <button
              className={styles.primaryButton}
              type="button"
              onClick={() => {
                void handleSearch();
              }}
            >
              Найти аптеки
            </button>
          </div>
          <p className={styles.hint}>
            Точный запрос сразу уходит в поиск аптек. Выберите подходящие точки и постройте маршрут.
          </p>
          {isLoading ? <p className={styles.loading}>Идет запрос к серверному пайплайну…</p> : null}
          {error ? <p className={styles.error}>{error}</p> : null}
        </article>
      </div>

      <div className={styles.contentGrid}>
        <article className={styles.panel}>
          <p className={styles.kicker}>Шаг 2</p>
          <h2 className={styles.cardTitle}>Подходящие аптеки</h2>
          {visibleOffers.length > 0 ? (
            <div className={styles.sortBar} aria-label="Сортировка аптек">
              <span className={styles.sortLabel}>Сортировать по</span>
              <button
                className={offerSort === "distance" ? styles.sortButtonActive : styles.sortButton}
                type="button"
                onClick={() => setOfferSort("distance")}
              >
                По расстоянию
              </button>
              <button
                className={offerSort === "price" ? styles.sortButtonActive : styles.sortButton}
                type="button"
                onClick={() => setOfferSort("price")}
              >
                По цене
              </button>
            </div>
          ) : null}
          <PharmacyResults
            offers={sortedOffers}
            distanceKmById={offerDistanceKmById}
            selectedIds={selectedIds}
            onToggle={toggleCartItem}
          />
          {visibleOffers.length > 0 ? (
            <RouteMap offers={sortedOffers} label="Карта аптек" />
          ) : null}
        </article>

        <article className={styles.panel}>
          <p className={styles.kicker}>Шаг 3</p>
          <h2 className={styles.cardTitle}>Корзина и маршрут</h2>
          <CartPanel
            items={cartItems}
            uniquePharmacyCount={uniquePharmacyCount}
            onRemove={removeCartItem}
            onClear={clearCart}
          />
          {hasRouteableSelection(cartItems) ? (
            <>
              <div className={styles.routeActions}>
                <button
                  className={`${styles.primaryButton} ${styles.routeActionButton}`}
                  type="button"
                  onClick={async () => {
                    if (!location) {
                      setError("Нужна геолокация для построения маршрута.");
                      return;
                    }

                    try {
                      logUiEvent("route_build_start", {
                        pharmacyCount: routePharmacies.length,
                        cartItemCount: cartItems.length
                      });
                      const data = await buildRoute({
                        origin: location,
                        pharmacies: routePharmacies
                      });
                      setRoute(data);
                      setError(null);
                      logUiEvent("route_build_success", {
                        stopCount: data.orderedStops.length,
                        distanceKm: data.totalDistanceKm,
                        durationMinutes: data.totalDurationMinutes
                      });
                    } catch {
                      logUiEvent("route_build_failure", {
                        pharmacyCount: routePharmacies.length,
                        cartItemCount: cartItems.length
                      });
                      setRoute(null);
                      setError("Не удалось построить маршрут через backend.");
                    }
                  }}
                >
                  Построить маршрут по корзине
                </button>
              </div>
              {route ? (
                <>
                  <RouteSummary route={route} />
                  <RouteMap route={route} offerDetails={routePharmacies} label="Карта маршрута" />
                </>
              ) : null}
            </>
          ) : (
            <p className={styles.cardText}>
              Добавьте в корзину хотя бы одну позицию, чтобы построить маршрут до нужной аптеки.
            </p>
          )}
        </article>
      </div>
    </section>
  );
}

function calculateDistanceKm(
  origin: { lat: number; lon: number } | null,
  offer: PharmacyOffer
): number {
  if (!origin || !hasConfirmedCoordinates(offer)) {
    return Number.POSITIVE_INFINITY;
  }

  const latDelta = toRadians(offer.lat - origin.lat);
  const lonDelta = toRadians(offer.lon - origin.lon);
  const fromLat = toRadians(origin.lat);
  const toLat = toRadians(offer.lat);
  const haversine =
    Math.sin(latDelta / 2) * Math.sin(latDelta / 2) +
    Math.cos(fromLat) * Math.cos(toLat) * Math.sin(lonDelta / 2) * Math.sin(lonDelta / 2);

  return 6371 * 2 * Math.atan2(Math.sqrt(haversine), Math.sqrt(1 - haversine));
}

function toRadians(value: number): number {
  return (value * Math.PI) / 180;
}

function hasConfirmedCoordinates(offer: PharmacyOffer): boolean {
  return Number.isFinite(offer.lat) && Number.isFinite(offer.lon) && (offer.lat !== 0 || offer.lon !== 0);
}
