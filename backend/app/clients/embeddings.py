"""Embedding client abstractions."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol, Sequence, runtime_checkable

from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@runtime_checkable
class EmbeddingClient(Protocol):
    """Protocol for embedding providers."""

    @property
    def dimension(self) -> int:
        """Return embedding vector dimension."""

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Return embeddings for given texts."""


@dataclass
class OpenAIEmbeddingClient:
    """LangChain OpenAI embeddings wrapper."""

    model: str
    api_key: str
    _dimension: int
    _client: OpenAIEmbeddings | None = None

    def __post_init__(self) -> None:
        self._client = OpenAIEmbeddings(model=self.model, api_key=self.api_key)

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        return await asyncio.to_thread(self._client.embed_documents, list(texts))


_embedding_client: EmbeddingClient | None = None


def get_embedding_client() -> EmbeddingClient:
    """Return singleton embedding client using configured provider."""

    global _embedding_client
    if _embedding_client is not None:
        return _embedding_client

    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for embeddings.")

    model = settings.openai_embedding_model
    dimension = settings.openai_embedding_dimensions
    logger.info("embedding_client.init", provider="openai", model=model)
    _embedding_client = OpenAIEmbeddingClient(
        model=model,
        api_key=settings.openai_api_key,
        _dimension=dimension,
    )
    return _embedding_client

