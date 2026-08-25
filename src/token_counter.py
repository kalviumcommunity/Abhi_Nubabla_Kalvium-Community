"""
Tokenization, Context Window Measurement, and LLM Cost Estimation Tool.

Tasks Implemented:
- Task 1: Token counting using tiktoken encoding.
- Task 2: Token counts for 3 text samples of varying length (Short, Medium, Long).
- Task 3: Input vs. Output token cost estimation across pricing tiers.
- Task 4: Text length vs. token count relationship analysis across text domains.
- Task 5: Export results to JSON and Markdown reports.
"""

import json
from pathlib import Path
import tiktoken


# ---------------------------------------------------------------------------
# Pricing Tiers (USD per 1,000,000 Tokens)
# ---------------------------------------------------------------------------
PRICING_MODELS = {
    "gpt-4o-mini": {
        "name": "GPT-4o-mini",
        "input_per_1m": 0.15,    # $0.15 per 1M input tokens
        "output_per_1m": 0.60,   # $0.60 per 1M output tokens
    },
    "gpt-4o": {
        "name": "GPT-4o",
        "input_per_1m": 2.50,    # $2.50 per 1M input tokens
        "output_per_1m": 10.00,  # $10.00 per 1M output tokens
    },
}


# ---------------------------------------------------------------------------
# Task 2 Sample Texts (Short, Medium, Long Corpus Samples)
# ---------------------------------------------------------------------------
SAMPLE_1_SHORT = (
    "What is the standard policy for requesting work-from-home or remote work days?"
)

SAMPLE_2_MEDIUM = """Work-from-home (WFH) requests must be submitted through the company's official HR Portal at least two weeks prior to the requested start date. All full-time employees with a minimum of six months of continuous service are eligible, provided their current job responsibilities permit remote operations. Department managers will review requests based on team workload, coverage, and performance metrics before forwarding the application to the HR Remote Work Coordinator for final administrative approval. Approved employees must adhere to core business hours and maintain secure network connectivity at all times."""

SAMPLE_3_LONG = """# Section 4.2: Remote Work & Workplace Flexibility Policy

## 1. Overview & Scope
This policy defines the operational guidelines and security protocols for remote work arrangements within the organization. It applies to all full-time and part-time administrative, technical, and operational personnel. Remote work is a privilege designed to support work-life balance while ensuring organizational productivity, client confidentiality, and data security remain uncompromised.

## 2. Eligibility Requirements
To qualify for regular or hybrid remote work:
- The employee must have completed a minimum of 6 months of continuous full-time employment.
- The employee's latest performance evaluation rating must meet or exceed 'Satisfactory' standards.
- The employee's role must be classified as 'Remote-Eligible' by the Department Head. Roles requiring mandatory physical presence (e.g., facilities maintenance, hardware support, physical security) are excluded.

## 3. Request & Approval Workflow
1. **Submission**: Employees must submit a formal Remote Work Application via the HR Portal at least 14 calendar days prior to the desired effective date.
2. **Managerial Review**: Direct supervisors evaluate the application considering team coverage, project deliverables, and communication plans.
3. **IT Security Verification**: The IT Security Operations team verifies that the employee's designated home office setup satisfies encrypted VPN and multi-factor authentication (MFA) requirements.
4. **HR Registration**: Approved requests are logged into the central employee database, valid for a maximum term of 12 months, subject to annual renewal.

## 4. Technical Equipment & Information Security
- **Company Hardware**: Only company-issued laptops equipped with active Endpoint Detection and Response (EDR) software may be used for remote work.
- **Network Security**: Connecting to public, unencrypted Wi-Fi networks is strictly prohibited. Remote workers must connect exclusively via the corporate AES-256 encrypted VPN tunnel.
- **Data Protection**: Confidential documents must not be printed at remote locations or stored on unapproved personal cloud storage accounts.

## 5. Working Hours & Availability
Remote employees are expected to maintain core operational hours from 9:00 AM to 5:00 PM local time. Employees must remain reachable via official communication channels (Slack, Microsoft Teams, corporate email) during working hours. Any scheduled absence or temporary unavailability must be logged in the shared department calendar.
"""


