"""FastAPI Application factory and configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="RAGA: Advanced RAG Agent API",
        description=(
            "Advanced RAG Agent with Context Compression & Semantic Memory. "
            "Features hybrid dense-sparse search, parent-document retrieval mapping, "
            "Cohere ReRank context compression, and Mem0/Zep persistent semantic memory."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API Router
    app.include_router(api_router)

    @app.get("/", tags=["Health"])
    async def root():
        """Root status endpoint."""
        return {
            "name": "RAGA API",
            "status": "operational",
            "version": "1.0.0",
            "endpoints": [
                "POST /api/chat",
                "GET /api/users/{user_id}/memories",
                "POST /api/ingest",
                "GET /docs",
            ],
        }

    @app.get("/health", tags=["Health"])
    async def health_check():
        """Service health check."""
        return {"status": "healthy"}

    return app


app = create_app()
