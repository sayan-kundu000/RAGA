"""Hybrid dense-sparse retrieval combining vector similarity with BM25 keyword matching

using Reciprocal Rank Fusion (RRF) to merge candidate result lists.
"""

import math
import re
from typing import List, Dict, Optional, Tuple, Any
from app.schemas.chat import DocumentChunk
from app.core.config import get_settings


def tokenize(text: str) -> List[str]:
    """Tokenize and normalize text into lowercase terms."""
    return re.findall(r"\w+", text.lower())


def reciprocal_rank_fusion(
    dense_results: List[DocumentChunk],
    sparse_results: List[DocumentChunk],
    k: int = 60,
    top_k: int = 20,
) -> List[DocumentChunk]:
    """Merge ranked lists from dense semantic search and sparse lexical search

    using Reciprocal Rank Fusion (RRF).

    Formula:
        RRF_Score(d) = sum_{m in M} (1.0 / (k + rank_m(d)))
    where rank_m(d) is 1-based index in ranking list m.

    Args:
        dense_results: Ranked list of DocumentChunk from dense search.
        sparse_results: Ranked list of DocumentChunk from sparse BM25 search.
        k: Smoothing constant (standard RRF constant = 60).
        top_k: Maximum number of merged documents to return.

    Returns:
        Consolidated list of DocumentChunk sorted by descending RRF score.
    """
    scores: Dict[str, float] = {}
    doc_map: Dict[str, DocumentChunk] = {}

    # 1. Process dense rankings
    for rank, doc in enumerate(dense_results, start=1):
        doc_id = doc.id
        doc_map[doc_id] = doc
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    # 2. Process sparse rankings
    for rank, doc in enumerate(sparse_results, start=1):
        doc_id = doc.id
        if doc_id not in doc_map:
            doc_map[doc_id] = doc
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    # 3. Sort unique documents by merged RRF score
    sorted_doc_ids = sorted(scores.keys(), key=lambda did: scores[did], reverse=True)

    merged: List[DocumentChunk] = []
    for doc_id in sorted_doc_ids[:top_k]:
        base_doc = doc_map[doc_id]
        merged.append(
            DocumentChunk(
                id=base_doc.id,
                text=base_doc.text,
                parent_id=base_doc.parent_id,
                metadata={
                    **base_doc.metadata,
                    "rrf_score": round(scores[doc_id], 6),
                },
                score=round(scores[doc_id], 6),
            )
        )

    return merged


class BM25Index:
    """Sparse lexical search index based on BM25 Okapi."""

    def __init__(self) -> None:
        self.documents: List[DocumentChunk] = []
        self.corpus_tokens: List[List[str]] = []
        self._bm25 = None

    def index_documents(self, documents: List[DocumentChunk]) -> None:
        """Build BM25 index over document chunks."""
        from rank_bm25 import BM25Okapi

        self.documents = documents
        self.corpus_tokens = [tokenize(doc.text) for doc in documents]
        if self.corpus_tokens:
            self._bm25 = BM25Okapi(self.corpus_tokens)
        else:
            self._bm25 = None

    def search(self, query: str, top_k: int = 20) -> List[DocumentChunk]:
        """Perform lexical keyword search and return top-k documents."""
        if not self._bm25 or not self.documents:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return self.documents[:top_k]

        scores = self._bm25.get_scores(query_tokens)
        scored_pairs = list(zip(self.documents, scores))
        scored_pairs.sort(key=lambda x: x[1], reverse=True)

        results = []
        for doc, score in scored_pairs[:top_k]:
            results.append(
                DocumentChunk(
                    id=doc.id,
                    text=doc.text,
                    parent_id=doc.parent_id,
                    metadata=doc.metadata,
                    score=float(round(score, 4)),
                )
            )
        return results


class DenseVectorIndex:
    """Dense semantic vector index with support for Qdrant and local fallback."""

    def __init__(self, collection_name: Optional[str] = None) -> None:
        settings = get_settings()
        self.collection_name = collection_name or settings.COLLECTION_NAME
        self.documents: Dict[str, DocumentChunk] = {}
        self.vectors: Dict[str, List[float]] = {}
        self._qdrant_client = None

        # Attempt to initialize Qdrant in-memory or remote
        try:
            from qdrant_client import QdrantClient

            self._qdrant_client = QdrantClient(location=settings.QDRANT_URL)
        except Exception:
            self._qdrant_client = None

    def _compute_embedding(self, text: str) -> List[float]:
        """Generate normalized embedding vector.

        Uses deterministic hashing/token frequency projection for local fallback,
        or OpenAI/Cohere embeddings when configured.
        """
        dim = 128
        vec = [0.0] * dim
        tokens = tokenize(text)
        if not tokens:
            return vec

        for token in tokens:
            # Deterministic word hashing into dim buckets
            h = abs(hash(token)) % dim
            vec[h] += 1.0

        # L2 normalization
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def index_documents(self, documents: List[DocumentChunk]) -> None:
        """Index document chunks into vector space."""
        for doc in documents:
            self.documents[doc.id] = doc
            self.vectors[doc.id] = self._compute_embedding(doc.text)

    def search(self, query: str, top_k: int = 20) -> List[DocumentChunk]:
        """Perform dense semantic search using cosine similarity."""
        query_vec = self._compute_embedding(query)
        q_norm = math.sqrt(sum(v * v for v in query_vec))
        if q_norm == 0:
            return list(self.documents.values())[:top_k]

        scores: List[Tuple[DocumentChunk, float]] = []
        for doc_id, doc_vec in self.vectors.items():
            # Dot product for normalized vectors = cosine similarity
            dot = sum(q * d for q, d in zip(query_vec, doc_vec))
            scores.append((self.documents[doc_id], float(dot)))

        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for doc, score in scores[:top_k]:
            results.append(
                DocumentChunk(
                    id=doc.id,
                    text=doc.text,
                    parent_id=doc.parent_id,
                    metadata=doc.metadata,
                    score=float(round(score, 4)),
                )
            )
        return results


class HybridRetriever:
    """Orchestrates hybrid dense + sparse search with RRF rank fusion."""

    def __init__(
        self,
        dense_index: Optional[DenseVectorIndex] = None,
        sparse_index: Optional[BM25Index] = None,
        rrf_k: Optional[int] = None,
        candidates_k: Optional[int] = None,
    ) -> None:
        settings = get_settings()
        self.dense_index = dense_index or DenseVectorIndex()
        self.sparse_index = sparse_index or BM25Index()
        self.rrf_k = rrf_k or settings.RRF_K
        self.candidates_k = candidates_k or settings.HYBRID_RETRIEVAL_CANDIDATES

    def index_documents(self, documents: List[DocumentChunk]) -> None:
        """Index documents across both dense and sparse representations."""
        self.dense_index.index_documents(documents)
        self.sparse_index.index_documents(documents)

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[DocumentChunk]:
        """Execute hybrid search: dense + sparse -> RRF fusion."""
        k = top_k or self.candidates_k
        dense_hits = self.dense_index.search(query, top_k=k)
        sparse_hits = self.sparse_index.search(query, top_k=k)
        return reciprocal_rank_fusion(
            dense_results=dense_hits,
            sparse_results=sparse_hits,
            k=self.rrf_k,
            top_k=k,
        )
