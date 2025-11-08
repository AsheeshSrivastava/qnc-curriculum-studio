"""Custom uvicorn runner with Windows event loop fix."""

import asyncio
import sys

# CRITICAL: Set Windows event loop policy BEFORE uvicorn imports anything
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("[Windows] Set WindowsSelectorEventLoopPolicy for psycopg async compatibility")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,  # Disable reload to avoid event loop issues
        log_level="info",
    )



