"""Root entrypoint for running RAGA server via Uvicorn.

Usage:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from app.main import app
from app.core.config import get_settings

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )

