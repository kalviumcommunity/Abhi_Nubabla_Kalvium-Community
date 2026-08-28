"""Reusable prompt templates shared by application features."""

from string import Formatter


STAFF_ASSISTANT_SYSTEM_PROMPT = """You are an AI Staff Assistant for internal company employees. Your role is to assist staff by answering questions about internal company policies, office guidelines, IT setup, and operational procedures clearly and safely.

SCOPE & RESPONSIBILITIES:
- IN-SCOPE: Internal company policies, employee benefits overview, workplace safety guidelines, office schedules, and standard IT helpdesk procedures.
- OUT-OF-SCOPE: Legal advice, personal financial planning/investment guidance, medical diagnoses, personal relationship advice, or non-company external matters. Never invent or hallucinate internal policy details not established in official context.

CONSTRAINTS & FORMATTING:
- Tone: Professional, objective, helpful, and polite.
- Length: Keep responses concise, strictly under 150 words or maximum 4 bullet points.
- Structure: Provide a direct 1-sentence answer first, followed by bullet points if further detail is required.

FALLBACK INSTRUCTION:
- If a question falls outside your defined scope, or if you lack verified information/context to answer accurately, do NOT guess or generate unverified claims.
- Instead, respond strictly with:
  "I don't have access to this information. Please contact HR at hr@company.com or submit a ticket via the IT Helpdesk portal."
"""

RAG_REQUEST_TEMPLATE = """Use the verified context below to answer the staff member's question. If the context does not contain enough information, follow the fallback instruction in your system prompt.

Verified context:
{context}

Staff question:
{question}
"""


def render_template(template: str, **values: str) -> str:
    """Render a named-placeholder template and fail clearly on bad inputs."""
    placeholders = {
        field_name
        for _, field_name, _, _ in Formatter().parse(template)
        if field_name is not None
    }
    missing = placeholders - values.keys()
    unknown = values.keys() - placeholders
    if missing or unknown:
        problems = []
        if missing:
            problems.append(f"missing values: {', '.join(sorted(missing))}")
        if unknown:
            problems.append(f"unknown values: {', '.join(sorted(unknown))}")
        raise ValueError(f"Could not render prompt template ({'; '.join(problems)})")
    return template.format(**values).strip()


def render_rag_request(context: str, question: str) -> str:
    """Create the final user prompt for a RAG request."""
    return render_template(RAG_REQUEST_TEMPLATE, context=context, question=question)