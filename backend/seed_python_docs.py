#!/usr/bin/env python3
"""
Seed PostgreSQL database with Python official documentation.

This script downloads Python 3.11 documentation, processes it into chunks,
generates embeddings, and uploads to the Render PostgreSQL database.

Usage:
    export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
    export OPENAI_API_KEY="sk-..."
    poetry run python seed_python_docs.py
"""

import asyncio
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# Fix Windows async event loop policy for psycopg
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.clients.embeddings import OpenAIEmbeddingClient
from app.core.config import get_settings
from app.db.models import Document, DocumentChunk
from app.ingestion.chunker import DocumentChunker, merge_chunks

# Python documentation URLs to seed
PYTHON_DOCS_URLS = [
    # Tutorial
    ("https://docs.python.org/3/tutorial/introduction.html", "Python Tutorial: Introduction"),
    ("https://docs.python.org/3/tutorial/controlflow.html", "Python Tutorial: Control Flow"),
    ("https://docs.python.org/3/tutorial/datastructures.html", "Python Tutorial: Data Structures"),
    ("https://docs.python.org/3/tutorial/modules.html", "Python Tutorial: Modules"),
    ("https://docs.python.org/3/tutorial/inputoutput.html", "Python Tutorial: Input/Output"),
    ("https://docs.python.org/3/tutorial/errors.html", "Python Tutorial: Errors and Exceptions"),
    ("https://docs.python.org/3/tutorial/classes.html", "Python Tutorial: Classes"),
    ("https://docs.python.org/3/tutorial/stdlib.html", "Python Tutorial: Standard Library"),
    
    # Language Reference
    ("https://docs.python.org/3/reference/lexical_analysis.html", "Python Reference: Lexical Analysis"),
    ("https://docs.python.org/3/reference/datamodel.html", "Python Reference: Data Model"),
    ("https://docs.python.org/3/reference/executionmodel.html", "Python Reference: Execution Model"),
    ("https://docs.python.org/3/reference/expressions.html", "Python Reference: Expressions"),
    ("https://docs.python.org/3/reference/simple_stmts.html", "Python Reference: Simple Statements"),
    ("https://docs.python.org/3/reference/compound_stmts.html", "Python Reference: Compound Statements"),
    
    # Library Reference (most important modules)
    ("https://docs.python.org/3/library/functions.html", "Python Library: Built-in Functions"),
    ("https://docs.python.org/3/library/stdtypes.html", "Python Library: Built-in Types"),
    ("https://docs.python.org/3/library/exceptions.html", "Python Library: Built-in Exceptions"),
    ("https://docs.python.org/3/library/string.html", "Python Library: String Services"),
    ("https://docs.python.org/3/library/re.html", "Python Library: Regular Expressions"),
    ("https://docs.python.org/3/library/datetime.html", "Python Library: Date and Time"),
    ("https://docs.python.org/3/library/collections.html", "Python Library: Collections"),
    ("https://docs.python.org/3/library/itertools.html", "Python Library: Itertools"),
    ("https://docs.python.org/3/library/functools.html", "Python Library: Functools"),
    ("https://docs.python.org/3/library/pathlib.html", "Python Library: Path Operations"),
    ("https://docs.python.org/3/library/os.html", "Python Library: OS Interface"),
    ("https://docs.python.org/3/library/sys.html", "Python Library: System Parameters"),
    ("https://docs.python.org/3/library/json.html", "Python Library: JSON"),
    ("https://docs.python.org/3/library/csv.html", "Python Library: CSV Files"),
    ("https://docs.python.org/3/library/sqlite3.html", "Python Library: SQLite Database"),
    ("https://docs.python.org/3/library/asyncio.html", "Python Library: Asyncio"),
    ("https://docs.python.org/3/library/threading.html", "Python Library: Threading"),
    ("https://docs.python.org/3/library/multiprocessing.html", "Python Library: Multiprocessing"),
    ("https://docs.python.org/3/library/unittest.html", "Python Library: Unit Testing"),
    ("https://docs.python.org/3/library/logging.html", "Python Library: Logging"),
    
    # HOWTOs
    ("https://docs.python.org/3/howto/regex.html", "Python HOWTO: Regular Expressions"),
    ("https://docs.python.org/3/howto/logging.html", "Python HOWTO: Logging"),
    ("https://docs.python.org/3/howto/functional.html", "Python HOWTO: Functional Programming"),
    ("https://docs.python.org/3/howto/sorting.html", "Python HOWTO: Sorting"),
    ("https://docs.python.org/3/howto/descriptor.html", "Python HOWTO: Descriptors"),
    ("https://docs.python.org/3/howto/argparse.html", "Python HOWTO: Argparse"),
]


