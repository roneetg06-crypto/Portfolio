import sys
from pathlib import Path

# Add backend root directory to Python path if run standalone
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.rag.embedding_service import EmbeddingService
from app.rag.ingestion_service import prepare_pm_kisan_chunks, prepare_scheme_chunks
from app.rag.vector_store import VectorStore


def build_vector_index():
    print("Starting vector index build process...")

    chunks = prepare_scheme_chunks()
    try:
        pm_kisan_chunks = prepare_pm_kisan_chunks()
        chunks.extend(pm_kisan_chunks)
    except Exception as e:
        print(f"Note: PM-KISAN raw dataset indexing skipped: {e}")

    if not chunks:
        print("No scheme chunks found to index.")
        return

    print(f"Prepared {len(chunks)} scheme chunks for indexing.")

    ids = [chunk["id"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]

    embedding_service = EmbeddingService()
    print("Generating embeddings...")
    embeddings = embedding_service.embed_documents(documents)

    vector_store = VectorStore()
    print(f"Upserting {len(chunks)} chunks into ChromaDB at '{vector_store.db_path}'...")
    vector_store.add_chunks(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(f"Vector index successfully built! Total items in collection: {vector_store.count()}")


if __name__ == "__main__":
    build_vector_index()
