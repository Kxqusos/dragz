import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import HomePage from "@/app/page";

describe("mvp home flow", () => {
  it("shows geolocation CTA before search results flow", () => {
    render(<HomePage />);

    expect(
      screen.getByRole("button", { name: /разрешить геолокацию/i })
    ).toBeInTheDocument();
  });

  it("lets the user search by symptom phrase", async () => {
    const user = userEvent.setup();
    render(<HomePage />);

    const input = screen.getByRole("searchbox", { name: /поиск препарата/i });
    await user.type(input, "Препарат от головной боли");

    expect(input).toHaveValue("Препарат от головной боли");
  });
});
