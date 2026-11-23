"""FastAPI route endpoints for RAGA agent interactions, memories, and ingestion."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    UserMemoriesResponse,
    IngestRequest,
    IngestResponse,
)
from app.agent.rag_agent import RAGAAgent

router = APIRouter(prefix="/api", tags=["RAGA Pipeline"])

# Singleton agent instance for application lifecycle
_global_agent: RAGAAgent = RAGAAgent()


def get_agent() -> RAGAAgent:
    """Dependency provider for RAGAAgent singleton."""
    return _global_agent


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Execute RAG query with Context Compression & Semantic Memory",
    description="Accepts query, user_id, and session_id. Retrieves documents, updates memory, and returns response with latency telemetry.",
)
async def chat_endpoint(
    payload: ChatRequest,
    agent: RAGAAgent = Depends(get_agent),
) -> ChatResponse:
    """POST /api/chat endpoint."""
    try:
        response = agent.chat(payload)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing RAG pipeline: {str(e)}")


@router.get(
    "/users/{user_id}/memories",
    response_model=UserMemoriesResponse,
    summary="Retrieve long-term semantic facts for a user",
    description="Retrieves the current list of semantic facts stored for a user across sessions.",
)
async def get_user_memories_endpoint(
    user_id: str,
    agent: RAGAAgent = Depends(get_agent),
) -> UserMemoriesResponse:
    """GET /api/users/{user_id}/memories endpoint."""
    memories = agent.memory_store.get_memories(user_id)
    return UserMemoriesResponse(
        user_id=user_id,
        memories=memories,
    )


@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Ingest raw documents into Parent and Child retrieval indices",
    description="Segments raw texts into parent nodes and child chunks, and updates hybrid indexes.",
)
async def ingest_documents_endpoint(
    payload: IngestRequest,
    agent: RAGAAgent = Depends(get_agent),
) -> IngestResponse:
    """POST /api/ingest endpoint."""
    try:
        counts = agent.ingest_documents(payload.documents)
        return IngestResponse(
            parent_count=counts["parent_count"],
            child_count=counts["child_count"],
            status="success",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting documents: {str(e)}")

