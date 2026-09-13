import sys
from pathlib import Path

# Add backend directory to path if run standalone
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.rag.embedding_service import EmbeddingService
from app.rag.ingestion_service import ingest_pm_kisan_to_vector_db, prepare_pm_kisan_chunks
from app.rag.vector_store import VectorStore
from app.services.rag_retrieval_service import retrieve_context


def run_ingestion():
    print("=================================================================")
    print("Ingesting Official PM-KISAN Government Dataset into ChromaDB RAG")
    print("=================================================================")

    vs = VectorStore()
    initial_count = vs.count()
    print(f"Existing chunks in collection before ingestion: {initial_count}")

    chunks = prepare_pm_kisan_chunks()
    print(f"Prepared {len(chunks)} official PM-KISAN chunks:")
    for idx, c in enumerate(chunks, 1):
        print(f"  {idx}. [{c['id']}] Topic: {c['metadata']['topic']}")

    es = EmbeddingService()
    print(f"\nGenerating embeddings using '{es.model}' ({es.provider})...")
    result = ingest_pm_kisan_to_vector_db(vector_store=vs, embedding_service=es)

    print("\nIngestion Result:")
    print(f"  Status: {result['status']}")
    print(f"  Chunks Indexed: {result['chunks_indexed']}")
    print(f"  Total Chunks in Collection: {result['total_collection_count']}")

    # Verification query
    test_query = "What is PM-KISAN and what benefits does it provide?"
    print(f"\nRunning verification query: '{test_query}'")
    retrieved = retrieve_context(query=test_query, top_k=3)

    print(f"\nRetrieved {len(retrieved)} chunks:")
    for idx, r in enumerate(retrieved, 1):
        meta = r["metadata"]
        print(f"\n--- Result #{idx} (Distance: {r.get('distance', 0.0):.4f}) ---")
        print(f"Scheme: {meta.get('scheme_name')} | Level: {meta.get('government_level', meta.get('level'))} | Ministry: {meta.get('ministry')}")
        print(f"Source URL: {meta.get('source_url')} | Topic: {meta.get('topic')}")
        print(f"Snippet: {r['text'][:180]}...")

    pm_kisan_retrieved = [r for r in retrieved if r["metadata"].get("scheme_name") == "PM-KISAN"]
    if pm_kisan_retrieved:
        print("\nSUCCESS: Verification query successfully returned PM-KISAN official chunks!")
    else:
        print("\nWARNING: Verification query did not return PM-KISAN chunks in top results.")


if __name__ == "__main__":
    run_ingestion()
