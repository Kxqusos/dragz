import { render, screen } from "@testing-library/react";
import { RouteSummary } from "@/components/mvp/RouteSummary";

describe("RouteSummary", () => {
  it("renders total route time when two or more pharmacies are selected", () => {
    render(
      <RouteSummary
        route={{
          totalDurationMinutes: 18,
          totalDistanceKm: 5.4,
          orderedStops: [
            {
              pharmacyId: "origin",
              label: "Ваше местоположение",
              lat: 0,
              lon: 0,
              order: 0
            },
            {
              pharmacyId: "1",
              label: "Аптека 1",
              lat: 0,
              lon: 0,
              order: 1
            },
            {
              pharmacyId: "2",
              label: "Аптека 2",
              lat: 0,
              lon: 0,
              order: 2
            }
          ]
        }}
      />
    );

    expect(screen.getByText(/18 мин/i)).toBeInTheDocument();
  });
});
