"""Self-improving RAG: Store high-quality Q&A pairs in vector database."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.documents import ParsedDocument
from app.services.ingestion import DocumentIngestionService
from app.vectorstore.pgvector_store import PGVectorStore
from app.clients.embeddings import get_embedding_client

logger = get_logger(__name__)


class QAStorageService:
    """Service for storing high-quality Q&A pairs in the vector database."""

    def __init__(self, session: AsyncSession):
        """Initialize QA storage service."""
        self.session = session
        self.settings = get_settings()
        self.embedding_client = get_embedding_client()
        self.vector_store = PGVectorStore(
            session=session,
            embedding_client=self.embedding_client,
        )
        self.ingestion_service = DocumentIngestionService(
            session=session,
            embedding_client=self.embedding_client,
        )

    async def should_store_qa(
        self,
        question: str,
        quality_score: float,
    ) -> bool:
        """
        Determine if a Q&A pair should be stored.

        Args:
            question: The question asked
            quality_score: Quality score of the generated answer

        Returns:
            True if Q&A should be stored, False otherwise
        """
        # Check if feature is enabled
        if not self.settings.enable_qa_storage:
            logger.debug("qa_storage.disabled")
            return False

        # Check quality threshold
        if quality_score < self.settings.qa_storage_min_quality:
            logger.debug(
                "qa_storage.quality_too_low",
                score=quality_score,
                threshold=self.settings.qa_storage_min_quality,
            )
            return False

        # Check for duplicates (semantic similarity)
        try:
            similar_docs = await self.vector_store.similarity_search(
                query=question,
                limit=1,
                max_distance=0.1,  # Very strict - only near-duplicates
            )

            if similar_docs:
                # Check if it's a Q&A document
                doc = similar_docs[0]
                if doc.get("source_type") == "qa_pair":
                    existing_score = doc.get("metadata", {}).get("quality_score", 0)

                    # Only store if new answer is significantly better
                    if quality_score <= existing_score + 5.0:
                        logger.info(
                            "qa_storage.duplicate_found",
                            question=question[:50],
                            existing_score=existing_score,
                            new_score=quality_score,
                        )
                        return False

        except Exception as e:
            logger.warning("qa_storage.duplicate_check_failed", error=str(e))
            # Continue with storage if duplicate check fails

        return True

    async def store_qa_pair(
        self,
        question: str,
        answer: str,
        quality_score: float,
        mode: str,
        citations: list[dict[str, Any]] | None = None,
    ) -> bool:
        """
        Store a high-quality Q&A pair in the vector database.

        Args:
            question: The question asked
            answer: The generated answer
            quality_score: Quality score of the answer
            mode: Mode used ("chat" or "generate")
            citations: Optional list of citations

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Check if should store
            if not await self.should_store_qa(question, quality_score):
                return False

            # Create document content
            content_parts = [
                f"# Question\n\n{question}",
                f"\n\n# Answer\n\n{answer}",
            ]

            # Add citations if available
            if citations:
                content_parts.append("\n\n# Sources")
                for i, citation in enumerate(citations, 1):
                    source = citation.get("source", "Unknown")
                    citation_type = citation.get("type", "N/A")
                    content_parts.append(f"\n- [{i}] {source} ({citation_type})")

            content = "".join(content_parts)

            # Create parsed document
            doc = ParsedDocument(
                title=f"Q&A: {question[:100]}",
                content=content,
                source_type="qa_pair",
                source_url=f"generated_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                metadata={
                    "quality_score": quality_score,
                    "mode": mode,
                    "timestamp": datetime.now().isoformat(),
                    "question": question,
                    "citation_count": len(citations) if citations else 0,
                },
            )

            # Ingest into vector database
            await self.ingestion_service.ingest(doc)

            logger.info(
                "qa_storage.stored",
                question=question[:50],
                score=quality_score,
                mode=mode,
                answer_length=len(answer),
            )

            return True

        except Exception as e:
            logger.error(
                "qa_storage.store_failed",
                question=question[:50],
                error=str(e),
                exc_info=True,
            )
            return False

    async def get_stored_qa_count(self) -> int:
        """
        Get the count of stored Q&A pairs.

        Returns:
            Number of Q&A pairs in the database
        """
        try:
            # Query for documents with source_type = "qa_pair"
            from sqlalchemy import select, func
            from app.db.models import Document

            stmt = select(func.count(Document.id)).where(
                Document.source_type == "qa_pair"
            )
            result = await self.session.execute(stmt)
            count = result.scalar_one()

            return count or 0

        except Exception as e:
            logger.error("qa_storage.count_failed", error=str(e))
            return 0


async def store_qa_if_high_quality(
    session: AsyncSession,
    question: str,
    answer: str,
    quality_score: float,
    mode: str,
    citations: list[dict[str, Any]] | None = None,
) -> bool:
    """
    Convenience function to store Q&A pair if it meets quality threshold.

    Args:
        session: Database session
        question: The question asked
        answer: The generated answer
        quality_score: Quality score of the answer
        mode: Mode used ("chat" or "generate")
        citations: Optional list of citations

    Returns:
        True if stored successfully, False otherwise
    """
    service = QAStorageService(session)
    return await service.store_qa_pair(
        question=question,
        answer=answer,
        quality_score=quality_score,
        mode=mode,
        citations=citations,
    )

