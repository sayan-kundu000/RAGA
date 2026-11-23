# Chapter 12: Relevance Score Thresholding & Hallucination Mitigation Techniques

> Part of the **RAGA Architecture & Systems Engineering Reference Manual**.

Hallucination remains one of the primary hurdles preventing autonomous AI agents from achieving widespread enterprise adoption. A frequent trigger of hallucinated outputs in RAG systems is forced generation over low-relevance context. When a user submits an out-of-domain, malicious, or unanswerable query, naive systems nonetheless retrieve their top-k nearest neighbors, forcing the LLM to synthesize an answer from unhelpful or misleading passages.

Relevance score thresholding establishes an essential defensive filter within the retrieval pipeline. Rather than unconditionally returning the top-k documents regardless of their quality, thresholding imposes a strict mathematical floor. If retrieved passages fail to meet the minimum score threshold, they are discarded. When no passages pass the threshold, the agent recognizes the absence of grounded data and refuses to fabricate an answer.

In RAGA, relevance score thresholding is integrated directly into the `CohereContextCompressor`. Cohere ReRank v3 produces calibrated relevance scores that reflect passage utility. RAGA applies a default threshold of 0.30 (configurable via `RERANK_SCORE_THRESHOLD`). Any candidate chunk scoring below this threshold is dropped, regardless of its position in the candidate list.

This mechanism is particularly effective at eliminating distractor chunks. In multi-topic documents, a passage may share incidental vocabulary with a query while discussing an entirely unrelated subject. While first-stage bi-encoders and BM25 might assign such chunks moderate scores, the cross-encoder identifies the semantic divergence and assigns a low relevance score, triggering the threshold filter.

The behavior of the threshold filter is rigorously verified through automated unit tests. Within `tests/test_rerank_filter.py`, mocked Cohere API returns verify that candidate chunks scoring below the cutoff are pruned from the final document list. This guarantees that threshold enforcement operates reliably and consistently across all deployment environments.

Complementing retrieval thresholding, RAGA implements persona adaptation rules that instruct the language model to ground its responses strictly in retrieved context. When the compressed document set is empty, the agent explicitly notifies the user rather than speculating, preventing ungrounded extrapolations.

By implementing strict relevance score thresholding, RAGA eliminates ungrounded answers at the retrieval stage. The system ensures that only verified, high-scoring context reaches the language model, upholding factual accuracy across all interactions.
