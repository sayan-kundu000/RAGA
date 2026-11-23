# Chapter 21: Vector Database Internals: Qdrant HNSW Graph Indexing & Quantization

> Part of the **RAGA Architecture & Systems Engineering Reference Manual**.

Vector databases are purpose-built data engines optimized for storing, indexing, and querying high-dimensional vector embeddings at scale. Traditional relational databases and B-tree indexes are fundamentally unsuited for vector search, as computing high-dimensional Euclidean or cosine distances across millions of rows via linear scans requires unacceptable O(N) compute time. Vector databases resolve this by utilizing Approximate Nearest Neighbor (ANN) search algorithms.

At the heart of Qdrant's vector search architecture is the Hierarchical Navigable Small World (HNSW) graph algorithm. HNSW constructs a multi-layered graph where the top layers feature sparse, long-range connections for fast geometric navigation across vector space, while the bottom layers contain dense, localized connections for fine-grained nearest-neighbor identification. This hierarchical structure enables logarithmic O(log N) search complexity, delivering sub-millisecond query latencies across massive vector datasets.

Qdrant, implemented in Rust, provides high memory safety, predictable concurrency, and native payload-based metadata filtering. Unlike naive vector stores that filter metadata post-search—often discarding valid candidates and degrading recall—Qdrant integrates metadata constraints directly into the HNSW graph traversal. This ensures that filters, such as tenancy identifiers or document types, are enforced seamlessly during search execution.

To manage the substantial RAM footprints associated with hosting millions of high-dimensional floating-point vectors, Qdrant incorporates advanced vector quantization techniques. Scalar Quantization (SQ) compresses 32-bit floating-point coordinates (FP32) into 8-bit integers (INT8), achieving up to a 4x reduction in memory consumption with minimal impact on retrieval recall. For even larger datasets, Product Quantization (PQ) divides vectors into sub-vectors and clusters them, delivering up to a 16x memory reduction.

In RAGA, Qdrant serves as the dense vector index backend. Configured via the `QDRANT_URL` setting, RAGA supports both distributed Qdrant clusters for production scale and lightweight in-memory instances (`:memory:`) for developer environments and CI/CD pipelines. This flexibility enables identical vector retrieval logic to run in cloud environments and localized test runners without configuration drift.

Qdrant's architecture also natively supports hybrid search setups. By supporting both dense vectors and sparse term vectors within a unified collection schema, Qdrant allows modern retrieval pipelines to execute dense and lexical queries against a single vector engine, streamlining operational maintenance.

Understanding Qdrant's internal graph indexing, metadata filtering, and quantization strategies is essential for building scalable RAG architectures. By leveraging Qdrant's high-speed indexing, RAGA achieves the vector search efficiency required for demanding enterprise applications.
