"""Bulk ingest Python materials using the upload API endpoint."""

import asyncio
import io
import os
import re
import sys
import unicodedata
from pathlib import Path

import httpx

# Fix for Windows async compatibility
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Fix for Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def sanitize_filename(name: str) -> str:
    """Return an ASCII-safe version of a filename for upload/display."""
    normalized = unicodedata.normalize("NFKD", name)
    ascii_only = normalized.encode("ascii", "ignore").decode()
    ascii_only = re.sub(r"[^A-Za-z0-9._ -]+", "_", ascii_only)
    ascii_only = re.sub(r"_+", "_", ascii_only).strip("_")
    return ascii_only or "document"


async def ingest_via_api():
    """Ingest all Python materials using the upload API."""
    
    # Path to Python database folder
    python_db_path = Path(__file__).parent.parent / "Python database"
    
    if not python_db_path.exists():
        print(f"ERROR: Python database folder not found at {python_db_path}")
        return
    
    # Get all markdown and PDF files
    md_files = list(python_db_path.glob("*.md"))
    include_pdfs = os.getenv("INGEST_INCLUDE_PDFS", "0") == "1"
    pdf_files = list(python_db_path.glob("*.pdf")) if include_pdfs else []
    
    all_files = md_files + pdf_files
    
    print("=" * 80)
    print("BULK INGESTION: Python Learning Materials")
    print("=" * 80)
    print(f"\nFound {len(all_files)} files:")
    print(f"  - Markdown files: {len(md_files)}")
    print(f"  - PDF files: {len(pdf_files)}")
    print()
    
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
        "Test.py",
        "testing 2-1.py",
    ]
    
    # Track results
    successful = 0
    failed = 0
    skipped = 0
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for idx, file_path in enumerate(all_files, 1):
            original_name = file_path.name
            safe_name = sanitize_filename(original_name)
            
            # Skip non-Python content
            if any(pattern in original_name for pattern in skip_patterns):
                print(f"[{idx}/{len(all_files)}] SKIP: {safe_name} (original: {original_name})")
                skipped += 1
                continue
            
            print(f"\n[{idx}/{len(all_files)}] Processing: {safe_name}")
            if safe_name != original_name:
                print(f"  Original name: {original_name}")
            print("-" * 80)
            
            try:
                # Read file
                with open(file_path, "rb") as f:
                    file_content = f.read()
                
                # Determine content type
                extension = file_path.suffix.lower()
                if extension == ".pdf":
                    content_type = "application/pdf"
                elif extension == ".md":
                    content_type = "text/markdown"
                else:
                    content_type = "text/plain"
                
                # Prepare multipart upload
                files = {
                    "file": (safe_name, file_content, content_type)
                }
                
                data = {
                    "description": f"Python learning material: {original_name}"
                }
                
                # Upload via API
                response = await client.post(
                    "http://127.0.0.1:8000/api/documents",
                    files=files,
                    data=data,
                )
                
                if response.status_code in (200, 201):
                    result = response.json()
                    print(f"  [OK] SUCCESS")
                    print(f"     Document ID: {result.get('document_id')}")
                    print(f"     Chunks: {result.get('chunk_count')}")
                    print(f"     Tokens: {result.get('total_tokens')}")
                    successful += 1
                elif response.status_code == 400:
                    # Filtered out by Python relevance filter
                    error_detail = response.json().get("detail", "")
                    if "does not pass relevance filter" in error_detail:
                        print(f"  [SKIP] FILTERED OUT: Not Python-related content")
                        skipped += 1
                    else:
                        print(f"  [FAIL] ERROR: {error_detail}")
                        failed += 1
                else:
                    print(f"  [FAIL] HTTP {response.status_code}")
                    print(f"     {response.text[:200]}")
                    failed += 1
                    
            except Exception as e:
                print(f"  [FAIL] ERROR: {str(e)}")
                failed += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("INGESTION COMPLETE")
    print("=" * 80)
    print(f"\nTotal files: {len(all_files)}")
    print(f"  [OK] Successful: {successful}")
    print(f"  [FAIL] Failed: {failed}")
    print(f"  [SKIP] Skipped: {skipped}")
    print()
    
    if successful > 0:
        print("SUCCESS! Your Python knowledge base is now ready!")
        print("The system will use RAG to retrieve from these materials first.")
        print("LLM calls will only happen if RAG doesn't find relevant content.")
    
    print()


if __name__ == "__main__":
    asyncio.run(ingest_via_api())

