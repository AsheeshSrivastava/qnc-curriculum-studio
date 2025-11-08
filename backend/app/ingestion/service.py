"""Document ingestion orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.embeddings import EmbeddingClient, get_embedding_client
from app.core.config import get_settings
from app.core.logging import get_logger
from app.ingestion.chunker import DocumentChunker, TextChunk, merge_chunks
from app.ingestion.filters import PythonRelevanceFilter
from app.ingestion.parsers import ParsedDocument
from app.services.repositories import ChunkCreate, DocumentCreate, document_repository

logger = get_logger(__name__)


@dataclass(slots=True)
class IngestionResult:
    document_id: str
    chunk_count: int


class DocumentIngestionService:
    """Coordinate parsing, chunking, embeddings, and persistence."""

    def __init__(
        self,
        *,
        embedding_client: EmbeddingClient | None = None,
        chunker: DocumentChunker | None = None,
        relevance_filter: PythonRelevanceFilter | None = None,
    ) -> None:
        settings = get_settings()
        self.embedding_client = embedding_client or get_embedding_client()
        self.chunker = chunker or DocumentChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self.relevance_filter = relevance_filter or PythonRelevanceFilter()
        self.embedding_model = settings.openai_embedding_model
        self.expected_dimension = settings.openai_embedding_dimensions

        if self.embedding_client.dimension != self.expected_dimension:
            raise RuntimeError(
                f"Embedding dimension mismatch: expected {self.expected_dimension}, "
                f"got {self.embedding_client.dimension}"
            )

    async def ingest(
        self,
        session: AsyncSession,
        parsed: ParsedDocument,
        *,
        description: str | None,
        source_uri: str | None,
    ) -> IngestionResult:
        logger.info("ingestion.start", title=parsed.title, source_type=parsed.source_type)

        chunks = self.chunker.split_text(parsed.text)
        relevant = self.relevance_filter.filter_relevant(chunks)
        if not relevant:
            raise ValueError("Uploaded document does not appear to contain Python-related content.")

        embeddings = await self.embedding_client.embed_documents(merge_chunks(relevant))
        if len(embeddings) != len(relevant):
            raise RuntimeError("Embedding count mismatch during ingestion.")

        chunk_payloads = list(self._build_chunk_payloads(relevant, embeddings, parsed))
        document_payload = DocumentCreate(
            title=parsed.title,
            description=description,
            source_type=parsed.source_type,
            source_uri=source_uri,
            doc_metadata=parsed.metadata,
        )

        document = await document_repository.create_document_with_chunks(
            session,
            document_payload,
            chunk_payloads,
        )

        logger.info("ingestion.complete", document_id=str(document.id), chunks=len(chunk_payloads))
        return IngestionResult(document_id=str(document.id), chunk_count=len(chunk_payloads))

    def _build_chunk_payloads(
        self,
        chunks: Sequence[TextChunk],
        embeddings: Sequence[Sequence[float]],
        parsed: ParsedDocument,
    ) -> Iterable[ChunkCreate]:
        metadata_base = {
            "source_type": parsed.source_type,
            "title": parsed.title,
        }
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            yield ChunkCreate(
                chunk_index=chunk.index,
                content=chunk.content,
                content_tokens=chunk.token_count,
                embedding=embedding,
                embedding_model=self.embedding_model,
                chunk_metadata={**metadata_base, "chunk_index": chunk.index},
            )


def get_ingestion_service() -> DocumentIngestionService:
    return DocumentIngestionService()

