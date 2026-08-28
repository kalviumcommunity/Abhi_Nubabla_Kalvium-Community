"""
Structured Output Module for RAG Assistant.

Tasks Implemented:
- Task 1: Prompt for a defined JSON structure ({"answer": ..., "source": ...})
           using JSON/response-format mode where available.
- Task 2: Parse the JSON response into a usable Python dict.
- Task 3: Handle malformed JSON gracefully — detect and report without crashing.
- Task 4: Validate that all required fields ("answer", "source") are present;
           reject or recover if any are missing.
- Task 5: Commit with sample parsed results (see data/structured_output_results.json).
"""

import json
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ─── Required fields for every structured response ──────────────────────────
REQUIRED_FIELDS = ["answer", "source"]

# ─── System prompt that enforces JSON output ─────────────────────────────────
STRUCTURED_SYSTEM_PROMPT = """You are a RAG (Retrieval-Augmented Generation) assistant for internal company staff.

CRITICAL OUTPUT RULE — YOU MUST FOLLOW THIS EXACTLY:
You MUST respond with a valid JSON object and NOTHING else.
Do NOT include any text, explanation, markdown, or code fences outside the JSON object.

The JSON object MUST have exactly these two keys:
{
  "answer": "<your concise answer to the question>",
  "source": "<the document, policy, or knowledge source you based the answer on>"
}

Examples of valid responses:
{"answer": "The standard work-from-home policy allows up to 2 days per week with manager approval.", "source": "Employee Handbook, Section 4.2 — Remote Work Policy"}
{"answer": "I don't have verified information on this topic.", "source": "N/A — No matching internal document found"}

RULES:
- The "answer" field must contain your response to the user's question.
- The "source" field must cite the document or policy you referenced; use "N/A" if unknown.
- Do NOT wrap the JSON in markdown code fences or add any surrounding text.
- Do NOT add extra keys beyond "answer" and "source".
"""

# ─── Test questions to exercise the pipeline ─────────────────────────────────
TEST_QUESTIONS = [
    {
        "id": "structured_q1",
        "question": "What is the company policy on requesting sick leave?",
        "description": "Standard in-scope question — expects clean JSON.",
    },
    {
        "id": "structured_q2",
        "question": "How do I reset my corporate VPN password?",
        "description": "IT helpdesk question — expects clean JSON.",
    },
    {
        "id": "structured_q3",
        "question": "What are the office hours during the holiday season?",
        "description": "Policy question — expects clean JSON.",
    },
]