# ---------------------------------------------------------------------------
# Task 4 Domain Comparison Texts (Prose, Code, Technical Terms, Multilingual)
# ---------------------------------------------------------------------------
DOMAIN_SAMPLES = {
    "Standard English Prose": (
        "The quick brown fox jumps over the lazy dog. Effective communication and documentation "
        "are essential for successful software engineering projects."
    ),
    "Python Code Snippet": (
        "def calculate_total_cost(input_tokens: int, output_tokens: int, rate: float = 0.000015) -> float:\n"
        "    return (input_tokens + output_tokens) * rate\n\n"
        "if __name__ == '__main__':\n"
        "    print(calculate_total_cost(1500, 500))\n"
    ),
    "Dense Technical / Hyphenated Text": (
        "AES-256-GCM-SHA384 microservices infrastructure orchestration hyperparameter optimization "
        "electronegativity subatomic-particle-acceleration asynchronous-event-driven-architecture."
    ),
    "Multilingual / Non-ASCII Text": (
        "リモートワークの申請は人事ポータルから提出してください。 "
        "El trabajo remoto requiere aprobación previa del departamento de recursos humanos. "
        "दूरस्थ कार्य नीति कंपनी के नियमों के अधीन है।"
    ),
}


def get_tokenizer(model_name: str = "gpt-4o"):
    """Returns the tiktoken encoding object for the specified model."""
    try:
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str, tokenizer) -> int:
    """Task 1: Returns exact token count using tiktoken."""
    return len(tokenizer.encode(text))


def calculate_cost(input_tokens: int, output_tokens: int, model_key: str = "gpt-4o-mini") -> dict:
    """
    Task 3: Calculates input, output, and total cost based on model rates per 1M tokens.
    """
    pricing = PRICING_MODELS[model_key]
    input_cost = (input_tokens / 1_000_000) * pricing["input_per_1m"]
    output_cost = (output_tokens / 1_000_000) * pricing["output_per_1m"]
    total_cost = input_cost + output_cost

    return {
        "model_name": pricing["name"],
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_cost_usd": round(input_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "total_cost_usd": round(total_cost, 6),
    }


def analyze_length_token_relationship(tokenizer) -> list:
    """
    Task 4: Demonstrates how text length (characters & words) relates to token count.
    """
    relationship_data = []

    for category, text in DOMAIN_SAMPLES.items():
        char_count = len(text)
        word_count = len(text.split())
        token_cnt = count_tokens(text, tokenizer)

        chars_per_token = round(char_count / token_cnt, 2) if token_cnt > 0 else 0
        words_per_token = round(word_count / token_cnt, 2) if token_cnt > 0 else 0

        relationship_data.append({
            "category": category,
            "char_count": char_count,
            "word_count": word_count,
            "token_count": token_cnt,
            "chars_per_token": chars_per_token,
            "words_per_token": words_per_token,
        })

    return relationship_data


def run_tokenization_analysis():
    """Executes Tasks 1 to 5 and outputs results to console and files."""
    tokenizer = get_tokenizer("gpt-4o")

    print("=" * 75)
    print("TASK 1 & TASK 2: TOKEN COUNT REPORT FOR SAMPLE TEXTS")
    print("=" * 75)

    samples = [
        ("Sample 1 (Short User Query)", SAMPLE_1_SHORT),
        ("Sample 2 (Medium Paragraph Context)", SAMPLE_2_MEDIUM),
        ("Sample 3 (Long RAG Document)", SAMPLE_3_LONG),
    ]

    sample_results = []
    total_corpus_tokens = 0

    for name, text in samples:
        char_cnt = len(text)
        word_cnt = len(text.split())
        token_cnt = count_tokens(text, tokenizer)
        total_corpus_tokens += token_cnt

        res = {
            "sample_name": name,
            "char_count": char_cnt,
            "word_count": word_cnt,
            "token_count": token_cnt,
            "chars_per_token": round(char_cnt / token_cnt, 2),
        }
        sample_results.append(res)

        print(f"\n[{name}]")
        print(f"  • Character Count : {char_cnt}")
        print(f"  • Word Count      : {word_cnt}")
        print(f"  • Token Count     : {token_cnt}")
        print(f"  • Ratio (Chars/Tkn): {round(char_cnt / token_cnt, 2)}")

    # Task 3: Cost Estimation
    print("\n" + "=" * 75)
    print("TASK 3: COST ESTIMATION ACROSS MODEL PRICING TIERS")
    print("=" * 75)

    # Assume a RAG workload ratio: Input tokens (Prompt + Context) vs Output tokens (Response)
    # Scenario: 1,000 queries with 800 input tokens and 150 output tokens per query
    num_queries = 1000
    avg_input_tokens = sample_results[1]["token_count"] + sample_results[0]["token_count"]  # Context + Query (~100 tokens)
    avg_output_tokens = 150  # Typical concise assistant answer length

    total_input = num_queries * avg_input_tokens
    total_output = num_queries * avg_output_tokens

    cost_estimates = {}
    for model_key in PRICING_MODELS:
        est = calculate_cost(total_input, total_output, model_key)
        cost_estimates[model_key] = est

        print(f"\nModel: {est['model_name']} (For {num_queries:,} Queries)")
        print(f"  • Input Tokens  : {total_input:,} (${est['input_cost_usd']:.4f})")
        print(f"  • Output Tokens : {total_output:,} (${est['output_cost_usd']:.4f})")
        print(f"  • Total Cost    : ${est['total_cost_usd']:.4f}")

    # Task 4: Length vs. Token Relationship
    print("\n" + "=" * 75)
    print("TASK 4: LENGTH vs TOKEN COUNT RELATIONSHIP DEMONSTRATION")
    print("=" * 75)

    length_relationship = analyze_length_token_relationship(tokenizer)

    for item in length_relationship:
        print(f"\nDomain: {item['category']}")
        print(f"  • Characters: {item['char_count']} | Words: {item['word_count']} | Tokens: {item['token_count']}")
        print(f"  • Chars/Token: {item['chars_per_token']} | Words/Token: {item['words_per_token']}")

    # Task 5: Exporting Results
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    json_path = data_dir / "token_count_results.json"
    full_output_data = {
        "tokenizer_encoding": "cl100k_base / o200k_base (gpt-4o)",
        "sample_counts": sample_results,
        "cost_estimates_1000_queries": cost_estimates,
        "length_token_relationship": length_relationship,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_output_data, f, indent=2)
    print(f"\n[Saved] Token counts exported to JSON: {json_path}")

    report_path = data_dir / "token_cost_report.md"
    generate_markdown_report(sample_results, cost_estimates, length_relationship, report_path)
    print(f"[Saved] Token cost report exported to Markdown: {report_path}")


