"""Vector store utilities backed by pgvector."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.db.models import Document, DocumentChunk


@dataclass(slots=True)
class RetrievalResult:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    score: float
    content: str
    chunk_index: int
    metadata: dict[str, Any]
    document_metadata: dict[str, Any]
    document_title: str
    source_type: str
    source_uri: str | None


class PGVectorStore:
    """Similarity search wrapper using pgvector operators."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def similarity_search(
        self,
        embedding: Sequence[float],
        *,
        limit: int = 5,
        max_distance: float | None = None,
        source_types: Iterable[str] | None = None,
    ) -> list[RetrievalResult]:
        document_alias = aliased(Document)
        query_vector = list(embedding)
        distance = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")

        stmt: Select[tuple[DocumentChunk, Document, float]] = (
            select(DocumentChunk, document_alias, distance)
            .join(document_alias, DocumentChunk.document_id == document_alias.id)
            .order_by(distance)
            .limit(limit)
        )

        if source_types:
            stmt = stmt.where(document_alias.source_type.in_(list(source_types)))

        results = await self._session.execute(stmt)

        retrievals: list[RetrievalResult] = []
        for chunk, document, distance_value in results.all():
            if max_distance is not None and distance_value > max_distance:
                continue

            retrievals.append(
                RetrievalResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    score=distance_value,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    metadata=chunk.chunk_metadata,
                    document_metadata=document.doc_metadata,
                    document_title=document.title,
                    source_type=document.source_type,
                    source_uri=document.source_uri,
                )
            )

        return retrievals

