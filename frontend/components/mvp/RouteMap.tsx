"use client";

import { useEffect, useMemo, useRef } from "react";
import type { PharmacyOffer, RoutePreview } from "@/lib/mvp/types";
import styles from "./search-experience.module.css";
import { getRouteMapMarkerLabel } from "./route-stop-presentation";

type HoverCard = {
  title: string;
  address?: string;
  matchedDrug?: string;
  quantityLabel?: string;
  availabilityLabel?: string;
  priceLabel?: string;
};

type MapPoint = {
  key: string;
  label: string;
  lat: number;
  lon: number;
  hoverCard: HoverCard;
};

type RouteMapProps = {
  route?: RoutePreview;
  offers?: PharmacyOffer[];
  offerDetails?: PharmacyOffer[];
  label?: string;
};

export function RouteMap({
  route,
  offers = [],
  offerDetails = offers,
  label = "Карта маршрута"
}: RouteMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const isRouteMap = Boolean(route);

  const points = useMemo(() => {
    const offersById = new Map(offerDetails.map((offer) => [offer.pharmacyId, offer]));

    if (route) {
      return route.orderedStops.map((stop) => ({
        key: `${stop.pharmacyId}-${stop.order}`,
        label: getRouteMapMarkerLabel(stop),
        lat: stop.lat,
        lon: stop.lon,
        hoverCard:
          stop.pharmacyId === "origin"
            ? { title: stop.label }
            : toHoverCard(offersById.get(stop.pharmacyId), stop.label)
      }));
    }

    return offers.map((offer) => ({
      key: offer.pharmacyId,
      label: `${offer.price}₽`,
      lat: offer.lat,
      lon: offer.lon,
      hoverCard: toHoverCard(offer, offer.pharmacyName)
    }));
  }, [offerDetails, offers, route]);

  const validPoints = useMemo(
    () =>
      points.filter(
        (point) => Number.isFinite(point.lat) && Number.isFinite(point.lon) && (point.lat !== 0 || point.lon !== 0)
      ),
    [points]
  );

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    let disposed = false;
    let mapInstance: { remove: () => void } | null = null;

    void (async () => {
      const maplibregl = await import("maplibre-gl");
      if (disposed || !containerRef.current) {
        return;
      }

      const map = new maplibregl.Map({
        container: containerRef.current,
        style: {
          version: 8,
          sources: {
            osm: {
              type: "raster",
              tiles: [
                "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
                "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
                "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png"
              ],
              tileSize: 256,
              attribution: "&copy; OpenStreetMap contributors"
            }
          },
          layers: [
            {
              id: "osm",
              type: "raster",
              source: "osm"
            }
          ]
        },
        center: validPoints.length ? [validPoints[0].lon, validPoints[0].lat] : [39.7015, 47.2357],
        zoom: validPoints.length ? 12 : 10
      });

      mapInstance = map;

      map.on("load", () => {
        if (!validPoints.length) {
          return;
        }

        const popup = new maplibregl.Popup({
          closeButton: false,
          closeOnClick: false,
          className: "tabletki-map-popup",
          maxWidth: "320px",
          offset: 18
        });

        validPoints.forEach((point) => {
          const marker = document.createElement("button");
          marker.className = styles.mapMarkerReal;
          marker.textContent = point.label;
          marker.type = "button";
          marker.setAttribute("aria-label", point.hoverCard.title);
          marker.addEventListener("mouseenter", () => {
            popup.setLngLat([point.lon, point.lat]).setDOMContent(buildPopupContent(point.hoverCard)).addTo(map);
          });
          marker.addEventListener("mouseleave", () => popup.remove());
          marker.addEventListener("focus", () => {
            popup.setLngLat([point.lon, point.lat]).setDOMContent(buildPopupContent(point.hoverCard)).addTo(map);
          });
          marker.addEventListener("blur", () => popup.remove());
          new maplibregl.Marker({ element: marker }).setLngLat([point.lon, point.lat]).addTo(map);
        });

        if (route && validPoints.length > 1) {
          const geometry =
            route.routeGeometry && route.routeGeometry.length > 1
              ? route.routeGeometry
              : validPoints.map((point) => [point.lon, point.lat] as [number, number]);

          map.addSource("route-line", {
            type: "geojson",
            data: {
              type: "Feature",
              geometry: {
                type: "LineString",
                coordinates: geometry
              },
              properties: {}
            }
          });
          map.addLayer({
            id: "route-line",
            type: "line",
            source: "route-line",
            paint: {
              "line-color": "#0f766e",
              "line-width": 5,
              "line-opacity": 0.92
            }
          });
        }

        const bounds = new maplibregl.LngLatBounds();
        validPoints.forEach((point) => bounds.extend([point.lon, point.lat]));
        map.fitBounds(bounds, { padding: 60, maxZoom: 15 });
      });
    })();

    return () => {
      disposed = true;
      mapInstance?.remove();
    };
  }, [label, route, validPoints]);

  return (
    <div className={styles.mapWrap}>
      {!validPoints.length ? (
        <p className={styles.mapFallbackNote}>
          Координаты точек пока недоступны, поэтому карта центрирована на Ростове-на-Дону.
        </p>
      ) : null}
      <div
        ref={containerRef}
        className={styles.mapCard}
        aria-label={label}
        data-map-kind={isRouteMap ? "route" : "offers"}
        data-map-size="expanded"
      />
    </div>
  );
}

function toHoverCard(offer: PharmacyOffer | undefined, fallbackTitle: string): HoverCard {
  if (!offer) {
    return { title: fallbackTitle };
  }

  return {
    title: offer.pharmacyName,
    address: offer.address,
    matchedDrug: offer.matchedDrug,
    quantityLabel: offer.quantityLabel,
    availabilityLabel: offer.inStock ? "В наличии" : "Нет в наличии",
    priceLabel: `${offer.price} ₽`
  };
}

function buildPopupContent(hoverCard: HoverCard): HTMLElement {
  const container = document.createElement("div");
  container.className = styles.mapPopupCard;
  container.dataset.mapPopupCard = "true";

  const title = document.createElement("strong");
  title.textContent = hoverCard.title;
  container.appendChild(title);

  if (hoverCard.address) {
    const address = document.createElement("p");
    address.textContent = hoverCard.address;
    container.appendChild(address);
  }

  if (hoverCard.matchedDrug) {
    const matchedDrug = document.createElement("p");
    matchedDrug.textContent = hoverCard.matchedDrug;
    container.appendChild(matchedDrug);
  }

  const metaParts = [hoverCard.quantityLabel, hoverCard.availabilityLabel, hoverCard.priceLabel].filter(Boolean);
  if (metaParts.length) {
    const meta = document.createElement("p");
    meta.className = styles.mapPopupMeta;
    meta.textContent = metaParts.join(" • ");
    container.appendChild(meta);
  }

  return container;
}
