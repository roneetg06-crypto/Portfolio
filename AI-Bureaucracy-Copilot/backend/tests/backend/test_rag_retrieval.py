"""
Tests for the RAG ingestion pipeline and retrieval filtering logic.
- Ingestion/chunking tests: fully in-memory, no external service needed.
- Retrieval tests: vector store query is mocked so tests run without Ollama or ChromaDB.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.rag.embedding_service import EmbeddingService
from app.rag.ingestion_service import prepare_scheme_chunks
from app.services.rag_retrieval_service import retrieve_context


# ---------------------------------------------------------------------------
# Shared fixture: a realistic set of mock chunks that span central and state schemes
# ---------------------------------------------------------------------------
MOCK_ALL_CHUNKS = [
    {
        "text": "Scheme Name: Ayushman Bharat - PM-JAY\nKey Benefits: Rs. 5 lakh central coverage.",
        "metadata": {
            "scheme_id": "SCH-HLT-001",
            "scheme_name": "Ayushman Bharat - PM-JAY",
            "level": "central",
            "applicable_states": "",
            "sector": "health",
        },
        "distance": 0.05,
    },
    {
        "text": "Scheme Name: NHM\nKey Benefits: Free essential drugs and maternal care.",
        "metadata": {
            "scheme_id": "SCH-HLT-002",
            "scheme_name": "National Health Mission (NHM)",
            "level": "central",
            "applicable_states": "",
            "sector": "health",
        },
        "distance": 0.10,
    },
    {
        "text": "Scheme Name: Dr. YSR Aarogyasri\nKey Benefits: Free treatment for BPL in AP.",
        "metadata": {
            "scheme_id": "SCH-HLT-004",
            "scheme_name": "Dr. YSR Aarogyasri Scheme",
            "level": "state",
            "applicable_states": "Andhra Pradesh",
            "sector": "health",
        },
        "distance": 0.12,
    },
    {
        "text": "Scheme Name: Karunya Health Insurance Scheme\nKey Benefits: Critical illness cover in Kerala.",
        "metadata": {
            "scheme_id": "SCH-HLT-006",
            "scheme_name": "Karunya Health Insurance Scheme (KHI)",
            "level": "state",
            "applicable_states": "Kerala",
            "sector": "health",
        },
        "distance": 0.20,
    },
]


# ---------------------------------------------------------------------------
# Ingestion & chunking tests (no external service)
# ---------------------------------------------------------------------------

def test_scheme_chunking_and_metadata():
    """Each scheme produces ≥2 chunks (overview + benefits) with required metadata fields."""
    chunks = prepare_scheme_chunks()
    assert len(chunks) >= 20  # 10 schemes × 2 chunks

    first = chunks[0]
    assert "id" in first
    assert "text" in first
    assert "metadata" in first

    meta = first["metadata"]
    for required_key in ("scheme_id", "scheme_name", "level", "sector"):
        assert required_key in meta, f"Missing metadata key: {required_key}"


def test_chunking_produces_overview_and_benefits():
    """Verify chunk types are correct for each scheme."""
    chunks = prepare_scheme_chunks()
    chunk_ids = [c["id"] for c in chunks]
    overview_count = sum(1 for cid in chunk_ids if "overview" in cid)
    benefits_count = sum(1 for cid in chunk_ids if "benefits" in cid)
    assert overview_count >= 10
    assert benefits_count >= 10


# ---------------------------------------------------------------------------
# Retrieval filtering tests (vector store mocked)
# ---------------------------------------------------------------------------

def _make_mock_vector_store(mock_chunks):
    """Returns a mock VectorStore whose .query() returns given chunks."""
    mock_vs = MagicMock()
    mock_vs.count.return_value = 20
    mock_vs.query.return_value = mock_chunks
    return mock_vs


def test_retrieval_andhra_pradesh_filter():
    """Retrieval with Andhra Pradesh returns only central + AP state schemes."""
    with patch("app.services.rag_retrieval_service.VectorStore") as mock_vs_cls, \
         patch("app.services.rag_retrieval_service.EmbeddingService") as mock_emb_cls:
        mock_vs_cls.return_value = _make_mock_vector_store(MOCK_ALL_CHUNKS)
        mock_emb_cls.return_value.embed_query.return_value = [0.1] * 768

        ap_chunks = retrieve_context(
            query="hospitalization coverage benefits",
            state="Andhra Pradesh",
            sector="health",
            top_k=4,
        )

    assert len(ap_chunks) > 0
    scheme_names = [c["metadata"]["scheme_name"] for c in ap_chunks]

    # Central schemes must be included
    assert "Ayushman Bharat - PM-JAY" in scheme_names
    # AP state scheme must be included
    assert "Dr. YSR Aarogyasri Scheme" in scheme_names
    # Kerala-only scheme must be excluded
    assert "Karunya Health Insurance Scheme (KHI)" not in scheme_names


def test_retrieval_excludes_other_state_schemes():
    """Kerala retrieval must not return Andhra Pradesh-only schemes."""
    with patch("app.services.rag_retrieval_service.VectorStore") as mock_vs_cls, \
         patch("app.services.rag_retrieval_service.EmbeddingService") as mock_emb_cls:
        mock_vs_cls.return_value = _make_mock_vector_store(MOCK_ALL_CHUNKS)
        mock_emb_cls.return_value.embed_query.return_value = [0.2] * 768

        kerala_chunks = retrieve_context(
            query="health coverage benefits",
            state="Kerala",
            sector="health",
            top_k=6,
        )

    scheme_names = [c["metadata"]["scheme_name"] for c in kerala_chunks]
    assert "Dr. YSR Aarogyasri Scheme" not in scheme_names, (
        "AP-specific scheme must not appear in Kerala results"
    )
    assert "Karunya Health Insurance Scheme (KHI)" in scheme_names


# ---------------------------------------------------------------------------
# EmbeddingService mock embedding utility
# ---------------------------------------------------------------------------

def test_embedding_service_mock_is_deterministic():
    """Mock embeddings produce same vector for same text, different for different text."""
    v1 = EmbeddingService.mock_embedding("test text")
    v2 = EmbeddingService.mock_embedding("test text")
    v3 = EmbeddingService.mock_embedding("different text")
    assert v1 == v2
    assert v1 != v3
    assert len(v1) == 768  # nomic-embed-text output dimension
