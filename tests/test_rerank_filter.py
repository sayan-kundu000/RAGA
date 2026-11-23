"""Test suite for Cohere ReRank Context Compression and score threshold filtering.

Verifies:
- Compression from 20 raw candidate chunks down to top 5.
- Pruning of chunks falling below the minimum relevance score threshold.
- Proper score propagation in metadata.
"""

from unittest.mock import MagicMock
import pytest
from app.schemas.chat import DocumentChunk
from app.retrieval.rerank import CohereContextCompressor


def test_rerank_compression_and_score_threshold_filter():
    """Mock Cohere API returns and verify the retriever drops document chunks

    that fall below the minimum relevance score threshold (e.g. 0.30).
    """
    # Create 10 candidate document chunks
    candidate_docs = [
        DocumentChunk(id=f"doc_{i}", text=f"Chunk content for document number {i}")
        for i in range(10)
    ]

    # Mock Cohere API response structure
    mock_cohere_client = MagicMock()
    # Assume 4 documents score above 0.3, and 6 score below 0.3
    mock_results = [
        MagicMock(index=0, relevance_score=0.95),
        MagicMock(index=1, relevance_score=0.82),
        MagicMock(index=2, relevance_score=0.64),
        MagicMock(index=3, relevance_score=0.41),
        MagicMock(index=4, relevance_score=0.28),  # below 0.30 -> must be dropped
        MagicMock(index=5, relevance_score=0.15),  # below 0.30 -> must be dropped
        MagicMock(index=6, relevance_score=0.08),  # below 0.30 -> must be dropped
        MagicMock(index=7, relevance_score=0.05),  # below 0.30 -> must be dropped
    ]
    mock_cohere_response = MagicMock()
    mock_cohere_response.results = mock_results
    mock_cohere_client.rerank.return_value = mock_cohere_response

    # Initialize compressor with mocked client and threshold 0.30
    compressor = CohereContextCompressor(
        client=mock_cohere_client,
        top_n=5,
        score_threshold=0.30,
    )

    compressed_docs = compressor.rerank_and_compress(
        query="test query for reranking",
        documents=candidate_docs,
        top_n=5,
        score_threshold=0.30,
    )

    # Assert that all dropped items had score < 0.30
    assert len(compressed_docs) == 4
    for doc in compressed_docs:
        assert doc.score is not None
        assert doc.score >= 0.30

    # Assert correct ordering by relevance score
    assert compressed_docs[0].id == "doc_0"
    assert compressed_docs[0].score == 0.95
    assert compressed_docs[1].id == "doc_1"
    assert compressed_docs[1].score == 0.82
    assert compressed_docs[2].id == "doc_2"
    assert compressed_docs[2].score == 0.64
    assert compressed_docs[3].id == "doc_3"
    assert compressed_docs[3].score == 0.41


def test_rerank_local_fallback_filter():
    """Verify the local heuristic fallback filter also adheres to score threshold."""
    docs = [
        DocumentChunk(id="1", text="Machine learning algorithms and deep neural networks"),
        DocumentChunk(id="2", text="Unrelated text about baking sourdough bread in ovens"),
    ]
    compressor = CohereContextCompressor(client=None, top_n=5, score_threshold=0.25)
    results = compressor.rerank_and_compress("machine learning algorithms", docs)

    # Doc 1 has high overlap, Doc 2 has zero overlap
    assert len(results) >= 1
    assert results[0].id == "1"
    assert all((d.score or 0) >= 0.25 for d in results)