class PythonDocsSeedingService:
    """Service to download and seed Python documentation."""
    
    def __init__(self, database_url: str, openai_api_key: str):
        self.database_url = database_url
        self.openai_api_key = openai_api_key
        
        # Initialize components
        settings = get_settings()
        self.embedding_client = OpenAIEmbeddingClient(
            model=settings.openai_embedding_model,
            api_key=openai_api_key,
            _dimension=settings.openai_embedding_dimensions,
        )
        self.chunker = DocumentChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self.embedding_model = settings.openai_embedding_model
        
        # Create async engine
        self.engine = create_async_engine(
            database_url.replace("postgresql://", "postgresql+psycopg://"),
            echo=False,
        )
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def download_page(self, url: str) -> str:
        """Download HTML page and extract text content."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Parse HTML and extract text
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Get text from main content area
            main_content = soup.find('div', class_='body') or soup.find('main') or soup.body
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
            else:
                text = soup.get_text(separator='\n', strip=True)
            
            # Clean up excessive whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines)
    
    async def process_document(
        self,
        session: AsyncSession,
        url: str,
        title: str,
    ) -> tuple[uuid.UUID, int]:
        """Process a single document: download, chunk, embed, and store."""
        
        # Download content
        print(f"  📥 Downloading: {title}")
        try:
            content = await self.download_page(url)
        except Exception as e:
            print(f"  ❌ Failed to download {title}: {e}")
            return None, 0
        
        if len(content) < 100:
            print(f"  ⚠️  Skipping {title}: content too short")
            return None, 0
        
        # Chunk the content
        print(f"  ✂️  Chunking...")
        chunks = self.chunker.split_text(content)
        
        if not chunks:
            print(f"  ⚠️  Skipping {title}: no chunks generated")
            return None, 0
        
        # Generate embeddings
        print(f"  🧮 Generating embeddings for {len(chunks)} chunks...")
        try:
            embeddings = await self.embedding_client.embed_documents(merge_chunks(chunks))
        except Exception as e:
            print(f"  ❌ Failed to generate embeddings for {title}: {e}")
            return None, 0
        
        if len(embeddings) != len(chunks):
            print(f"  ❌ Embedding count mismatch for {title}")
            return None, 0
        
        # Create document
        document = Document(
            title=title,
            description=f"Python 3.11 official documentation: {title}",
            source_type="web",
            source_uri=url,
            doc_metadata={
                "source": "python.org",
                "version": "3.11",
                "seeded_at": datetime.utcnow().isoformat(),
            },
        )
        session.add(document)
        await session.flush()
        
        # Create chunks
        chunk_objects = [
            DocumentChunk(
                document_id=document.id,
                chunk_index=chunk.index,
                content=chunk.content,
                content_tokens=chunk.token_count,
                embedding=list(embedding),
                embedding_model=self.embedding_model,
                chunk_metadata={
                    "source_type": "web",
                    "title": title,
                    "chunk_index": chunk.index,
                    "url": url,
                },
            )
            for chunk, embedding in zip(chunks, embeddings, strict=True)
        ]
        
        session.add_all(chunk_objects)
        await session.flush()
        
        print(f"  ✅ Stored: {len(chunk_objects)} chunks")
        return document.id, len(chunk_objects)
    
    async def seed_database(self) -> dict[str, Any]:
        """Seed the database with Python documentation."""
        start_time = time.time()
        
        print("\n" + "="*60)
        print("🌱 SEEDING PYTHON DOCUMENTATION")
        print("="*60 + "\n")
        
        total_docs = 0
        total_chunks = 0
        failed_docs = 0
        
        async with self.async_session() as session:
            for idx, (url, title) in enumerate(PYTHON_DOCS_URLS, 1):
                print(f"\n[{idx}/{len(PYTHON_DOCS_URLS)}] Processing: {title}")
                
                try:
                    doc_id, chunk_count = await self.process_document(session, url, title)
                    
                    if doc_id:
                        total_docs += 1
                        total_chunks += chunk_count
                        
                        # Commit every 5 documents
                        if total_docs % 5 == 0:
                            await session.commit()
                            print(f"\n  💾 Committed batch (total: {total_docs} docs, {total_chunks} chunks)")
                    else:
                        failed_docs += 1
                    
                    # Rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"  ❌ Error processing {title}: {e}")
                    failed_docs += 1
                    await session.rollback()
                    continue
            
            # Final commit
            await session.commit()
        
        elapsed = time.time() - start_time
        
        # Print summary
        print("\n" + "="*60)
        print("✅ SEEDING COMPLETE")
        print("="*60)
        print(f"📊 Documents uploaded: {total_docs}")
        print(f"📦 Total chunks created: {total_chunks}")
        print(f"❌ Failed documents: {failed_docs}")
        print(f"⏱️  Time elapsed: {elapsed:.1f}s")
        if total_docs > 0:
            print(f"📈 Average: {elapsed/total_docs:.1f}s per document")
        print("="*60 + "\n")
        
        return {
            "documents_uploaded": total_docs,
            "chunks_created": total_chunks,
            "failed_documents": failed_docs,
            "time_elapsed": elapsed,
        }
    
    async def verify_seeding(self) -> None:
        """Verify the seeding was successful."""
        print("\n🔍 VERIFYING DATABASE...")
        
        async with self.async_session() as session:
            # Count documents
            result = await session.execute(text("SELECT COUNT(*) FROM documents"))
            doc_count = result.scalar()
            
            # Count chunks
            result = await session.execute(text("SELECT COUNT(*) FROM document_chunks"))
            chunk_count = result.scalar()
            
            # Sample a document
            result = await session.execute(
                text("SELECT title, source_uri FROM documents LIMIT 1")
            )
            sample = result.fetchone()
            
            print(f"✅ Documents in database: {doc_count}")
            print(f"✅ Chunks in database: {chunk_count}")
            if sample:
                print(f"✅ Sample document: {sample[0]}")
                print(f"   URL: {sample[1]}")
            print()
    
    async def close(self):
        """Close database connections."""
        await self.engine.dispose()


async def main():
    """Main entry point."""
    # Check environment variables
    database_url = os.getenv("DATABASE_URL")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("\nGet your DATABASE_URL from Render:")
        print("  1. Go to https://dashboard.render.com")
        print("  2. Click on 'curriculum-studio-db'")
        print("  3. Copy the 'Internal Database URL'")
        print("\nThen run:")
        print('  export DATABASE_URL="postgresql://..."')
        sys.exit(1)
    
    if not openai_api_key:
        print("❌ ERROR: OPENAI_API_KEY environment variable not set")
        print("\nSet your OpenAI API key:")
        print('  export OPENAI_API_KEY="sk-..."')
        sys.exit(1)
    
    print("\n🚀 Starting Python Documentation Seeding...")
    print(f"📍 Database: {database_url.split('@')[1] if '@' in database_url else 'local'}")
    print(f"🔑 OpenAI API Key: {openai_api_key[:10]}...{openai_api_key[-4:]}")
    
    # Create service and seed
    service = PythonDocsSeedingService(database_url, openai_api_key)
    
    try:
        # Seed the database
        result = await service.seed_database()
        
        # Verify seeding
        await service.verify_seeding()
        
        print("🎉 SUCCESS! Your database is now seeded with Python documentation.")
        print("\n📝 Next steps:")
        print("  1. Test a query in your frontend")
        print("  2. Check Render logs for 'rag_docs > 0'")
        print("  3. Verify citations appear in generated answers")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())

