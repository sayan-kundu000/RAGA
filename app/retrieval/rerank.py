"""Cohere ReRank v3 Context Compression and token filtering.

Reduces top 20 candidate documents to top 5 highest-scoring documents
and prunes chunks below the minimum relevance score threshold.
"""

import os
from typing import List, Optional, Any
from app.schemas.chat import DocumentChunk
from app.core.config import get_settings


class CohereContextCompressor:
    """Compresses candidate documents using Cohere ReRank v3 cross-encoder model."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        top_n: Optional[int] = None,
        score_threshold: Optional[float] = None,
        client: Optional[Any] = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.COHERE_API_KEY
        self.model = model or settings.RERANK_MODEL
        self.top_n = top_n if top_n is not None else settings.RERANK_TOP_N
        self.score_threshold = (
            score_threshold if score_threshold is not None else settings.RERANK_SCORE_THRESHOLD
        )
        self.client = client

        # Lazy initialize Cohere client if not injected and api_key present
        if self.client is None and self.api_key:
            try:
                import cohere

                self.client = cohere.ClientV2(api_key=self.api_key)
            except Exception:
                try:
                    import cohere

                    self.client = cohere.Client(api_key=self.api_key)
                except Exception:
                    self.client = None

    def rerank_and_compress(
        self,
        query: str,
        documents: List[DocumentChunk],
        top_n: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ) -> List[DocumentChunk]:
        """Re-rank candidate documents against the query and compress the list.

        Args:
            query: The user prompt or retrieval query.
            documents: Candidate documents (e.g. top 20 from hybrid search).
            top_n: Maximum number of compressed documents to retain (default 5).
            score_threshold: Minimum acceptable relevance score.

        Returns:
            Compressed list of top_n documents scoring above score_threshold.
        """
        if not documents:
            return []

        limit = top_n if top_n is not None else self.top_n
        threshold = score_threshold if score_threshold is not None else self.score_threshold

        # 1. Use real Cohere API or injected mock client if available
        if self.client is not None:
            try:
                doc_texts = [d.text for d in documents]

                # Support both Cohere v2 (client.rerank) and v1 interfaces or mocks
                if hasattr(self.client, "rerank"):
                    response = self.client.rerank(
                        model=self.model,
                        query=query,
                        documents=doc_texts,
                        top_n=min(limit, len(documents)),
                    )
                else:
                    response = None

                if response and hasattr(response, "results"):
                    compressed: List[DocumentChunk] = []
                    for result in response.results:
                        score = getattr(result, "relevance_score", 0.0)
                        idx = getattr(result, "index", 0)

                        # Filter out chunks falling below relevance threshold
                        if score >= threshold and idx < len(documents):
                            orig_doc = documents[idx]
                            compressed.append(
                                DocumentChunk(
                                    id=orig_doc.id,
                                    text=orig_doc.text,
                                    parent_id=orig_doc.parent_id,
                                    metadata={
                                        **orig_doc.metadata,
                                        "rerank_score": round(float(score), 4),
                                    },
                                    score=round(float(score), 4),
                                )
                            )
                    return compressed[:limit]
            except Exception as e:
                # Log error and fallback to score-based heuristic
                pass

        # 2. Local Fallback / Heuristic Scorer for offline execution and testing
        return self._local_heuristic_rerank(query, documents, limit, threshold)

    def _local_heuristic_rerank(
        self,
        query: str,
        documents: List[DocumentChunk],
        top_n: int,
        score_threshold: float,
    ) -> List[DocumentChunk]:
        """Deterministic lexical-semantic overlap scorer used when no external API is available."""
        from app.retrieval.hybrid_search import tokenize

        query_terms = set(tokenize(query))
        scored_docs = []

        for doc in documents:
            doc_terms = tokenize(doc.text)
            if not doc_terms:
                score = 0.0
            else:
                matches = sum(1 for t in doc_terms if t in query_terms)
                # Normalize by query length and doc length
                term_coverage = matches / max(len(query_terms), 1)
                # Combine with any prior score (RRF score)
                prior = doc.score if doc.score is not None else 0.5
                score = round(min(0.3 * prior + 0.7 * term_coverage, 1.0), 4)

            # Apply score threshold filter
            if score >= score_threshold:
                scored_docs.append(
                    DocumentChunk(
                        id=doc.id,
                        text=doc.text,
                        parent_id=doc.parent_id,
                        metadata={
                            **doc.metadata,
                            "rerank_score": score,
                            "rerank_provider": "local_simulator",
                        },
                        score=score,
                    )
                )

        scored_docs.sort(key=lambda d: d.score or 0.0, reverse=True)
        return scored_docs[:top_n]

