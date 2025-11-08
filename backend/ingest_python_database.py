"""Bulk ingest all Python learning materials from 'Python database' folder."""

import asyncio
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import Database
from app.ingestion.parsers import DocumentParser, ParsedDocument
from app.ingestion.service import DocumentIngestionService
from app.ingestion.filters import PythonRelevanceFilter

logger = get_logger(__name__)

# Fix for Windows async psycopg compatibility
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def ingest_python_materials():
    """Ingest all Python learning materials from the database folder."""
    
    # Path to Python database folder
    python_db_path = Path(__file__).parent.parent / "Python database"
    
    if not python_db_path.exists():
        logger.error("python_database.not_found", path=str(python_db_path))
        print(f"ERROR: Python database folder not found at {python_db_path}")
        return
    
    # Get all markdown and PDF files
    md_files = list(python_db_path.glob("*.md"))
    pdf_files = list(python_db_path.glob("*.pdf"))
    
    all_files = md_files + pdf_files
    
    print("=" * 80)
    print("BULK INGESTION: Python Learning Materials")
    print("=" * 80)
    print(f"\nFound {len(all_files)} files:")
    print(f"  - Markdown files: {len(md_files)}")
    print(f"  - PDF files: {len(pdf_files)}")
    print()
    
    # Initialize database
    db = Database()
    db.configure()
    
    # Initialize services
    settings = get_settings()
    parser = DocumentParser()
    topic_filter = PythonRelevanceFilter()
    ingestion_service = DocumentIngestionService(
        embedding_model=settings.openai_embedding_model,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    
    # Track results
    successful = 0
    failed = 0
    skipped = 0
    
    async with db.async_session() as session:
        for idx, file_path in enumerate(all_files, 1):
            file_name = file_path.name
            
            # Skip non-Python content files
            skip_patterns = [
                "Content Log",
                "My Energies",
                "My Weekly Planning",
                "How I Take Notes",
                "How to Create Monthly",
                "How to create my workflow",
                "Jupyter Setup for Obsidian",
                "curriculum_context.json",
                ".ts",
                ".py",
            ]
            
            if any(pattern in file_name for pattern in skip_patterns):
                print(f"[{idx}/{len(all_files)}] SKIP: {file_name} (non-Python content)")
                skipped += 1
                continue
            
            print(f"\n[{idx}/{len(all_files)}] Processing: {file_name}")
            print("-" * 80)
            
            try:
                # Read file
                with open(file_path, "rb") as f:
                    raw_bytes = f.read()
                
                # Parse based on extension
                extension = file_path.suffix.lower()
                if extension == ".pdf":
                    text = parser._parse_pdf(raw_bytes)
                    source_type = "pdf"
                elif extension == ".md":
                    text = parser._parse_markdown(raw_bytes)
                    source_type = "markdown"
                else:
                    text = raw_bytes.decode("utf-8", errors="ignore")
                    source_type = "text"
                
                # Normalize whitespace
                clean_text = parser._normalize_whitespace(text)
                
                # Apply Python topic filter
                passes_filter, reason = topic_filter.passes(clean_text)
                
                if not passes_filter:
                    print(f"  ⚠️  FILTERED OUT: {reason}")
                    skipped += 1
                    continue
                
                # Create ParsedDocument
                parsed = ParsedDocument(
                    title=file_name,
                    content=clean_text,
                    source_type=source_type,
                    metadata={"original_filename": file_name},
                    passes_filter=True,
                    filter_reason=None,
                )
                
                # Ingest
                result = await ingestion_service.ingest(
                    session=session,
                    parsed=parsed,
                    description=f"Python learning material: {file_name}",
                    source_uri=f"file://Python database/{file_name}",
                )
                
                print(f"  ✅ SUCCESS")
                print(f"     Document ID: {result.document_id}")
                print(f"     Chunks: {result.chunk_count}")
                print(f"     Tokens: {result.total_tokens}")
                
                successful += 1
                
            except Exception as e:
                print(f"  ❌ FAILED: {str(e)}")
                logger.error("ingestion.failed", file=file_name, error=str(e), exc_info=True)
                failed += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("INGESTION COMPLETE")
    print("=" * 80)
    print(f"\nTotal files: {len(all_files)}")
    print(f"  ✅ Successful: {successful}")
    print(f"  ❌ Failed: {failed}")
    print(f"  ⚠️  Skipped: {skipped}")
    print()
    
    if successful > 0:
        print("🎉 Your Python knowledge base is now ready!")
        print("   The system will use RAG to retrieve from these materials first.")
        print("   LLM calls will only happen if RAG doesn't find relevant content.")
    
    print()


if __name__ == "__main__":
    asyncio.run(ingest_python_materials())

