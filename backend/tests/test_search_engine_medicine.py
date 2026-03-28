from app.services.search_engine.medicine import (
    analyze_search_query,
    build_drug_search_candidates,
)


def test_build_drug_search_candidates_normalizes_brand_and_dosage():
    candidates = build_drug_search_candidates("Nurofen 200mg tabs")

    assert candidates[0] == "ибупрофен 200 мг таблетки"
    assert "нурофен 200 мг таблетки" in candidates
    assert "ибупрофен" in candidates


def test_build_drug_search_candidates_normalizes_vitamin_d_notation():
    candidates = build_drug_search_candidates("витамин d3 2000ме капсулы")

    assert candidates[0] == "витамин д3 2000 ме капсулы"
    assert "витамин д3" in candidates


def test_analyze_search_query_keeps_symptom_queries_out_of_pharmacy_search_engine():
    normalized = analyze_search_query("сильная головная боль и температура")

    assert normalized.intent == "non_drug"
    assert normalized.canonical_query == ""
    assert normalized.candidates == []
