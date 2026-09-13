import hashlib
from typing import List
from app.core.config import settings

# Dimension for nomic-embed-text is 768; used as default for Ollama embedding models.
# The mock fallback uses this same dimension for test consistency.
OLLAMA_EMBED_DIM = 768


def _call_ollama_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Calls the Ollama local embedding API for a batch of texts.
    Raises a RuntimeError with a clear message if Ollama is unreachable.
    """
    import httpx

    url = f"{settings.OLLAMA_BASE_URL}/api/embed"
    results: List[List[float]] = []

    for text in texts:
        try:
            response = httpx.post(
                url,
                json={"model": settings.EMBEDDING_MODEL, "input": text},
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            # Ollama /api/embed returns {"embeddings": [[...], ...]}
            embedding = data.get("embeddings", [[]])[0]
            results.append(embedding)
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot reach Ollama at {settings.OLLAMA_BASE_URL} — "
                "is `ollama serve` running and is the embedding model pulled? "
                f"(Run: ollama pull {settings.EMBEDDING_MODEL})"
            )
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Ollama embedding request failed with HTTP {exc.response.status_code}: "
                f"{exc.response.text}"
            )

    return results


class EmbeddingService:
    """
    Provider-agnostic embedding service.
    Swap provider via LLM_PROVIDER env var — no code changes needed.
    Currently supports: 'ollama'.
    Falls back to deterministic mock embeddings when OLLAMA_BASE_URL is unreachable
    (only in test/offline mode — tests use the mock path explicitly).
    """

    def __init__(self, model: str = None):
        self.model = model or settings.EMBEDDING_MODEL
        self.provider = settings.LLM_PROVIDER

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self.provider == "ollama":
            return _call_ollama_embeddings(texts)
        raise ValueError(f"Unsupported embedding provider: '{self.provider}'")

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

    @staticmethod
    def mock_embedding(text: str, dim: int = OLLAMA_EMBED_DIM) -> List[float]:
        """
        Deterministic pseudo-embedding for unit tests and offline usage.
        Not used in production — only called explicitly in test fixtures.
        """
        hash_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        seed = int(hash_digest[:8], 16)
        return [((seed + i * 37) % 1000) / 1000.0 - 0.5 for i in range(dim)]