def generate_markdown_report(samples, costs, relationship, report_path: Path):
    """Task 5: Formats results into a clean markdown document."""
    md = [
        "# Tokenization & LLM Cost Estimation Report",
        "",
        "This report measures context window usage, evaluates text-length-to-token ratios using `tiktoken`, and calculates RAG assistant costs.",
        "",
        "---",
        "",
        "## 📊 Task 1 & 2: Token Counts for Sample Texts",
        "",
        "| Sample | Characters | Words | Tokens | Chars / Token |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ]

    for s in samples:
        md.append(f"| **{s['sample_name']}** | {s['char_count']} | {s['word_count']} | **{s['token_count']}** | {s['chars_per_token']} |")

    md.extend([
        "",
        "---",
        "",
        "## 💰 Task 3: Cost Estimates (1,000 RAG Workload Queries)",
        "",
        "Scenario: 1,000 queries with ~95 input tokens (context + question) and 150 output tokens per query.",
        "",
        "| Model | Input Tokens | Input Cost ($) | Output Tokens | Output Cost ($) | **Total Cost ($)** |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ])

    for model_key, c in costs.items():
        md.append(
            f"| **{c['model_name']}** | {c['input_tokens']:,} | ${c['input_cost_usd']:.4f} | {c['output_tokens']:,} | ${c['output_cost_usd']:.4f} | **${c['total_cost_usd']:.4f}** |"
        )

    md.extend([
        "",
        "---",
        "",
        "## 🔍 Task 4: Text Length vs. Token Count Relationship",
        "",
        "Character length and word count do **not** scale linearly with token counts across different text types:",
        "",
        "| Domain Category | Characters | Words | Tokens | Chars / Token | Words / Token |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ])

    for r in relationship:
        md.append(
            f"| **{r['category']}** | {r['char_count']} | {r['word_count']} | **{r['token_count']}** | {r['chars_per_token']} | {r['words_per_token']} |"
        )

    md.extend([
        "",
        "### Key Takeaways",
        "1. **English Prose**: Averages ~4 characters per token (0.75 words per token).",
        "2. **Code Snippets & Syntax**: Syntax characters (`:`, `=`, `->`, indentation) create higher token density (~2.5-3 characters per token).",
        "3. **Technical / Hyphenated Words**: Complex compounds break into multiple sub-word tokens (~3.8 characters per token).",
        "4. **Multilingual / Non-ASCII**: Non-Latin scripts require multi-byte UTF-8 token encodings, dramatically increasing token count per character (~1.2-1.8 characters per token).",
    ])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))


if __name__ == "__main__":
    run_tokenization_analysis()
