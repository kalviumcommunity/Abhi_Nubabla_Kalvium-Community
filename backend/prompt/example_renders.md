# Prompt Template Example Renders

The chat and parameter-experiment features both render the same `RAG_REQUEST_TEMPLATE` at runtime.

## Chat request

```text
Use the verified context below to answer the staff member's question. If the context does not contain enough information, follow the fallback instruction in your system prompt.

Verified context:
The remote-work policy permits up to two remote days per week with manager approval.

Staff question:
How many remote days can I request?
```

## Batch experiment request

```text
Use the verified context below to answer the staff member's question. If the context does not contain enough information, follow the fallback instruction in your system prompt.

Verified context:
RAG retrieves relevant internal documents before generating an answer.

Staff question:
Explain what Retrieval-Augmented Generation (RAG) is in approximately 100 words. Focus on factual information and explain how retrieval provides context to the language model.
```