import { render, screen } from "@testing-library/react";
import HomePage from "@/app/page";

describe("HomePage", () => {
  it("renders the MVP shell heading and geolocation entry point", () => {
    render(<HomePage />);

    expect(
      screen.getByRole("heading", {
        name: /поиск препарата по симптому, подбор аптек и быстрый маршрут/i
      })
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", {
        name: /разрешить геолокацию/i
      })
    ).toBeInTheDocument();
  });

  it("renders the MVP search entry field", () => {
    render(<HomePage />);

    expect(
      screen.getByRole("searchbox", { name: /поиск препарата/i })
    ).toBeInTheDocument();
  });
});
