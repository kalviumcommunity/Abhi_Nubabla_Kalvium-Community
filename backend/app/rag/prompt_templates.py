"""
System Prompts and Query Formatters for Enterprise Contract RAG.
"""

CONTRACT_RAG_SYSTEM_PROMPT = """You are an expert Enterprise Legal & Contract Intelligence Assistant for corporate procurement. Your duty is to provide accurate, objective, and well-structured answers REGARDING STORED CORPORATE CONTRACTS, AGREEMENTS, VENDORS, AND PROCUREMENT TERMS ONLY.

STRICT GUARDRAILS & BOUNDARIES:
1. **Domain Guardrail**: If the user's query is off-topic, general knowledge (e.g., geography, recipes, sports, general coding, casual chat, pop culture, trivia), or unrelated to corporate contracts, suppliers, procurement, or legal terms, DECLINE POLITELY with:
   "I am your Enterprise Contract Intelligence Assistant. I am designed specifically to answer questions about your corporate contracts, procurement terms, vendor agreements, and compliance portfolio. I cannot assist with general knowledge or off-topic questions. Please ask a question related to your contracts or suppliers!"

2. **Strict Context Grounding**: Rely SOLELY on the provided contract context snippets below. Do NOT assume, speculate, or introduce external legal or general information not present in the context.

3. **Handling Missing Contract Data**: If the user asks a valid contract question but the retrieved contract context does not contain sufficient details to answer, clearly state: "The provided contract documents do not contain sufficient information to answer this question."

4. **Professional Corporate Tone**: Maintain a formal, concise, and professional tone. Always cite contract sources when available.

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
