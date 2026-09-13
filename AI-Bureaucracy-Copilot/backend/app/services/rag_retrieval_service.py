from typing import Any, Dict, List, Optional
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore


def retrieve_context(
    query: str,
    state: Optional[str] = None,
    sector: Optional[str] = None,
    scheme_id: Optional[str] = None,
    top_k: int = 4,
) -> List[Dict[str, Any]]:
    vector_store = VectorStore()
    if vector_store.count() == 0:
        return []

    embedding_service = EmbeddingService()
    query_embedding = embedding_service.embed_query(query)

    where_filter: Dict[str, Any] = {}

    if scheme_id and scheme_id.strip():
        where_filter["scheme_id"] = scheme_id.strip()
    elif sector and sector.strip():
        where_filter["sector"] = sector.strip().lower()

    results = vector_store.query(
        query_embedding=query_embedding,
        top_k=top_k * 2 if state else top_k,
        where_filter=where_filter if where_filter else None,
    )

    if not state or not state.strip():
        return results[:top_k]

    target_state = state.strip().lower()
    filtered = []
    for chunk in results:
        meta = chunk["metadata"]
        level = meta.get("level", "").lower()
        if level == "central":
            filtered.append(chunk)
        elif level == "state":
            applicable = [
                s.strip().lower()
                for s in meta.get("applicable_states", "").split(",")
                if s.strip()
            ]
            if target_state in applicable:
                filtered.append(chunk)

    return filtered[:top_k]
