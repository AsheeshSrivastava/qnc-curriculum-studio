"""Test script for sequential pipeline (Agents 1-2-3)."""

import asyncio
import os
from datetime import datetime

import httpx


async def test_sequential_pipeline():
    """Test the new sequential pipeline with a simple query."""
    
    backend_url = "https://qnc-curriculum-studio.onrender.com"
    
    print("=" * 80)
    print("TESTING SEQUENTIAL PIPELINE (Agents 1-2-3)")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Backend URL: {backend_url}")
    print()
    
    # Test query
    question = "How do list comprehensions work?"
    print(f"Question: {question}")
    print()
    
    # Make API request
    async with httpx.AsyncClient(timeout=360.0) as client:
        try:
            print("Sending request to backend...")
            response = await client.post(
                f"{backend_url}/api/chat/query",
                json={
                    "question": question,
                    "history": [],
                },
            )
            response.raise_for_status()
            result = response.json()
            
            print("Response received!")
            print()
            
            # Display results
            print("=" * 80)
            print("RESULTS")
            print("=" * 80)
            
            answer = result.get("answer", "")
            citations = result.get("citations", [])
            
            print(f"Answer length: {len(answer)} characters")
            print(f"Citations: {len(citations)}")
            print()
            
            # Show first 500 characters of answer
            print("Answer preview:")
            print("-" * 80)
            print(answer[:500])
            if len(answer) > 500:
                print(f"\n... ({len(answer) - 500} more characters)")
            print("-" * 80)
            print()
            
            # Show citations
            if citations:
                print("Citations:")
                print("-" * 80)
                for i, citation in enumerate(citations[:5], 1):
                    print(f"{i}. [{citation.get('id')}] {citation.get('title', 'N/A')}")
                    print(f"   Source: {citation.get('source_type', 'N/A')}")
                if len(citations) > 5:
                    print(f"   ... and {len(citations) - 5} more")
                print("-" * 80)
                print()
            
            # Check for markdown structure
            headers = answer.count("##")
            code_blocks = answer.count("```python")
            paragraphs = answer.count("\n\n")
            
            print("QUALITY CHECKS:")
            print("-" * 80)
            print(f"Markdown headers (##): {headers} {'[PASS]' if headers >= 5 else '[FAIL]'}")
            print(f"Code blocks (```python): {code_blocks} {'[PASS]' if code_blocks >= 3 else '[FAIL]'}")
            print(f"Paragraphs (blank lines): {paragraphs} {'[PASS]' if paragraphs >= 8 else '[FAIL]'}")
            print(f"Citations: {len(citations)} {'[PASS]' if len(citations) >= 10 else '[FAIL]'}")
            print("-" * 80)
            print()
            
            # Overall assessment
            passed_checks = sum([
                headers >= 5,
                code_blocks >= 3,
                paragraphs >= 8,
                len(citations) >= 10,
            ])
            
            print("=" * 80)
            if passed_checks == 4:
                print("SUCCESS: ALL CHECKS PASSED! Sequential pipeline working perfectly!")
            elif passed_checks >= 3:
                print(f"PARTIAL: {passed_checks}/4 checks passed. Pipeline mostly working.")
            else:
                print(f"FAILED: Only {passed_checks}/4 checks passed. Pipeline needs adjustment.")
            print("=" * 80)
            
            print(f"Completed at: {datetime.now().strftime('%H:%M:%S')}")
            
        except httpx.HTTPStatusError as e:
            print(f"ERROR: HTTP {e.response.status_code}")
            print(f"Response: {e.response.text}")
        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(test_sequential_pipeline())

