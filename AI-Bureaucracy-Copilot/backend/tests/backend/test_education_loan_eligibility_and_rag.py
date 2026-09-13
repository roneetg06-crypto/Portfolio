import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.eligibility_service import evaluate_scheme_eligibility
from app.services.scheme_discovery_service import discover_schemes
from app.services.rag_retrieval_service import retrieve_context

client = TestClient(app)


def test_eligibility_evaluation_eligible_student():
    """Verify an eligible student passes all criteria."""
    result = evaluate_scheme_eligibility(
        scheme_id="SCH-EDU-001",
        profile_data={"age": 21, "state": "Maharashtra"},
        form_data={"annual_family_income": 450000, "course": "B.Tech"},
    )
    assert result["eligible"] is True
    assert len(result["reasons"]) == 0
    assert any(c["criterion"].startswith("Age") and c["status"] == "PASS" for c in result["criteria_summary"])
    assert any(c["criterion"].startswith("Annual Family Income") and c["status"] == "PASS" for c in result["criteria_summary"])


def test_eligibility_evaluation_underage():
    """Verify student below 16 years is flagged ineligible."""
    result = evaluate_scheme_eligibility(
        scheme_id="SCH-EDU-001",
        profile_data={"age": 14, "state": "Delhi"},
        form_data={"annual_family_income": 300000},
    )
    assert result["eligible"] is False
    assert any("below the minimum required age of 16" in r for r in result["reasons"])


def test_eligibility_evaluation_overage():
    """Verify applicant above 35 years is flagged ineligible."""
    result = evaluate_scheme_eligibility(
        scheme_id="SCH-EDU-001",
        profile_data={"age": 42, "state": "Karnataka"},
        form_data={"annual_family_income": 300000},
    )
    assert result["eligible"] is False
    assert any("exceeds the maximum allowable age of 35" in r for r in result["reasons"])


def test_eligibility_evaluation_excess_income():
    """Verify annual family income over 8 Lakhs is flagged."""
    result = evaluate_scheme_eligibility(
        scheme_id="SCH-EDU-001",
        profile_data={"age": 22, "state": "Gujarat"},
        form_data={"annual_family_income": 1200000},
    )
    assert result["eligible"] is False
    assert any("exceeds the limit of Rs. 800,000" in r for r in result["reasons"])


def test_scheme_discovery_all_states():
    """Verify SCH-EDU-001 is discoverable across different Indian states."""
    for test_state in ["Punjab", "Tamil Nadu", "Assam", "Maharashtra", "Delhi"]:
        schemes = discover_schemes(state=test_state, sector=None)
        scheme_ids = [s.scheme_id for s in schemes]
        assert "SCH-EDU-001" in scheme_ids, f"SCH-EDU-001 not found for state {test_state}"


def test_rag_retrieval_finds_education_loan_chunks():
    """Verify RAG retrieval fetches SCH-EDU-001 chunks for education loan queries."""
    chunks = retrieve_context("What is the interest subsidy and age limit for National Student Education Loan?")
    assert len(chunks) > 0
    edu_chunks = [c for c in chunks if c["metadata"].get("scheme_id") == "SCH-EDU-001"]
    assert len(edu_chunks) > 0
    top_chunk = edu_chunks[0]
    assert "SCH-EDU-001" == top_chunk["metadata"]["scheme_id"]


def test_evaluate_eligibility_api_endpoint():
    """Verify POST /api/schemes/SCH-EDU-001/evaluate-eligibility returns criteria assessment."""
    payload = {
        "data": {
            "age": 20,
            "annual_family_income": 350000,
            "state": "Uttar Pradesh",
        }
    }
    res = client.post("/api/schemes/SCH-EDU-001/evaluate-eligibility", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["scheme_id"] == "SCH-EDU-001"
    assert data["eligible"] is True
    assert len(data["criteria_summary"]) >= 2


def test_submit_information_blocks_ineligible_applicant():
    """Verify POST /api/schemes/SCH-EDU-001/information blocks underage applicant."""
    payload = {
        "data": {
            "date_of_birth": "2015-01-01",  # Age ~11
            "category": "General",
            "parent_name": "Test Parent",
            "parent_occupation": "Salaried / Private",
            "annual_family_income": 300000,
            "aadhaar_last_four": "1234",
            "course": "B.Tech",
            "college": "Test College",
            "loan_amount": 500000,
            "tuition_fee": 350000,
            "living_expenses": 150000,
            "bank_preference": "State Bank of India",
            "loan_tenure": "10 Years",
        }
    }
    res = client.post("/api/schemes/SCH-EDU-001/information", json=payload)
    assert res.status_code == 422
    err_msg = res.json().get("error") or res.json().get("detail", "")
    assert "Eligibility criteria validation failed" in err_msg
    assert "Age 11 is below the minimum required age of 16 years" in err_msg
