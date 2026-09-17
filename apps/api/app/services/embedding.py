import time
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.services.demo import embed_text


class EmbeddingNotConfigured(RuntimeError):
    pass


@dataclass
class EmbeddingResult:
    vectors: list[list[float]]
    input_tokens: int
    latency_ms: int


class OpenAICompatibleEmbeddingClient:
    def __init__(self) -> None:
        self.base_url = settings.embedding_base_url.rstrip("/")
        self.api_key = settings.embedding_api_key
        self.model = settings.embedding_model

    async def embed(self, texts: list[str]) -> EmbeddingResult:
        if not self.api_key:
            raise EmbeddingNotConfigured("EMBEDDING_API_KEY is not configured.")

        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "input": texts},
            )
            response.raise_for_status()
            payload = response.json()

        vectors = [
            item["embedding"]
            for item in sorted(payload["data"], key=lambda item: item["index"])
        ]
        usage = payload.get("usage", {})
        return EmbeddingResult(
            vectors=vectors,
            input_tokens=int(usage.get("prompt_tokens", 0)),
            latency_ms=int((time.perf_counter() - started) * 1000),
        )


class DeterministicEmbeddingClient:
    async def embed(self, texts: list[str]) -> EmbeddingResult:
        started = time.perf_counter()
        vectors = [embed_text(text, settings.embedding_dimension) for text in texts]
        return EmbeddingResult(
            vectors=vectors,
            input_tokens=sum(max(1, len(text) // 2) for text in texts),
            latency_ms=int((time.perf_counter() - started) * 1000),
        )


def get_embedding_client() -> OpenAICompatibleEmbeddingClient | DeterministicEmbeddingClient:
    if settings.demo_mode:
        return DeterministicEmbeddingClient()
    return OpenAICompatibleEmbeddingClient()
