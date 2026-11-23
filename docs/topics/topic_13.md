# Chapter 13: Cognitive Memory Taxonomies: Episodic, Semantic, and Procedural Memory Systems

> Part of the **RAGA Architecture & Systems Engineering Reference Manual**.

To build conversational agents capable of sustained, coherent collaboration across extended workflows, AI architectures must incorporate structured memory systems. Cognitive psychology categorizes human memory into three primary taxonomies: episodic memory, semantic memory, and procedural memory. Modern AI agents require computational counterparts for each of these modalities to overcome the stateless limitations of foundation models.

Episodic memory encapsulates the chronological record of specific past experiences, events, and conversational interactions. In an AI agent, episodic memory stores the transcript of prior turns, user questions, and model answers within a specific session. While vital for short-term conversational context, raw episodic logs expand linearly, eventually overflowing context windows and degrading attention focus if retained indefinitely.

Semantic memory, in contrast, abstracts structured knowledge, persistent facts, user preferences, and generalized concepts away from specific chronological episodes. When a user mentions that they develop in Python and prefer concise answers, semantic memory extracts and stores this factual preference permanently. On future sessions, the agent accesses these semantic facts without needing to re-read the original conversation transcript.

Procedural memory governs the rules, skills, and execution strategies required to perform tasks effectively. In agentic frameworks, procedural memory encompasses system prompts, tool usage specifications, routing heuristics, and formatting constraints. It defines how the agent operates, processes information, and adapts its behavior in response to semantic and episodic cues.

RAGA prioritizes persistent semantic memory as its primary personalization engine, drawing inspiration from Mem0 and Zep architectures. Rather than accumulating bulky episodic conversation histories, RAGA utilizes a dedicated extraction pipeline to distill raw conversational turns into atomic semantic facts. This keeps prompt token overhead minimal while enabling long-term personalization across sessions.

This cognitive separation enhances both token efficiency and user privacy. Raw conversational exchanges containing transient chit-chat or temporary debugging logs can be expired according to retention policies, while core user preferences remain securely indexed in the semantic memory store. This mirrors human cognitive consolidation, where detailed episodic memories fade while key facts endure.

By organizing its memory subsystem along cognitive principles, RAGA transcends the limitations of stateless interaction. The agent remembers developer preferences, honors stylistic constraints, and provides a continuous, personalized user experience across disparate sessions.
