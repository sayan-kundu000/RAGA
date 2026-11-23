"""FastAPI Application factory and configuration."""

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router
from app.core.config import get_settings

STATIC_DASHBOARD_PATH = Path(__file__).parent / "static" / "dashboard.html"


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

    @app.get("/docs/pdf", response_class=FileResponse, tags=["Dashboard & Documentation"])
    async def download_docs_pdf():
        """Download or view the compiled RAGA Documentation PDF."""
        pdf_path = Path(__file__).parent.parent / "docs" / "RAGA_Complete_37_Topics_Manual.pdf"
        if not pdf_path.exists():
            pdf_path = Path(__file__).parent.parent / "docs" / "README.pdf"
        if pdf_path.exists():
            return FileResponse(pdf_path, media_type="application/pdf", filename="RAGA_Documentation.pdf")
        return HTMLResponse("<h2>Documentation PDF not found. Run python convert_docs_to_pdf.py</h2>", status_code=404)

    @app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
    async def dashboard():
        """Interactive control center and telemetry dashboard."""
        if STATIC_DASHBOARD_PATH.exists():
            return FileResponse(STATIC_DASHBOARD_PATH, media_type="text/html")
        return HTMLResponse("<h2>RAGA Dashboard: static file not found.</h2>")

    @app.get("/", tags=["Dashboard & Status"])
    async def root(request: Request):
        """Root status and web dashboard router."""
        # If requested by a web browser, serve the interactive dashboard
        accept_header = request.headers.get("accept", "")
        if "text/html" in accept_header and STATIC_DASHBOARD_PATH.exists():
            return FileResponse(STATIC_DASHBOARD_PATH, media_type="text/html")

        # Otherwise return API status JSON
        return {
            "name": "RAGA API",
            "status": "operational",
            "version": "1.0.0",
            "dashboard": "/dashboard",
            "endpoints": [
                "GET /dashboard",
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

