# Chapter 32: Agentic RAG Extensions: Query Transformation, HyDE & Multi-Hop Reasoning

> Part of the **RAGA Architecture & Systems Engineering Reference Manual**.

While Advanced RAG pipelines excel at resolving single-step factual inquiries, complex enterprise problem-solving often requires multi-step reasoning, query decomposition, and iterative information gathering. Agentic RAG extends standard retrieval pipelines by granting the language model autonomous agency to reformulate queries, plan multi-step retrieval strategies, and evaluate whether retrieved evidence is sufficient to answer the prompt.

A foundational agentic extension is Query Transformation, which rewrites ambiguous, conversational, or poorly phrased user queries into optimized search vectors. In multi-turn conversations, user questions frequently contain pronoun references (e.g. 'What are its performance benefits?'). An agentic query rewriter analyzes the conversational context to produce an explicit search query ('What are the performance benefits of Qdrant HNSW indexing?'), improving retrieval recall.

Hypothetical Document Embeddings (HyDE) represent another powerful agentic technique for overcoming vocabulary mismatches. Instead of embedding an abstract, brief user query directly, HyDE prompts an LLM to generate a hypothetical, ideal answer to the question. While this speculative answer may contain factual inaccuracies, its linguistic style and terminology closely match genuine source documents. Embedding this hypothetical answer produces vector search results with high topical overlap.

For complex research questions requiring information from disparate sources, Agentic RAG employs Multi-Hop Reasoning and Query Decomposition. The agent breaks a complex question down into discrete sub-queries, executes targeted retrieval for each sub-problem, evaluates the intermediate evidence, and synthesizes the findings into a cohesive answer. If initial retrieval leaves gaps, the agent autonomously issues follow-up queries.

Routing agents represent an additional layer of architectural sophistication. By classifying incoming user queries, an agentic router determines the optimal execution path: directing simple factual queries to cached memory lookups, technical questions to the hybrid RAGA retrieval pipeline, and numerical inquiries to external API tools, optimizing both cost and latency.

In RAGA, these agentic patterns are designed as modular pre-retrieval and post-retrieval middleware. The core hybrid search, parent document resolution, and Cohere compression modules serve as reliable tool primitives that higher-level agentic loops (such as LangGraph state machines) can invoke iteratively.

Agentic RAG extensions transform information retrieval from a static, single-turn lookup into an active, intelligent reasoning process. By incorporating query rewriting, HyDE, and multi-hop planning, RAGA handles complex, ambiguous inquiries with high accuracy.