# ─── Synthetic malformed payloads for testing Task 3 & 4 ─────────────────────
MALFORMED_TEST_CASES = [
    {
        "id": "malformed_broken_json",
        "raw": '{"answer": "Sick leave requires a doctor\'s note", "source": }',
        "description": "Broken JSON — trailing comma / missing value.",
    },
    {
        "id": "malformed_missing_source",
        "raw": '{"answer": "You can reset your VPN password via the IT portal."}',
        "description": "Valid JSON but missing required 'source' field.",
    },
    {
        "id": "malformed_missing_answer",
        "raw": '{"source": "IT Helpdesk FAQ, Section 2.1"}',
        "description": "Valid JSON but missing required 'answer' field.",
    },
    {
        "id": "malformed_empty_string",
        "raw": "",
        "description": "Completely empty response string.",
    },
    {
        "id": "malformed_markdown_wrapped",
        "raw": '```json\n{"answer": "Holiday hours are 9 AM to 3 PM.", "source": "Office Schedule 2025"}\n```',
        "description": "JSON wrapped in markdown code fences — needs extraction.",
    },
    {
        "id": "malformed_with_thinking_tags",
        "raw": '<think>Let me consider the policy...</think>\n{"answer": "Two remote days allowed per week.", "source": "HR Policy Manual, Section 4"}',
        "description": "Response prefixed with <think> tags from reasoning models.",
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
#  Task 2 & 3: Parse JSON safely
# ═══════════════════════════════════════════════════════════════════════════════


def clean_raw_response(raw: str) -> str:
    """
    Pre-process a raw LLM response string to extract the JSON payload.

    Handles common model quirks:
      - Strips markdown code fences (```json ... ```)
      - Strips <think>...</think> reasoning tags
      - Trims surrounding whitespace
    """
    if not raw or not raw.strip():
        return ""

    text = raw.strip()

    # Strip <think>...</think> blocks (reasoning models like Qwen3)
    if "<think>" in text and "</think>" in text:
        text = text.split("</think>")[-1].strip()

    # Strip markdown code fences: ```json ... ``` or ``` ... ```
    fence_pattern = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```$", re.DOTALL)
    match = fence_pattern.match(text)
    if match:
        text = match.group(1).strip()

    return text


def parse_json_response(raw: str) -> dict:
    """
    Task 2 — Parse the raw string into a Python dict.
    Task 3 — If the JSON is malformed, raise a descriptive ValueError
             instead of letting json.JSONDecodeError propagate uncaught.

    Returns:
        dict with the parsed data.

    Raises:
        ValueError with a human-readable message on any parse failure.
    """
    cleaned = clean_raw_response(raw)

    if not cleaned:
        raise ValueError(
            "Empty response received from model — no JSON to parse."
        )

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Malformed JSON — could not parse model response. "
            f"JSONDecodeError: {exc.msg} at line {exc.lineno} col {exc.colno}. "
            f"Raw (cleaned): {cleaned!r}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a JSON object (dict), got {type(data).__name__}: {data!r}"
        )

    return data


# ═══════════════════════════════════════════════════════════════════════════════
#  Task 4: Validate required fields
# ═══════════════════════════════════════════════════════════════════════════════


def validate_fields(data: dict, required: list[str] = REQUIRED_FIELDS) -> dict:
    """
    Validate that all required keys exist and are non-empty strings.

    Returns:
        The validated dict if all fields pass.

    Raises:
        ValueError listing every missing or empty field.
    """
    problems = []

    for field in required:
        if field not in data:
            problems.append(f"Missing required field: '{field}'")
        elif not isinstance(data[field], str) or not data[field].strip():
            problems.append(f"Field '{field}' is empty or not a string")

    if problems:
        raise ValueError(
            "Validation failed — " + "; ".join(problems) + f". Got: {data!r}"
        )

    return data


# ═══════════════════════════════════════════════════════════════════════════════
#  Combined safe-parse pipeline
# ═══════════════════════════════════════════════════════════════════════════════


def safe_parse_and_validate(raw: str) -> dict:
    """
    Full pipeline: clean → parse → validate.

    Returns a result dict:
        On success: {"status": "ok", "data": {...}}
        On failure: {"status": "error", "error": "...", "raw": "..."}
    """
    try:
        data = parse_json_response(raw)
        validated = validate_fields(data)
        return {"status": "ok", "data": validated}
    except ValueError as exc:
        return {"status": "error", "error": str(exc), "raw": raw}


# ═══════════════════════════════════════════════════════════════════════════════
#  Task 1: Call the model with JSON structure instructions
# ═══════════════════════════════════════════════════════════════════════════════


def call_llm_structured(
    client: OpenAI, model_name: str, user_question: str
) -> str:
    """
    Task 1 — Send a chat completion request instructing the model to return
    a JSON object with {"answer": ..., "source": ...}.

    Uses `response_format={"type": "json_object"}` when supported by the
    provider; falls back to prompt-only enforcement otherwise.
    """
    messages = [
        {"role": "system", "content": STRUCTURED_SYSTEM_PROMPT},
        {"role": "user", "content": user_question},
    ]

    kwargs = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.1,
    }

    # Attempt JSON mode if the provider supports it
    try:
        kwargs["response_format"] = {"type": "json_object"}
        response = client.chat.completions.create(**kwargs)
    except Exception:
        # Provider doesn't support response_format — fall back to prompt-only
        kwargs.pop("response_format", None)
        response = client.chat.completions.create(**kwargs)

    content = response.choices[0].message.content
    return content if content else ""


# ═══════════════════════════════════════════════════════════════════════════════
#  Runner
# ═══════════════════════════════════════════════════════════════════════════════


def run_structured_output():
    """
    Main runner: exercises live API calls and synthetic malformed inputs,
    then saves all results to data/structured_output_results.json.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
    model_name = os.getenv("OPENAI_MODEL", "openai/gpt-oss-20b")

    if not api_key:
        print("[Error] OPENAI_API_KEY is missing from environment or .env file.")
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=base_url)

    all_results = []

    # ── Part A: Live API calls (Tasks 1-2-4) ──────────────────────────────────
    print("=" * 70)
    print("STRUCTURED OUTPUT — LIVE API CALLS (Tasks 1, 2, 4)")
    print("=" * 70)

    for test in TEST_QUESTIONS:
        qid = test["id"]
        question = test["question"]

        print(f"\n[{qid}] {question}")

        raw_response = call_llm_structured(client, model_name, question)
        print(f"  Raw response: {raw_response!r}")

        result = safe_parse_and_validate(raw_response)

        if result["status"] == "ok":
            print(f"  ✅ Parsed successfully: {result['data']}")
        else:
            print(f"  ❌ Parse/validation error: {result['error']}")

        all_results.append({
            "id": qid,
            "description": test["description"],
            "question": question,
            "raw_response": raw_response,
            "result": result,
        })

    # ── Part B: Synthetic malformed inputs (Tasks 3-4) ────────────────────────
    print("\n" + "=" * 70)
    print("STRUCTURED OUTPUT — MALFORMED INPUT TESTS (Tasks 3, 4)")
    print("=" * 70)

    for case in MALFORMED_TEST_CASES:
        cid = case["id"]
        raw = case["raw"]

        print(f"\n[{cid}] {case['description']}")
        print(f"  Raw input: {raw!r}")

        result = safe_parse_and_validate(raw)

        if result["status"] == "ok":
            print(f"  ✅ Recovered successfully: {result['data']}")
        else:
            print(f"  ❌ Handled gracefully: {result['error']}")

        all_results.append({
            "id": cid,
            "description": case["description"],
            "raw_response": raw,
            "result": result,
        })

    # ── Save everything (Task 5) ──────────────────────────────────────────────
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    output_path = data_dir / "structured_output_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n[Saved] All results exported to: {output_path}")


if __name__ == "__main__":
    run_structured_output()
