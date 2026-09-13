"""
Tests for PM-KISAN Action Routing and Retrieval Default Handling:
- Verifies retrieval without sector restriction enables cross-scheme querying.
- Verifies controlled mapping for actionable PM-KISAN tasks:
  * new_farmer_registration -> https://pmkisan.gov.in/RegistrationFormnew.aspx
  * beneficiary_status -> https://pmkisan.gov.in/BeneficiaryStatus_New.aspx
  * self_registered_farmer_status -> https://pmkisan.gov.in/FarmerStatus.aspx
- Verifies informational queries do NOT trigger action routing.
- Verifies no invented/hallucinated URLs are produced.
- Verifies integration with /api/knowledge/ask endpoint.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.pmkisan_action_router import (
    PM_KISAN_ACTION_ROUTES,
    detect_pmkisan_action,
)
from app.services.rag_retrieval_service import retrieve_context
from app.agents.knowledge_agent.graph import run_knowledge_agent

client = TestClient(app)


def test_scenario_1_controlled_action_routes_integrity():
    """All PM-KISAN action routes must point to official gov.in URLs with human verification."""
    expected_actions = {
        "new_farmer_registration": "https://pmkisan.gov.in/RegistrationFormnew.aspx",
        "beneficiary_status": "https://pmkisan.gov.in/BeneficiaryStatus_New.aspx",
        "self_registered_farmer_status": "https://pmkisan.gov.in/FarmerStatus.aspx",
    }
    for action_key, expected_url in expected_actions.items():
        assert action_key in PM_KISAN_ACTION_ROUTES
        route = PM_KISAN_ACTION_ROUTES[action_key]
        assert route["action_url"] == expected_url
        assert route["requires_human_verification"] is True
        assert "pmkisan.gov.in" in route["action_url"]


def test_scenario_2_informational_queries_no_action():
    """Informational queries must NOT trigger action routing."""
    queries = [
        "What is PM-KISAN?",
        "How much benefit does PM-KISAN provide?",
        "Who is eligible for PM-KISAN?",
        "Tell me about PM-KISAN scheme",
    ]
    for q in queries:
        action = detect_pmkisan_action(q, explicit_scheme_id="PM-KISAN")
        assert action is None, f"Query '{q}' should be informational only, got action {action}"


def test_scenario_3_actionable_queries_match_controlled_routes():
    """Actionable queries must return exact controlled actions without LLM URL invention."""
    # 1. New Farmer Registration
    reg_action = detect_pmkisan_action("I want to register as a farmer.")
    assert reg_action is not None
    assert reg_action["action"] == "new_farmer_registration"
    assert reg_action["action_url"] == "https://pmkisan.gov.in/RegistrationFormnew.aspx"
    assert reg_action["requires_human_verification"] is True

    # 2. Beneficiary Status
    status_action = detect_pmkisan_action("I want to check my PM-KISAN beneficiary status.")
    assert status_action is not None
    assert status_action["action"] == "beneficiary_status"
    assert status_action["action_url"] == "https://pmkisan.gov.in/BeneficiaryStatus_New.aspx"
    assert status_action["requires_human_verification"] is True

    # 3. Self Registered Farmer Status
    self_status_action = detect_pmkisan_action("How to check self registered farmer status?")
    assert self_status_action is not None
    assert self_status_action["action"] == "self_registered_farmer_status"
    assert self_status_action["action_url"] == "https://pmkisan.gov.in/FarmerStatus.aspx"
    assert self_status_action["requires_human_verification"] is True


def test_scenario_4_retrieval_default_relaxation_and_scheme_filter():
    """
    Retrieval without sector restriction queries across all schemes.
    Explicit scheme_id or sector filters are respected.
    """
    # Test with scheme_id="PM-KISAN"
    pmkisan_chunks = retrieve_context(
        query="PM-KISAN guidelines and benefits",
        scheme_id="PM-KISAN",
        top_k=2,
    )
    assert len(pmkisan_chunks) > 0
    for chunk in pmkisan_chunks:
        assert chunk["metadata"]["scheme_id"] == "PM-KISAN"

    # Test with sector="health" still preserves mock health schemes
    health_chunks = retrieve_context(
        query="hospital coverage benefits",
        sector="health",
        top_k=2,
    )
    assert len(health_chunks) > 0
    for chunk in health_chunks:
        assert chunk["metadata"]["sector"] == "health"


def test_scenario_5_end_to_end_knowledge_agent_test_queries():
    """
    Runs the 4 required user queries through run_knowledge_agent with mocked LLM:
    1. 'What is PM-KISAN?' -> Informational, action=None
    2. 'How much benefit does PM-KISAN provide?' -> Informational, action=None
    3. 'I want to register as a farmer.' -> Actionable, action=new_farmer_registration
    4. 'I want to check my PM-KISAN beneficiary status.' -> Actionable, action=beneficiary_status
    """
    with patch(
        "app.agents.knowledge_agent.graph._call_ollama_llm"
    ) as mock_llm:
        # Query 1: What is PM-KISAN?
        mock_llm.return_value = "PM-KISAN is a Central Sector Scheme providing income support to landholding farmers."
        res1 = run_knowledge_agent(question="What is PM-KISAN?")
        assert res1["grounded"] is True
        assert res1["action"] is None
        assert res1["action_url"] is None
        assert "income support" in res1["answer"]

        # Query 2: How much benefit does PM-KISAN provide?
        mock_llm.return_value = "Under PM-KISAN, eligible farmers receive Rs. 6,000 per year in three installments."
        res2 = run_knowledge_agent(question="How much benefit does PM-KISAN provide?")
        assert res2["grounded"] is True
        assert res2["action"] is None
        assert res2["action_url"] is None
        assert "6,000" in res2["answer"]

        # Query 3: I want to register as a farmer.
        mock_llm.return_value = "You can register for PM-KISAN by submitting your Aadhaar and land details on the official portal."
        res3 = run_knowledge_agent(question="I want to register as a farmer.")
        assert res3["action"] == "new_farmer_registration"
        assert res3["action_url"] == "https://pmkisan.gov.in/RegistrationFormnew.aspx"
        assert res3["requires_human_verification"] is True
        assert res3["scheme_id"] == "PM-KISAN"

        # Query 4: I want to check my PM-KISAN beneficiary status.
        mock_llm.return_value = "To check your beneficiary status, enter your registration number and OTP on the official portal."
        res4 = run_knowledge_agent(question="I want to check my PM-KISAN beneficiary status.")
        assert res4["action"] == "beneficiary_status"
        assert res4["action_url"] == "https://pmkisan.gov.in/BeneficiaryStatus_New.aspx"
        assert res4["requires_human_verification"] is True
        assert res4["scheme_id"] == "PM-KISAN"


def test_scenario_6_api_endpoint_ask_knowledge_agent_returns_action():
    """POST /api/knowledge/ask endpoint returns structured action route fields."""
    with patch(
        "app.agents.knowledge_agent.graph._call_ollama_llm",
        return_value="Check your status via the official portal.",
    ), patch(
        "app.api.knowledge.VectorStore"
    ) as mock_vs:
        mock_vs.return_value.count.return_value = 27

        payload = {
            "question": "I want to check my PM-KISAN beneficiary status.",
        }
        response = client.post("/api/knowledge/ask", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "beneficiary_status"
        assert data["action_url"] == "https://pmkisan.gov.in/BeneficiaryStatus_New.aspx"
        assert data["requires_human_verification"] is True
        assert data["scheme_id"] == "PM-KISAN"
