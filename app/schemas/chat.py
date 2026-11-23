"""Pydantic request and response schemas for RAGA API."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.core.telemetry import TelemetryMetrics


class DocumentChunk(BaseModel):
    """Schema for retrieved document chunks."""
    id: str = Field(..., description="Unique document chunk identifier")
    text: str = Field(..., description="Extracted text chunk content")
    parent_id: Optional[str] = Field(None, description="Identifier of the parent document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata tags")
    score: Optional[float] = Field(None, description="Relevance or re-rank score")


class ChatRequest(BaseModel):
    """Request payload for /api/chat endpoint."""
    query: str = Field(..., min_length=1, description="User question or prompt", examples=["Write a quick merge sort routine."])
    user_id: str = Field(..., min_length=1, description="Unique user identifier", examples=["usr_99"])
    session_id: str = Field(..., min_length=1, description="Unique session identifier", examples=["sess_001"])


class ChatResponse(BaseModel):
    """Response payload for /api/chat endpoint."""
    response: str = Field(..., description="Generated answer from the RAGA agent")
    user_id: str = Field(..., description="User ID associated with the interaction")
    session_id: str = Field(..., description="Active session ID")
    telemetry: TelemetryMetrics = Field(..., description="Execution latency profiling metadata")
    retrieved_documents: List[DocumentChunk] = Field(
        default_factory=list,
        description="Top compressed document chunks fed to the LLM prompt"
    )


class UserMemoriesResponse(BaseModel):
    """Response payload for /api/users/{user_id}/memories endpoint."""
    user_id: str = Field(..., description="User identifier")
    memories: List[str] = Field(default_factory=list, description="List of extracted semantic facts and preferences")


class IngestRequest(BaseModel):
    """Request payload to ingest documents into the RAGA pipeline."""
    documents: List[Dict[str, Any]] = Field(..., description="List of raw documents containing text and optional metadata")


class IngestResponse(BaseModel):
    """Response payload confirming document ingestion."""
    parent_count: int = Field(..., description="Number of parent documents indexed")
    child_count: int = Field(..., description="Number of child chunks generated and indexed")
    status: str = Field("success", description="Status string")

