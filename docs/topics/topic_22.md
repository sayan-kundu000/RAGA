# Chapter 22: Local Storage Persistence & Document Key-Value Mapping Strategies

> Part of the **RAGA Architecture & Systems Engineering Reference Manual**.

In hierarchical retrieval architectures such as Parent-Document Retrieval, fast and reliable passage storage is just as vital as vector indexing. While vector databases excel at indexing compact child chunks for mathematical similarity matching, storing large, multi-kilobyte parent text nodes directly within vector payloads can degrade memory efficiency and slow index traversals. Separating search vectors from parent passage storage optimizes overall pipeline performance.

A dedicated document store functions as a specialized key-value repository optimized for rapid point lookups by identifier. When the retrieval pipeline resolves parent documents, it performs indexed primary key lookups (`parent_id`) rather than broad table scans. This key-value pattern delivers deterministic O(1) retrieval latencies, ensuring parent context resolution adds negligible overhead to the end-to-end request.

In RAGA, this storage layer is implemented via the `ParentDocumentStore` class in `app/retrieval/parent_document.py`. The store maintains a keyed registry of `DocumentChunk` parent nodes, exposing clean methods for single lookups (`get`), batch retrievals (`multi_get`), insertions (`put`), and state resets (`clear`). This clean abstraction isolates parent document storage from the retrieval and generation modules.

For enterprise production deployments, this in-memory key-value pattern maps directly to high-throughput, persistent storage engines such as Redis, SQLite, RocksDB, or cloud blob stores like Amazon S3. In high-traffic environments, caching hot parent documents in an in-memory Redis cluster provides sub-millisecond point lookups while offloading persistent storage to durable distributed databases.

Data serialization within the document store is standardized using RAGA's Pydantic schemas. Parent nodes are stored alongside rich metadata attributes, including document source, heading hierarchies, section indices, and ingestion timestamps. When a parent node is retrieved, this metadata is reconstructed without loss, supplying the downstream LLM with complete contextual provenance.

Additionally, the document store coordinates with the vector database during ingestion and deletion lifecycles. When a document is re-indexed or removed, the pipeline removes both the parent node from the document store and its associated child chunk vectors from the vector index, preventing orphaned data from degrading retrieval quality.

By establishing an optimized key-value storage layer for parent documents, RAGA ensures that context resolution remains fast, scalable, and decoupled from vector search. This architecture provides the structural foundation needed to deliver rich, grounded context to the language model.
