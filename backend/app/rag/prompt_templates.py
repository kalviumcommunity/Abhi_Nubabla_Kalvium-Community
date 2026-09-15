"""
System Prompts and Query Formatters for Enterprise Contract RAG.
"""

CONTRACT_RAG_SYSTEM_PROMPT = """You are an expert Enterprise Legal & Contract Assistant. Your duty is to provide highly accurate, objective, and well-structured answers to queries regarding stored corporate contracts and agreements.

CRITICAL INSTRUCTIONS & BOUNDARIES:
1. **Strict Context Grounding**: Rely SOLELY on the provided contract context snippets below. Do NOT assume, speculate, or introduce external legal information not present in the context.
2. **Citations & References**: Always cite the exact contract title, section/clause name, or chunk reference when answering.
3. **Handling Ambiguity & Missing Information**: If the retrieved contract context does not contain enough information to answer the user's question, clearly state: "The provided contract documents do not contain sufficient information to answer this question."
4. **Professional Tone**: Maintain a formal, accurate corporate tone. Avoid fluff or legal disclaimers unless explicitly asked.

Retrieved Contract Context:
--------------------------------------------------------------------------------
{context}
--------------------------------------------------------------------------------
"""

def render_contract_rag_prompt(query: str, retrieved_chunks: list) -> tuple:
    """
    Renders context block and system prompt for Contract Q&A.
    """
    context_blocks = []
    for idx, item in enumerate(retrieved_chunks, 1):
        meta = item.get("metadata", {})
        c_title = meta.get("contract_title") or meta.get("filename") or "Unknown Contract"
        sec_title = meta.get("section_title") or "General Clause"
        c_id = item.get("chunk_id", f"chunk-{idx}")
        score = item.get("similarity_score", 0.0)
        
        block = (
            f"[Source {idx} | Ref: {c_id}]\n"
            f"Contract Title: {c_title}\n"
            f"Section/Clause: {sec_title}\n"
            f"Relevance Match: {score:.2f}\n"
            f"Content:\n{item['text']}\n"
        )
        context_blocks.append(block)

    formatted_context = "\n---\n".join(context_blocks) if context_blocks else "No relevant contract context retrieved."
    system_prompt = CONTRACT_RAG_SYSTEM_PROMPT.format(context=formatted_context)
    
    return system_prompt, formatted_context
