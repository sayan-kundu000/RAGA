"""Test Case 1: Hybrid Retrieval & Re-ranking Latency Validation.

Specification:
1. Start the FastAPI application server.
2. Send a query payload to `/api/chat`. Verify that the JSON response contains the telemetry block.
3. Assert that retrieval_latency_ms, rerank_latency_ms, and total_latency_ms contain valid positive numeric values.
"""

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_hybrid_retrieval_and_reranking_latency_validation():
    """Execute Test Case 1 verification workflow."""
    payload = {
        "query": "Explain how hybrid search merges sparse and dense vectors.",
        "user_id": "usr_perf_test",
        "session_id": "session_latency_001",
    }

    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

    data = response.json()
    assert "telemetry" in data, "Response JSON missing telemetry metadata block"

    telemetry = data["telemetry"]

    # Assert that retrieval_latency_ms, rerank_latency_ms, and total_latency_ms contain valid positive numeric values
    assert "retrieval_latency_ms" in telemetry
    assert "rerank_latency_ms" in telemetry
    assert "generation_latency_ms" in telemetry
    assert "total_latency_ms" in telemetry

    retrieval_ms = telemetry["retrieval_latency_ms"]
    rerank_ms = telemetry["rerank_latency_ms"]
    generation_ms = telemetry["generation_latency_ms"]
    total_ms = telemetry["total_latency_ms"]

    assert isinstance(retrieval_ms, (int, float)) and retrieval_ms > 0, (
        f"retrieval_latency_ms must be positive numeric, got {retrieval_ms}"
    )
    assert isinstance(rerank_ms, (int, float)) and rerank_ms > 0, (
        f"rerank_latency_ms must be positive numeric, got {rerank_ms}"
    )
    assert isinstance(generation_ms, (int, float)) and generation_ms > 0, (
        f"generation_latency_ms must be positive numeric, got {generation_ms}"
    )
    assert isinstance(total_ms, (int, float)) and total_ms > 0, (
        f"total_latency_ms must be positive numeric, got {total_ms}"
    )

    # Total latency should be greater than or equal to individual components
    assert total_ms >= retrieval_ms
    assert total_ms >= rerank_ms
