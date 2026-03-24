import { load } from "cheerio";

type Ref003Option = {
  value: string;
  label: string;
};

type Ref003SearchMetadata = {
  action: string;
  cityFieldName: string;
  areaFieldName: string;
  drugFieldName: string;
  defaultCity: Ref003Option;
  defaultArea: Ref003Option;
  defaultDrugType: "torg" | "mnn";
};

type Ref003Results = {
  query: string;
  offers: [];
  warnings: string[];
};

function getSelectedOption(
  root: ReturnType<typeof load>,
  selector: string
): Ref003Option {
  const selected = root(`${selector} option[selected]`).first();

  if (selected.length > 0) {
    return {
      value: selected.attr("value") ?? "",
      label: selected.text().trim()
    };
  }

  const first = root(`${selector} option`).first();

  return {
    value: first.attr("value") ?? "",
    label: first.text().trim()
  };
}

export function parseRef003SearchPage(html: string): Ref003SearchMetadata {
  const root = load(html);
  const searchForm = root("#searchform");

  return {
    action: searchForm.attr("action") ?? "",
    cityFieldName: root("#city_id").attr("name") ?? "city_id",
    areaFieldName: root("#area_id").attr("name") ?? "area_id",
    drugFieldName: root("#drugname").attr("name") ?? "drugname",
    defaultCity: getSelectedOption(root, "#city_id"),
    defaultArea: getSelectedOption(root, "#area_id"),
    defaultDrugType: root("#type_drug_mnn").is(":checked") ? "mnn" : "torg"
  };
}

export function parseRef003ResultsPage(html: string): Ref003Results {
  const root = load(html);
  const warnings: string[] = [];

  if (root("body").text().includes("A PHP Error was encountered")) {
    warnings.push("php-notice");
  }

  return {
    query: root("#drugname").attr("value")?.trim() ?? "",
    offers: [],
    warnings
  };
}
