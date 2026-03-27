from dataclasses import dataclass
from html import unescape
import re
from urllib.parse import parse_qs, urlparse


@dataclass
class Ref003SearchInitial:
    action: str
    city_field_name: str
    area_field_name: str
    drug_field_name: str
    default_city_label: str


@dataclass
class Ref003Variant:
    drug_name: str
    drug_id: str
    href: str


@dataclass
class Ref003Offer:
    pharmacy_name: str
    address: str
    price: float
    quantity_label: str
    matched_drug: str


@dataclass
class Ref003SearchResults:
    query: str
    variants: list[Ref003Variant]
    offers: list[Ref003Offer]
    warnings: list[str]


def _extract_attr(html: str, pattern: str, default: str = "") -> str:
    match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
    return unescape(match.group(1)).strip() if match else default


def parse_search_initial(html: str) -> Ref003SearchInitial:
    return Ref003SearchInitial(
      action=_extract_attr(html, r'<form[^>]+id="searchform"[^>]+action="([^"]+)"'),
      city_field_name=_extract_attr(html, r'<select[^>]+id="city_id"[^>]+name="([^"]+)"', "city_id"),
      area_field_name=_extract_attr(html, r'<select[^>]+id="area_id"[^>]+name="([^"]+)"', "area_id"),
      drug_field_name=_extract_attr(html, r'<input[^>]+id="drugname"[^>]+name="([^"]+)"', "drugname"),
      default_city_label=_extract_attr(
          html,
          r'<select[^>]+id="city_id"[^>]*>.*?<option[^>]*selected[^>]*>(.*?)</option>',
      ),
    )


def parse_search_results(html: str) -> Ref003SearchResults:
    query = _extract_attr(html, r'<input[^>]+id="drugname"[^>]+value="([^"]*)"')
    warnings: list[str] = []
    variants: list[Ref003Variant] = []
    offers: list[Ref003Offer] = []

    if "A PHP Error was encountered" in html:
        warnings.append("php-notice")

    if "ничего не найдено" in html.lower():
        warnings.append("empty-results")

    for href, label in re.findall(r'<a href="([^"]*drugname_id=[^"]+)">([^<]+)</a>', html):
        parsed_href = unescape(href)
        query_parts = parse_qs(urlparse(parsed_href).query)
        drug_id = query_parts.get("drugname_id", [""])[0]
        variants.append(
            Ref003Variant(
                drug_name=unescape(label).strip(),
                drug_id=drug_id,
                href=parsed_href,
            )
        )

    table_match = re.search(
        r'<table[^>]+id="resultt"[^>]*>(.*?)</table>',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if table_match:
        table_html = table_match.group(1)
        tbody_match = re.search(r"<tbody>(.*?)</tbody>", table_html, re.IGNORECASE | re.DOTALL)
        rows_source = tbody_match.group(1) if tbody_match else table_html
        for row_html in re.findall(r"<tr>(.*?)</tr>", rows_source, re.IGNORECASE | re.DOTALL):
            cells = [
                re.sub(r"<[^>]+>", "", unescape(cell)).strip().strip('"')
                for cell in re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.IGNORECASE | re.DOTALL)
            ]
            if len(cells) < 5:
                continue
            try:
                price = float(cells[4].replace(",", "."))
            except ValueError:
                continue

            offers.append(
                Ref003Offer(
                    pharmacy_name=cells[2],
                    address=cells[3],
                    price=price,
                    quantity_label=cells[1],
                    matched_drug=cells[0],
                )
            )

    return Ref003SearchResults(
        query=query,
        variants=variants,
        offers=offers,
        warnings=warnings,
    )
