"""Service for storing high-quality Q&A pairs in the vector database."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.embeddings import get_embedding_client
from app.core.logging import get_logger
from app.db.models import Document, DocumentChunk
from app.vectorstore.pgvector_store import PGVectorStore

logger = get_logger(__name__)


async def store_qa_if_high_quality(
    *,
    session: AsyncSession,
    question: str,
    answer: str,
    quality_score: float,
    min_quality_threshold: float = 85.0,
    source_type: str = "qa_pair",
) -> bool:
    """
    Store a high-quality Q&A pair in the vector database for self-improving RAG.
    
    This function enables the system to learn from successful interactions by
    storing high-quality Q&A pairs as searchable documents in the knowledge base.
    
    Args:
        session: Database session
        question: User's question
        answer: System's generated answer
        quality_score: Quality evaluation score (0-100)
        min_quality_threshold: Minimum score required to store (default: 85.0)
        source_type: Type identifier for stored documents (default: "qa_pair")
    
    Returns:
        True if Q&A pair was stored, False if quality too low or error occurred
    """
    try:
        # Check quality threshold
        if quality_score < min_quality_threshold:
            logger.info(
                "qa_storage.quality_too_low",
                quality_score=quality_score,
                threshold=min_quality_threshold,
            )
            return False
        
        logger.info(
            "qa_storage.storing",
            question=question[:50],
            quality_score=quality_score,
            answer_length=len(answer),
        )
        
        # Format Q&A pair as a document
        qa_content = f"""Question: {question}

Answer:
{answer}

---
Source: Generated Q&A pair (Quality Score: {quality_score:.1f}/100)
"""
        
        # Create document metadata
        metadata = {
            "source_type": source_type,
            "quality_score": quality_score,
            "question": question,
            "answer_length": len(answer),
        }
        
        # Generate embedding for the Q&A pair
        embedding_client = get_embedding_client()
        embeddings = await embedding_client.embed_documents([qa_content])
        
        if not embeddings or len(embeddings) == 0:
            logger.error("qa_storage.embedding_failed", question=question[:50])
            return False
        
        qa_embedding = embeddings[0]
        
        # Create document in database
        document = Document(
            title=f"Q&A: {question[:100]}",
            url=None,  # Generated content, no URL
            content=qa_content,
            metadata=metadata,
        )
        session.add(document)
        await session.flush()  # Get document ID
        
        # Create chunk with embedding
        chunk = DocumentChunk(
            document_id=document.id,
            content=qa_content,
            chunk_index=0,  # Single chunk for Q&A pairs
            embedding=qa_embedding,
            metadata=metadata,
        )
        session.add(chunk)
        await session.commit()
        
        logger.info(
            "qa_storage.success",
            document_id=document.id,
            chunk_id=chunk.id,
            quality_score=quality_score,
        )
        
        return True
        
    except Exception as e:
        logger.error("qa_storage.error", error=str(e), exc_info=True)
        await session.rollback()
        return False


async def store_chat_qa_pair(
    *,
    session: AsyncSession,
    question: str,
    answer: str,
    teaching_mode: str,
    sources_used: int,
) -> bool:
    """
    Store a chat Q&A pair in the vector database (no quality filter).
    
    Chat mode Q&A pairs are stored without quality evaluation since they're
    fast, conversational responses. This helps build a knowledge base of
    common questions and teaching-mode-specific answers.
    
    Args:
        session: Database session
        question: User's question
        answer: System's generated answer
        teaching_mode: Teaching mode used (coach, hybrid, socratic)
        sources_used: Number of sources used in generation
    
    Returns:
        True if Q&A pair was stored, False if error occurred
    """
    try:
        logger.info(
            "chat_qa_storage.storing",
            question=question[:50],
            teaching_mode=teaching_mode,
            sources_used=sources_used,
        )
        
        # Format chat Q&A pair as a document
        qa_content = f"""Question: {question}

Answer ({teaching_mode.title()} Mode):
{answer}

---
Source: Chat Q&A pair (Teaching Mode: {teaching_mode}, Sources: {sources_used})
"""
        
        # Create document metadata
        metadata = {
            "source_type": "chat_qa_pair",
            "teaching_mode": teaching_mode,
            "sources_used": sources_used,
            "question": question,
            "answer_length": len(answer),
        }
        
        # Generate embedding for the Q&A pair
        embedding_client = get_embedding_client()
        embeddings = await embedding_client.embed_documents([qa_content])
        
        if not embeddings or len(embeddings) == 0:
            logger.error("chat_qa_storage.embedding_failed", question=question[:50])
            return False
        
        qa_embedding = embeddings[0]
        
        # Create document in database
        document = Document(
            title=f"Chat Q&A ({teaching_mode}): {question[:80]}",
            url=None,  # Generated content, no URL
            content=qa_content,
            metadata=metadata,
        )
        session.add(document)
        await session.flush()  # Get document ID
        
        # Create chunk with embedding
        chunk = DocumentChunk(
            document_id=document.id,
            content=qa_content,
            chunk_index=0,  # Single chunk for Q&A pairs
            embedding=qa_embedding,
            metadata=metadata,
        )
        session.add(chunk)
        await session.commit()
        
        logger.info(
            "chat_qa_storage.success",
            document_id=document.id,
            chunk_id=chunk.id,
            teaching_mode=teaching_mode,
        )
        
        return True
        
    except Exception as e:
        logger.error("chat_qa_storage.error", error=str(e), exc_info=True)
        await session.rollback()
        return False
