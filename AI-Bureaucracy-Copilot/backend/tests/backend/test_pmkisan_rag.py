import pytest
from app.rag.embedding_service import EmbeddingService
from app.rag.ingestion_service import (
    prepare_pm_kisan_chunks,
    prepare_scheme_chunks,
    ingest_pm_kisan_to_vector_db,
)
from app.rag.vector_store import VectorStore
from app.services.rag_retrieval_service import retrieve_context


def test_scenario_1_pm_kisan_chunks_and_metadata_validation():
    """
    Scenario 1: Extract, clean, and chunk PM-KISAN dataset.
    Verify required metadata: scheme_name=PM-KISAN, government_level=central,
    ministry, source_url, topic, and sector.
    """
    chunks = prepare_pm_kisan_chunks()
    assert len(chunks) >= 5, "Expected at least 5 semantic chunks for PM-KISAN"

    required_keys = [
        "scheme_name",
        "government_level",
        "level",
        "ministry",
        "source_url",
        "topic",
        "sector",
        "scheme_id",
    ]

    for chunk in chunks:
        assert "id" in chunk
        assert "text" in chunk
        assert "metadata" in chunk

        meta = chunk["metadata"]
        for key in required_keys:
            assert key in meta, f"Missing required metadata key '{key}' in chunk {chunk['id']}"

        assert meta["scheme_name"] == "PM-KISAN"
        assert meta["government_level"] == "central"
        assert meta["level"] == "central"
        assert meta["ministry"] == "Ministry of Agriculture and Farmers Welfare"
        assert meta["source_url"] == "https://pmkisan.gov.in"
        assert meta["sector"] == "agriculture"
        assert meta["topic"] is not None and len(meta["topic"]) > 0


def test_scenario_2_no_beneficiary_pii_stored():
    """
    Scenario 2: Verify that no beneficiary personally identifiable information (PII)
    is stored in the dataset or chunk texts.
    """
    chunks = prepare_pm_kisan_chunks()
    for chunk in chunks:
        text = chunk["text"].lower()
        # Verify text is generic policy/guidelines, not individual citizen records
        assert "beneficiary name:" not in text
        assert "aadhaar no:" not in text
        assert "bank account no:" not in text
        assert "phone number:" not in text


def test_scenario_3_preserve_existing_mock_data_and_insert():
    """
    Scenario 3: Verify that PM-KISAN ingestion preserves existing mock data in ChromaDB
    and adds the new official PM-KISAN chunks alongside them.
    """
    vs = VectorStore()
    es = EmbeddingService()

    # Ingest mock schemes first if collection is empty
    if vs.count() == 0:
        mock_chunks = prepare_scheme_chunks()
        m_ids = [c["id"] for c in mock_chunks]
        m_docs = [c["text"] for c in mock_chunks]
        m_meta = [c["metadata"] for c in mock_chunks]
        m_embs = [EmbeddingService.mock_embedding(t) for t in m_docs]
        vs.add_chunks(m_ids, m_docs, m_embs, m_meta)

    count_before = vs.count()
    assert count_before >= 20, "Expected existing mock chunks in collection"

    # Ingest PM-KISAN chunks using mock embeddings for fast offline testing
    pm_chunks = prepare_pm_kisan_chunks()
    p_ids = [c["id"] for c in pm_chunks]
    p_docs = [c["text"] for c in pm_chunks]
    p_meta = [c["metadata"] for c in pm_chunks]
    p_embs = [EmbeddingService.mock_embedding(t) for t in p_docs]

    vs.add_chunks(p_ids, p_docs, p_embs, p_meta)

    count_after = vs.count()
    assert count_after >= count_before, "Existing chunks must be preserved after upsert"
    assert count_after >= 27, "Collection should contain both mock schemes and PM-KISAN chunks"


def test_scenario_4_retrieval_query_returns_pm_kisan_chunks():
    """
    Scenario 4: Test query 'What is PM-KISAN and what benefits does it provide?'
    and verify that retrieval returns PM-KISAN chunks with high relevance.
    """
    query = "What is PM-KISAN and what benefits does it provide?"

    # Ensure PM-KISAN is in the vector store
    vs = VectorStore()
    pm_chunks = prepare_pm_kisan_chunks()
    p_ids = [c["id"] for c in pm_chunks]
    p_docs = [c["text"] for c in pm_chunks]
    p_meta = [c["metadata"] for c in pm_chunks]

    try:
        es = EmbeddingService()
        p_embs = es.embed_documents(p_docs)
        query_emb = es.embed_query(query)
    except Exception:
        # Fallback to mock embeddings for test environment
        p_embs = [EmbeddingService.mock_embedding(t) for t in p_docs]
        query_emb = EmbeddingService.mock_embedding(query)

    vs.add_chunks(p_ids, p_docs, p_embs, p_meta)

    # Query ChromaDB directly or via retrieve_context
    results = vs.query(query_embedding=query_emb, top_k=4)
    assert len(results) > 0

    pm_kisan_matches = [
        r for r in results if r["metadata"].get("scheme_name") == "PM-KISAN"
    ]
    assert len(pm_kisan_matches) > 0, "Expected at least one PM-KISAN chunk in top results"

    top_pm = pm_kisan_matches[0]
    assert "PM-KISAN" in top_pm["text"]
    assert top_pm["metadata"]["government_level"] == "central"
    assert top_pm["metadata"]["ministry"] == "Ministry of Agriculture and Farmers Welfare"
    assert top_pm["metadata"]["source_url"] == "https://pmkisan.gov.in"


def test_scenario_5_metadata_filtering():
    """
    Scenario 5: Verify that filtering by scheme_id='PM-KISAN' returns only PM-KISAN chunks.
    """
    vs = VectorStore()
    query_emb = EmbeddingService.mock_embedding("PM-KISAN agriculture installment")

    results = vs.query(
        query_embedding=query_emb,
        top_k=5,
        where_filter={"scheme_id": "PM-KISAN"},
    )

    assert len(results) > 0
    for r in results:
        assert r["metadata"]["scheme_name"] == "PM-KISAN"
        assert r["metadata"]["government_level"] == "central"
        assert r["metadata"]["sector"] == "agriculture"
