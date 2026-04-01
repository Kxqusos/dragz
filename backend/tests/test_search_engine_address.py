from app.services.search_engine.address import (
    build_geocode_queries,
    normalize_address_for_matching,
)


def test_build_geocode_queries_normalizes_street_type_and_removes_landmark_noise():
    queries = build_geocode_queries(
        "ул.1-ой Конной Армии,18/9 (рядом Магнит)",
        default_city="Ростов-на-Дону",
    )

    assert queries[0] == "Ростов-на-Дону, улица 1-й Конной Армии, 18/9"
    assert "Ростов-на-Дону, 1-й Конной Армии 18/9" in queries


def test_normalize_address_for_matching_builds_stable_matching_key():
    normalized = normalize_address_for_matching(
        "пр.Чехова,72 (м/у Пушкинской и Горького)",
        default_city="Ростов-на-Дону",
    )

    assert normalized == "ростов на дону чехова 72"


def test_build_geocode_queries_preserves_feminine_ordinal_street_names():
    queries = build_geocode_queries(
        "ул.2-я Краснодарская,145Д",
        default_city="Ростов-на-Дону",
    )

    assert queries[0] == "Ростов-на-Дону, улица 2-я Краснодарская, 145д"


def test_normalize_address_for_matching_strips_landmarks_outside_parentheses():
    normalized = normalize_address_for_matching(
        "пр.Нагибина,35 ост.Школа напротив Горизонт",
        default_city="Ростов-на-Дону",
    )

    assert normalized == "ростов на дону нагибина 35"


def test_normalize_address_for_matching_keeps_house_fraction_and_drops_square_landmarks():
    normalized = normalize_address_for_matching(
        "ул.Киргизская,43/26 пл.Чкалова",
        default_city="Ростов-на-Дону",
    )

    assert normalized == "ростов на дону киргизская 43/26"
