# Chapter 05: Parent-Document Retrieval Architecture: Decoupling Search Index from LLM Context

> Part of the **RAGA Architecture & Systems Engineering Reference Manual**.

The Parent-Document Retrieval pattern is an architectural breakthrough designed to decouple the search representation of a document from its generative presentation. In conventional RAG setups, the exact text segment retrieved from the vector database is passed directly into the language model's prompt. This creates an unresolvable trade-off: indexing small chunks maximizes search precision but starves the LLM of necessary context, while indexing large chunks provides rich context but dilutes search accuracy.

Decoupling these two concerns resolves the conflict. In a Parent-Document Retrieval architecture, the vector index contains exclusively small child chunks optimized for semantic discrimination, while a separate document store retains the corresponding large parent nodes. The vector database functions purely as a high-precision locator, while the document store functions as the contextual provider for the generation stage.

Within RAGA, this architecture is implemented through the `ParentDocumentRetriever` and `ParentDocumentStore` classes. When documents are ingested, each parent node is persisted in the document store under a unique UUID key. The derived child chunks are embedded with a foreign key metadata reference pointing back to their respective `parent_id`. This establishes a one-to-many relationship between parent contexts and child search keys.

During the execution of a retrieval query, the hybrid search engine evaluates incoming queries against the child chunk corpus, generating a ranked list of candidate matches. Once the top-scoring child chunks are identified, the retriever invokes `resolve_parents()`. This method reads the `parent_id` from each matched child and queries the document store to fetch the corresponding full parent passage.

Crucially, the parent resolution logic incorporates intelligent deduplication while strictly preserving relevance ordering. If multiple child chunks originating from the same parent document appear in the top retrieval results, RAGA resolves that parent only once, assigning it the highest relevance score among its constituent child hits. This prevents duplicate passages from crowding the LLM prompt while maintaining ranking integrity.

The operational advantages of this pattern are substantial in technical and domain-specific search. For example, if a user queries a specific function argument, a child chunk containing that parameter name will score highly in dense and lexical matching. By resolving the parent document, the LLM receives the full class definition and surrounding docstrings, enabling it to explain parameter usage with complete architectural understanding.

By implementing Parent-Document Retrieval, RAGA achieves both pinpoint retrieval accuracy and comprehensive generative grounding. The system eliminates the ambiguity common to isolated chunk retrieval, establishing a robust foundation for subsequent reranking and token compression stages.
