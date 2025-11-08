"""Custom uvicorn runner with Windows event loop fix."""

import asyncio
import os
import sys

# CRITICAL: Set Windows event loop policy BEFORE uvicorn imports anything
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("[Windows] Set WindowsSelectorEventLoopPolicy for psycopg async compatibility")

if __name__ == "__main__":
    import uvicorn

    # Use environment variables for host and port (for Render deployment)
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,  # Disable reload to avoid event loop issues
        log_level="info",
    )



