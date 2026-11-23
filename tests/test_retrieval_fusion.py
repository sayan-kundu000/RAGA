"""Test suite for Reciprocal Rank Fusion (RRF) and hybrid retrieval.

Verifies:
- Accurate mathematical score calculation for RRF.
- Correct rank merging when documents appear in both dense and sparse lists.
- Proper ordering by consolidated RRF scores.
"""

import pytest
from app.schemas.chat import DocumentChunk
from app.retrieval.hybrid_search import reciprocal_rank_fusion


def test_rrf_mathematical_merging():
    """Verify that RRF properly merges mocked dense and sparse candidate returns."""
    k = 60

    # Mock candidate documents
    doc_a = DocumentChunk(id="doc_a", text="Dense top document")
    doc_b = DocumentChunk(id="doc_b", text="Dense second / Sparse top document")
    doc_c = DocumentChunk(id="doc_c", text="Sparse second document")

    # Dense ranked list: doc_a (rank 1), doc_b (rank 2)
    dense_results = [doc_a, doc_b]

    # Sparse ranked list: doc_b (rank 1), doc_c (rank 2)
    sparse_results = [doc_b, doc_c]

    # Expected RRF scores:
    # doc_a: 1/(60+1) = 1/61 =~ 0.016393
    # doc_b: 1/(60+2) + 1/(60+1) = 1/62 + 1/61 =~ 0.016129 + 0.016393 = 0.032522
    # doc_c: 1/(60+2) = 1/62 =~ 0.016129
    fused_results = reciprocal_rank_fusion(
        dense_results=dense_results,
        sparse_results=sparse_results,
        k=k,
        top_k=10,
    )

    assert len(fused_results) == 3
    # doc_b appeared in both and must be ranked #1
    assert fused_results[0].id == "doc_b"
    assert fused_results[1].id == "doc_a"
    assert fused_results[2].id == "doc_c"

    # Verify score accuracy
    expected_doc_b_score = round((1.0 / 61) + (1.0 / 62), 6)
    expected_doc_a_score = round(1.0 / 61, 6)
    expected_doc_c_score = round(1.0 / 62, 6)

    assert fused_results[0].score == expected_doc_b_score
    assert fused_results[1].score == expected_doc_a_score
    assert fused_results[2].score == expected_doc_c_score


def test_rrf_empty_inputs():
    """Verify RRF handles empty or disjoint input lists gracefully."""
    fused = reciprocal_rank_fusion([], [], k=60, top_k=5)
    assert fused == []

    doc1 = DocumentChunk(id="1", text="Only dense")
    fused_dense_only = reciprocal_rank_fusion([doc1], [], k=60, top_k=5)
    assert len(fused_dense_only) == 1
    assert fused_dense_only[0].id == "1"

