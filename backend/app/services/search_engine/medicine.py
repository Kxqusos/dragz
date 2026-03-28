from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SearchQueryAnalysis:
    intent: str
    canonical_query: str
    candidates: list[str]


_PHRASE_ALIASES = {
    "nurofen": "ибупрофен",
    "нурофен": "ибупрофен",
    "advil": "ибупрофен",
    "ibuprofen": "ибупрофен",
    "panadol": "парацетамол",
    "панадол": "парацетамол",
    "paracetamol": "парацетамол",
    "vitamin d3": "витамин д3",
    "vit d3": "витамин д3",
    "витамин d3": "витамин д3",
    "витамин d 3": "витамин д3",
    "vitamin d": "витамин д",
    "vit d": "витамин д",
    "aquadetrim": "витамин д3",
    "аквадетрим": "витамин д3",
}

_BRAND_VARIANTS = {
    "ибупрофен": "нурофен",
    "парацетамол": "панадол",
    "витамин д3": "аквадетрим",
}

_FORM_ALIASES = {
    "tabs": "таблетки",
    "tab": "таблетки",
    "tablet": "таблетки",
    "tablets": "таблетки",
    "таб": "таблетки",
    "табл": "таблетки",
    "таблетки": "таблетки",
    "caps": "капсулы",
    "cap": "капсулы",
    "capsule": "капсулы",
    "capsules": "капсулы",
    "капс": "капсулы",
    "капсула": "капсулы",
    "капсулы": "капсулы",
    "syrup": "сироп",
    "spray": "спрей",
    "drops": "капли",
}

_UNIT_ALIASES = {
    "mg": "мг",
    "мг": "мг",
    "g": "г",
    "гр": "г",
    "ml": "мл",
    "мл": "мл",
    "mcg": "мкг",
    "мкг": "мкг",
    "iu": "ме",
    "ед": "ме",
    "ме": "ме",
}

_SYMPTOM_HINTS = (
    "боль",
    "болит",
    "температура",
    "горло",
    "насморк",
    "кашель",
    "простуда",
    "голова",
    "головная",
)

_NON_DRUG_HINTS = (
    "аптека",
    "аптеки",
    "маршрут",
    "рядом",
    "адрес",
)


def _normalize_raw_query(query: str) -> str:
    normalized = query.lower().replace("ё", "е").strip()
    normalized = re.sub(r"[,+]", " ", normalized)
    normalized = re.sub(r"\bd\s*3\b", "д3", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(\d)([a-zа-я]+)", r"\1 \2", normalized)
    normalized = re.sub(r"([a-zа-я]+)(\d)", r"\1 \2", normalized)
    normalized = re.sub(r"\bд\s+3\b", "д3", normalized, flags=re.IGNORECASE)

    for source, target in sorted(_PHRASE_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        normalized = re.sub(rf"\b{re.escape(source)}\b", target, normalized)

    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _normalize_tokens(normalized_query: str) -> list[str]:
    tokens = re.findall(r"[a-zа-я0-9/.-]+", normalized_query)
    cleaned_tokens: list[str] = []

    for token in tokens:
        unit = _UNIT_ALIASES.get(token)
        form = _FORM_ALIASES.get(token)
        if unit:
            cleaned_tokens.append(unit)
        elif form:
            cleaned_tokens.append(form)
        else:
            cleaned_tokens.append(token)

    return cleaned_tokens


def _extract_form(tokens: list[str]) -> str | None:
    for token in tokens:
        if token in {"таблетки", "капсулы", "сироп", "спрей", "капли"}:
            return token
    return None


def _extract_dosage(tokens: list[str]) -> str | None:
    for index, token in enumerate(tokens[:-1]):
        if re.fullmatch(r"\d+[.,]?\d*", token) and tokens[index + 1] in {"мг", "г", "мл", "мкг", "ме"}:
            return f"{token} {tokens[index + 1]}"
    return None


def _extract_drug_name(normalized_query: str) -> str:
    for alias in sorted(set(_PHRASE_ALIASES.values()), key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", normalized_query):
            return alias

    words = [token for token in _normalize_tokens(normalized_query) if not re.search(r"\d", token)]
    meaningful = [
        token for token in words
        if token not in _UNIT_ALIASES.values()
        and token not in _FORM_ALIASES.values()
    ]
    return " ".join(meaningful[:2]).strip()


def _build_canonical_query(drug_name: str, dosage: str | None, form: str | None) -> str:
    parts = [drug_name]
    if dosage:
        parts.append(dosage)
    if form:
        parts.append(form)
    return " ".join(part for part in parts if part).strip()


def build_drug_search_candidates(query: str) -> list[str]:
    normalized_query = _normalize_raw_query(query)
    tokens = _normalize_tokens(normalized_query)
    drug_name = _extract_drug_name(normalized_query)
    dosage = _extract_dosage(tokens)
    form = _extract_form(tokens)

    candidates: list[str] = []
    canonical_query = _build_canonical_query(drug_name, dosage, form)
    if canonical_query:
        candidates.append(canonical_query)

    brand_variant = _BRAND_VARIANTS.get(drug_name)
    if brand_variant:
        brand_query = _build_canonical_query(brand_variant, dosage, form)
        if brand_query not in candidates:
            candidates.append(brand_query)

    if drug_name and drug_name not in candidates:
        candidates.append(drug_name)

    base_without_form = _build_canonical_query(drug_name, dosage, None)
    if base_without_form and base_without_form not in candidates:
        candidates.append(base_without_form)

    return [candidate for candidate in candidates if candidate]


def analyze_search_query(query: str) -> SearchQueryAnalysis:
    normalized_query = _normalize_raw_query(query)

    if any(hint in normalized_query for hint in _NON_DRUG_HINTS):
        return SearchQueryAnalysis(intent="non_drug", canonical_query="", candidates=[])

    if any(hint in normalized_query for hint in _SYMPTOM_HINTS):
        return SearchQueryAnalysis(intent="non_drug", canonical_query="", candidates=[])

    candidates = build_drug_search_candidates(query)
    return SearchQueryAnalysis(
        intent="drug" if candidates else "non_drug",
        canonical_query=candidates[0] if candidates else "",
        candidates=candidates,
    )


def normalize_query_key(query: str) -> str:
    normalized = _normalize_raw_query(query)
    normalized = re.sub(r"\s+", "", normalized)
    return normalized
