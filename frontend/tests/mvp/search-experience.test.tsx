import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SearchExperience } from "@/components/mvp/SearchExperience";

describe("SearchExperience", () => {
  it("adds a suggested drug into the selected list", async () => {
    const user = userEvent.setup();

    render(
      <SearchExperience
        suggestions={[
          {
            id: "1",
            title: "Ибупрофен 200 мг",
            kind: "drug",
            confidence: 0.9,
            rationale: "Подходит для симптома"
          }
        ]}
        offers={[]}
      />
    );

    await user.click(
      screen.getByRole("button", { name: /добавить ибупрофен 200 мг/i })
    );

    expect(screen.getAllByText(/ибупрофен 200 мг/i).length).toBeGreaterThan(2);
  });
});
