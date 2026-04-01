import re
from dataclasses import dataclass


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

_CITY_STOP_WORDS = {"ростов", "на", "дону"}


@dataclass(frozen=True)
class AddressMatchResult:
    is_match: bool
    matching_key: str
    match_strategy: str
    confidence_tier: str


def _normalize_spacing(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" ,")


def _strip_landmarks(address: str) -> str:
    return _normalize_spacing(re.sub(r"\([^)]*\)", "", address))


def _normalize_ordinals(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        number = match.group(1)
        next_word = match.group(2)
        suffix = "-я" if next_word.lower().endswith(("ая", "яя")) else "-й"
        return f"{number}{suffix} {next_word}"

    return re.sub(
        r"\b(\d+)[-\s]?(?:ой|ый|ая|я|й)\s+([А-Яа-яA-Za-z-]+)",
        replace,
        value,
        flags=re.IGNORECASE,
    )


def _normalize_street_types(value: str) -> str:
    normalized = value
    for source, target in _STREET_TYPE_ALIASES.items():
        normalized = re.sub(rf"\b{re.escape(source)}\b", target, normalized, flags=re.IGNORECASE)
    return normalized


def _normalize_house_spacing(value: str) -> str:
    normalized = re.sub(r",\s*", ", ", value)
    normalized = re.sub(r"\s*/\s*", "/", normalized)
    normalized = re.sub(
        r"(\d)\s+([а-яa-z])\b",
        lambda match: f"{match.group(1)}{match.group(2).lower()}",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(
        r"(\d)([а-яa-z])\b",
        lambda match: f"{match.group(1)}{match.group(2).lower()}",
        normalized,
        flags=re.IGNORECASE,
    )
    return _normalize_spacing(normalized)


def _strip_trailing_landmarks(value: str) -> str:
    house_match = re.search(r"\d+[а-яa-z]?(?:/\d+[а-яa-z]?)?", value, flags=re.IGNORECASE)
    if house_match is None:
        return value

    tail = value[house_match.end():]
    landmark_match = re.search(
        r"\b(?:ост\.?|остановка|рядом|напротив|возле|около|м/у|между|пл\.?|площадь)\b",
        tail,
        flags=re.IGNORECASE,
    )
    if landmark_match is None:
        return value

    return _normalize_spacing(value[:house_match.end() + landmark_match.start()])


def _normalize_address(address: str, *, default_city: str) -> str:
    normalized = address.replace("_", " ").strip()
    normalized = _strip_landmarks(normalized)
    normalized = re.sub(r"(?<=\D)\.(?=\d)", " ", normalized)
    normalized = _normalize_ordinals(normalized)
    normalized = _normalize_street_types(normalized)
    normalized = _normalize_house_spacing(normalized)
    normalized = _strip_trailing_landmarks(normalized)

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


def _extract_house_token(normalized_address: str) -> str:
    matches = re.findall(r"\b(\d+[а-яa-z]?(?:/\d+[а-яa-z]?)?)\b", normalized_address, flags=re.IGNORECASE)
    return matches[-1] if matches else ""


def _extract_street_tokens(normalized_address: str, house_token: str) -> set[str]:
    candidate = normalized_address
    if house_token:
        candidate = re.sub(rf"\b{re.escape(house_token)}\b", " ", candidate)
    return {
        token for token in re.findall(r"[a-zа-я0-9]+", candidate)
        if token not in _CITY_STOP_WORDS and not token.isdigit()
    }


def evaluate_address_match(
    *,
    expected_address: str,
    candidate_address: str,
    default_city: str,
) -> AddressMatchResult:
    expected_key = normalize_address_for_matching(expected_address, default_city=default_city)
    candidate_key = normalize_address_for_matching(candidate_address, default_city=default_city)

    expected_house = _extract_house_token(expected_key)
    candidate_house = _extract_house_token(candidate_key)
    expected_street_tokens = _extract_street_tokens(expected_key, expected_house)
    candidate_street_tokens = _extract_street_tokens(candidate_key, candidate_house)

    street_overlap = expected_street_tokens & candidate_street_tokens
    has_street_match = bool(expected_street_tokens) and expected_street_tokens <= candidate_street_tokens
    has_house_match = bool(expected_house) and expected_house == candidate_house

    if has_street_match and has_house_match:
        return AddressMatchResult(
            is_match=True,
            matching_key=expected_key,
            match_strategy="strict-house-and-street",
            confidence_tier="high",
        )

    if street_overlap:
        return AddressMatchResult(
            is_match=False,
            matching_key=expected_key,
            match_strategy="street-only",
            confidence_tier="low",
        )

    return AddressMatchResult(
        is_match=False,
        matching_key=expected_key,
        match_strategy="no-match",
        confidence_tier="none",
    )
