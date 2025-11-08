"""Data access layer for documents and chunks."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from sqlalchemy import Select, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from app.db.models import Document, DocumentChunk


@dataclass(slots=True)
class DocumentCreate:
    title: str
    description: str | None
    source_type: str
    source_uri: str | None
    doc_metadata: dict[str, Any]


@dataclass(slots=True)
class ChunkCreate:
    chunk_index: int
    content: str
    content_tokens: int
    embedding: Sequence[float]
    embedding_model: str
    chunk_metadata: dict[str, Any]


class DocumentRepository:
    """Repository abstraction for document persistence."""

    async def create_document_with_chunks(
        self,
        session: AsyncSession,
        document_payload: DocumentCreate,
        chunk_payloads: Iterable[ChunkCreate],
    ) -> Document:
        document = Document(
            title=document_payload.title,
            description=document_payload.description,
            source_type=document_payload.source_type,
            source_uri=document_payload.source_uri,
            doc_metadata=document_payload.doc_metadata or {},
        )
        session.add(document)
        await session.flush()

        chunks = [
            DocumentChunk(
                document_id=document.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                content_tokens=chunk.content_tokens,
                embedding=list(chunk.embedding),
                embedding_model=chunk.embedding_model,
                chunk_metadata=chunk.chunk_metadata or {},
            )
            for chunk in chunk_payloads
        ]

        session.add_all(chunks)
        await session.flush()

        return document

    async def upsert_chunks(
        self,
        session: AsyncSession,
        document_id: uuid.UUID,
        chunk_payloads: Iterable[ChunkCreate],
    ) -> None:
        values = [
            {
                "document_id": document_id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "content_tokens": chunk.content_tokens,
                "embedding": list(chunk.embedding),
                "embedding_model": chunk.embedding_model,
                "chunk_metadata": chunk.chunk_metadata or {},
            }
            for chunk in chunk_payloads
        ]

        if not values:
            return

        insert_stmt = insert(DocumentChunk).values(values)
        update_columns = {
            "content": insert_stmt.excluded.content,
            "content_tokens": insert_stmt.excluded.content_tokens,
            "embedding": insert_stmt.excluded.embedding,
            "embedding_model": insert_stmt.excluded.embedding_model,
            "chunk_metadata": insert_stmt.excluded.chunk_metadata,
        }
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=["document_id", "chunk_index"],
            set_=update_columns,
        )
        await session.execute(upsert_stmt)

    async def get_document(self, session: AsyncSession, document_id: uuid.UUID) -> Document | None:
        stmt: Select[tuple[Document]] = select(Document).where(Document.id == document_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_documents(self, session: AsyncSession, limit: int = 50) -> list[Document]:
        stmt = select(Document).order_by(Document.created_at.desc()).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars())

    async def delete_document(self, session: AsyncSession, document_id: uuid.UUID) -> None:
        await session.execute(
            delete(Document).where(Document.id == document_id),
        )

    async def get_document_with_chunks(
        self,
        session: AsyncSession,
        document_id: uuid.UUID,
    ) -> Document | None:
        stmt = (
            select(Document)
            .outerjoin(Document.chunks)
            .options(contains_eager(Document.chunks))
            .where(Document.id == document_id)
        )
        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()


document_repository = DocumentRepository()

