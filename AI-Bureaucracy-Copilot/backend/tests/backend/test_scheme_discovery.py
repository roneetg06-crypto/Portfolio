import pytest
from app.services.scheme_discovery_service import discover_schemes


def test_central_schemes_included_for_any_state():
    results = discover_schemes(state="Any State", sector="health")
    central_schemes = [s for s in results if s.level == "central"]
    assert len(central_schemes) >= 3
    names = [s.name for s in central_schemes]
    assert "Ayushman Bharat - PM-JAY" in names


def test_state_specific_filtering_andhra_pradesh_vs_kerala():
    ap_results = discover_schemes(state="Andhra Pradesh", sector="health")
    kerala_results = discover_schemes(state="Kerala", sector="health")

    ap_scheme_names = [s.name for s in ap_results]
    kerala_scheme_names = [s.name for s in kerala_results]

    # Andhra Pradesh state schemes should be present in AP results but not Kerala results
    assert "Dr. YSR Aarogyasri Scheme" in ap_scheme_names
    assert "Dr. YSR Aarogyasri Scheme" not in kerala_scheme_names

    # Kerala state schemes should be present in Kerala results but not AP results
    assert "Karunya Health Insurance Scheme (KHI)" in kerala_scheme_names
    assert "Karunya Health Insurance Scheme (KHI)" not in ap_scheme_names

    # Both should still include central schemes
    assert "Ayushman Bharat - PM-JAY" in ap_scheme_names
    assert "Ayushman Bharat - PM-JAY" in kerala_scheme_names


def test_state_with_no_state_schemes_returns_central_only():
    results = discover_schemes(state="Goa", sector="health")
    state_schemes = [s for s in results if s.level == "state"]
    central_schemes = [s for s in results if s.level == "central"]

    assert len(state_schemes) == 0
    assert len(central_schemes) >= 3


def test_sector_filtering():
    health_results = discover_schemes(state="Andhra Pradesh", sector="health")
    education_results = discover_schemes(state="Andhra Pradesh", sector="education")
    defense_results = discover_schemes(state="Andhra Pradesh", sector="defense")

    assert len(health_results) > 0
    assert len(education_results) == 1
    assert education_results[0].scheme_id == "SCH-EDU-001"
    assert len(defense_results) == 0
