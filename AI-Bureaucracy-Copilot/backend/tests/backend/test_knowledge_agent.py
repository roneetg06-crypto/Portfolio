"""
Tests for the Knowledge Agent graph and /api/knowledge/ask endpoint.
Ollama LLM and embedding calls are mocked so tests run without a live Ollama service.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.rag.embedding_service import EmbeddingService

client = TestClient(app)


def _make_mock_chunks():
    return [
        {
            "text": (
                "Scheme Name: Ayushman Bharat - PM-JAY\n"
                "Key Benefits and Coverage: Rs. 5,000,000 annual health cover per family."
            ),
            "metadata": {
                "scheme_id": "SCH-HLT-001",
                "scheme_name": "Ayushman Bharat - PM-JAY",
                "level": "central",
                "applicable_states": "",
                "sector": "health",
            },
            "distance": 0.1,
        }
    ]


def test_knowledge_agent_known_question_mocked():
    """Knowledge Agent returns a grounded answer when context is available."""
    mock_chunks = _make_mock_chunks()

    with patch(
        "app.agents.knowledge_agent.graph.retrieve_context",
        return_value=mock_chunks,
    ), patch(
        "app.agents.knowledge_agent.graph._call_ollama_llm",
        return_value="Ayushman Bharat provides Rs. 5 lakh annual health coverage per family.",
    ):
        from app.agents.knowledge_agent.graph import run_knowledge_agent
        result = run_knowledge_agent(
            question="What are the benefits of Ayushman Bharat?",
            state="Andhra Pradesh",
            sector="health",
        )

    assert result["grounded"] is True
    assert len(result["sources"]) > 0
    assert "answer" in result
    assert len(result["answer"]) > 0


def test_knowledge_agent_unknown_question_returns_ungrounded():
    """Knowledge Agent returns grounded=False when no context is found."""
    with patch(
        "app.agents.knowledge_agent.graph.retrieve_context",
        return_value=[],
    ):
        from app.agents.knowledge_agent.graph import run_knowledge_agent
        result = run_knowledge_agent(
            question="What is the policy for space exploration grants?",
            state="Kerala",
            sector="health",
        )

    assert result["grounded"] is False
    assert result["sources"] == []
    assert "don't have information" in result["answer"].lower() or "not available" in result["answer"].lower()


def test_knowledge_ask_endpoint_success():
    """POST /api/knowledge/ask returns 200 with answer, sources, and grounded flag."""
    mock_chunks = _make_mock_chunks()

    with patch(
        "app.agents.knowledge_agent.graph.retrieve_context",
        return_value=mock_chunks,
    ), patch(
        "app.agents.knowledge_agent.graph._call_ollama_llm",
        return_value="PM-JAY provides up to Rs. 5 lakh hospital cover per family.",
    ), patch(
        "app.api.knowledge.VectorStore"
    ) as mock_vs_cls:
        mock_vs_cls.return_value.count.return_value = 20
        payload = {
            "question": "Tell me about PM-JAY benefits",
            "state": "Andhra Pradesh",
            "sector": "health",
        }
        response = client.post("/api/knowledge/ask", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "grounded" in data


def test_knowledge_ask_endpoint_empty_question():
    """POST /api/knowledge/ask returns 422 when question is blank."""
    payload = {"question": "   ", "state": "Andhra Pradesh"}
    response = client.post("/api/knowledge/ask", json=payload)
    assert response.status_code == 422
    assert "error" in response.json()


def test_knowledge_ask_endpoint_ollama_unreachable():
    """Returns 500 with clear error message when Ollama is unreachable."""
    mock_chunks = _make_mock_chunks()

    with patch(
        "app.agents.knowledge_agent.graph.retrieve_context",
        return_value=mock_chunks,
    ), patch(
        "app.agents.knowledge_agent.graph._call_ollama_llm",
        side_effect=RuntimeError(
            "Cannot reach Ollama at http://localhost:11434 — is `ollama serve` running?"
        ),
    ), patch(
        "app.api.knowledge.VectorStore"
    ) as mock_vs_cls:
        mock_vs_cls.return_value.count.return_value = 20
        payload = {
            "question": "What benefits does NHM offer?",
            "state": "Kerala",
            "sector": "health",
        }
        response = client.post("/api/knowledge/ask", json=payload)

    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert "ollama" in data["error"].lower() or "Cannot reach" in data["error"]


def test_embedding_service_mock_embedding_is_deterministic():
    """Mock embeddings produce same vector for same input text."""
    vec1 = EmbeddingService.mock_embedding("test text")
    vec2 = EmbeddingService.mock_embedding("test text")
    assert vec1 == vec2
    assert len(vec1) == 768  # nomic-embed-text dimension
