import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings


class VectorStore:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.VECTOR_DB_PATH
        base_dir = Path(__file__).resolve().parent.parent.parent
        resolved_path = (base_dir / self.db_path).resolve()
        os.makedirs(resolved_path, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(resolved_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection_name = "schemes_collection"

    def get_or_create_collection(self):
        return self.client.get_or_create_collection(name=self.collection_name)

    def add_chunks(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ):
        collection = self.get_or_create_collection()
        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        try:
            collection = self.client.get_collection(name=self.collection_name)
        except Exception:
            return []

        total_count = collection.count()
        if total_count == 0:
            return []

        kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k, total_count),
        }
        if where_filter:
            kwargs["where"] = where_filter

        results = collection.query(**kwargs)

        chunks = []
        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            dists = (
                results["distances"][0]
                if results.get("distances")
                else [0.0] * len(docs)
            )
            for doc, meta, dist in zip(docs, metas, dists):
                chunks.append({
                    "text": doc,
                    "metadata": meta,
                    "distance": dist,
                })

        return chunks

    def count(self) -> int:
        try:
            collection = self.client.get_collection(name=self.collection_name)
            return collection.count()
        except Exception:
            return 0
