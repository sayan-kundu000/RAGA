# Chapter 11: Contextual Compression & Token Economics: Signal-to-Noise Optimization

> Part of the **RAGA Architecture & Systems Engineering Reference Manual**.

In modern enterprise LLM applications, token economics and prompt signal-to-noise ratios are central drivers of performance, cost, and accuracy. Language models exhibit known vulnerabilities when presented with excessive context, including the 'lost-in-the-middle' phenomenon where models overlook critical facts placed within long prompts. Moreover, every uninformative token passed to an LLM increases billing costs and inflates time-to-first-token generation latencies.

Contextual compression directly addresses this challenge by systematically trimming extraneous context before prompt construction. Rather than feeding raw retrieval dumps directly into the language model, contextual compression evaluates, filters, and prunes passages. The objective is to maximize the density of relevant information per prompt token, supplying the LLM with high-signal context.

In the RAGA pipeline, contextual compression operates as a two-stage filter. First, candidate documents are retrieved using hybrid search and expanded to their respective parent nodes. While parent expansion restores vital context, it also introduces additional tokens. The second stage uses Cohere ReRank v3 to compress these candidate documents down to the top 5 highest-scoring passages, discarding tangential material.

The financial benefits of this compression pipeline are substantial when deployed at scale. In a typical enterprise application processing millions of queries monthly, passing 20 raw parent documents (averaging 1,000 characters each) would consume millions of unnecessary prompt tokens daily. Compressing the candidate set down to the top 5 relevant passages reduces prompt token volumes by up to 75%, leading to major API cost savings.

Beyond financial savings, context compression significantly reduces generation latency. Large language model inference speeds are inversely correlated with prompt length, as input token ingestion requires GPU compute time before the first output token can be decoded. By delivering compact, high-relevance prompts, RAGA decreases generation latency and accelerates overall response times.

Additionally, contextual compression mitigates hallucination risks. When language models are flooded with tangential text, attention weights disperse across irrelevant tokens, increasing the likelihood that the model incorporates irrelevant details or fabricates answers. Providing a focused set of relevant passages concentrates the model's attention on factual context, enhancing answer faithfulness.

Contextual compression transforms information retrieval from a brute-force context dump into a refined signal-extraction pipeline. By optimizing prompt token economics and maximizing the signal-to-noise ratio, RAGA achieves high performance, cost efficiency, and generative reliability.
