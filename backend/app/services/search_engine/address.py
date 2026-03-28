import re


_STREET_TYPE_ALIASES = {
    "ул": "улица",
    "ул.": "улица",
    "улица": "улица",
    "пр": "проспект",
    "пр.": "проспект",
    "просп": "проспект",
    "просп.": "проспект",
    "проспект": "проспект",
    "пер": "переулок",
    "пер.": "переулок",
    "переулок": "переулок",
    "бул": "бульвар",
    "бул.": "бульвар",
    "бульвар": "бульвар",
    "пл": "площадь",
    "пл.": "площадь",
    "площадь": "площадь",
}


def _normalize_spacing(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" ,")


def _strip_landmarks(address: str) -> str:
    return _normalize_spacing(re.sub(r"\([^)]*\)", "", address))


def _normalize_ordinals(value: str) -> str:
    return re.sub(r"\b(\d+)[-\s]?(?:ой|ый|ая|я|й)\b", r"\1-й", value, flags=re.IGNORECASE)


def _normalize_street_types(value: str) -> str:
    normalized = value
    for source, target in _STREET_TYPE_ALIASES.items():
        normalized = re.sub(rf"\b{re.escape(source)}\b", target, normalized, flags=re.IGNORECASE)
    return normalized


def _normalize_house_spacing(value: str) -> str:
    normalized = re.sub(r",\s*", ", ", value)
    normalized = re.sub(r"\s*/\s*", "/", normalized)
    normalized = re.sub(r"(\d)\s+([а-яa-z])\b", r"\1\2", normalized, flags=re.IGNORECASE)
    return _normalize_spacing(normalized)


def _normalize_address(address: str, *, default_city: str) -> str:
    normalized = address.replace("_", " ").strip()
    normalized = _strip_landmarks(normalized)
    normalized = re.sub(r"(?<=\D)\.(?=\d)", " ", normalized)
    normalized = _normalize_ordinals(normalized)
    normalized = _normalize_street_types(normalized)
    normalized = _normalize_house_spacing(normalized)

    if default_city and default_city.lower() not in normalized.lower():
        normalized = f"{default_city}, {normalized}"

    return _normalize_spacing(normalized)


def build_geocode_queries(address: str, *, default_city: str) -> list[str]:
    base = _normalize_address(address, default_city=default_city)
    no_commas = _normalize_spacing(base.replace(",", " "))
    without_street_type = _normalize_spacing(
        re.sub(
            r"\b(улица|проспект|переулок|бульвар|площадь)\b\s+",
            "",
            base,
            flags=re.IGNORECASE,
        )
    )

    candidates: list[str] = []
    without_street_type_no_commas = _normalize_spacing(without_street_type.replace(",", " "))
    parts = [part.strip() for part in without_street_type.split(",") if part.strip()]
    if len(parts) >= 3:
        city_preserved_without_street_type = _normalize_spacing(
            f"{parts[0]}, {parts[1]} {parts[2]}"
        )
    else:
        city_preserved_without_street_type = without_street_type
    for candidate in (
        base,
        no_commas,
        without_street_type,
        without_street_type_no_commas,
        city_preserved_without_street_type,
    ):
        if candidate and candidate not in candidates:
            candidates.append(candidate)
    return candidates


def normalize_address_for_matching(address: str, *, default_city: str) -> str:
    normalized = _normalize_address(address, default_city=default_city).lower().replace("ё", "е")
    normalized = normalized.replace("-", " ")
    normalized = re.sub(
        r"\b(улица|проспект|переулок|бульвар|площадь)\b",
        " ",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(r"[^a-zа-я0-9/ -]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized
