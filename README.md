# Staff RAG Assistant - Tokenization, Prompt Engineering & Cost Estimation

This repository implements tools, benchmark reports, and system prompt architectures for an internal Staff RAG Assistant.

---

## 📋 Features & Tasks Implemented

### 1. Tokenization & Cost Estimation (`Tokenization-Cost-Estimation` Branch)
- **Task 1 — Token Counting with Tiktoken**: Token counting module built using OpenAI's `tiktoken` tokenizer (`cl100k_base` / `o200k_base`).
- **Task 2 — Sample Token Counts**: Benchmark reports measuring token usage across short user queries, medium paragraph contexts, and long employee handbook documents.
- **Task 3 — Cost Estimation Engine**: Differential input vs. output token cost calculation supporting multiple pricing tiers (`GPT-4o-mini`, `GPT-4o`).
- **Task 4 — Length–Token Relationship Analysis**: Empirical analysis demonstrating why character/word count does not map 1:1 to tokens across plain prose, code syntax, technical jargon, and multilingual text.
- **Task 5 — Report Generation & Exports**: Automated export of JSON data to `data/token_count_results.json` and formatted markdown report to `data/token_cost_report.md`.

### 2. System Prompt Engineering (`Prompt-Construction` Branch)
- **Distinct System & User Roles**: Standardized Chat Completion payload structures (`system` behavior vs. `user` query).
- **Constrained System Prompt**: Explicit Role definition, In/Out-of-Scope boundaries, length limits (<150 words / max 4 bullet points), and deterministic safety fallback redirecting to `hr@company.com`.
- **Empirical Prompt Benchmark**: Side-by-side comparison of baseline vague system prompt vs. constrained prompt.

### 3. Text Extraction Cleaning Pipeline (`Text-Extraction-Cleaning-Pipeline` Branch)
- **Task 1 — Remove Boilerplate**: Automatic stripping of repeated headers, footers, page numbers ("Page X of Y"), breadcrumbs ("Home > HR > Policies"), legal disclaimers, and section dividers.
- **Task 2 — Normalise Whitespace & Encoding**: Unicode NFKC normalization, ligatures repair (`ﬁ` $\rightarrow$ `fi`), removal of soft hyphens and zero-width spaces, mid-sentence and hyphenated line break unwrapping, horizontal/vertical space collapsing.
- **Task 3 — Apply Consistently Across Corpus**: Uniform batch processing engine running identical cleaning stages across all documents in `data/raw_documents/`.
- **Task 4 — Show Before/After Evidence**: Detailed reports (`data/cleaning_report.md`, `data/cleaning_results.json`) featuring side-by-side comparative text snippets and token reduction metrics via `tiktoken`.
- **Task 5 — Commit with Sample Output**: Exported clean document files saved to `data/cleaned_documents/` ready for vector retrieval.

---

## 📁 Repository Structure

```text
.
├── src/
│   ├── token_counter.py          # Token counting & cost estimation engine
│   ├── prompts.py                # System prompt definitions & test scenarios
│   ├── compare_prompts.py        # Prompt engineering benchmark runner
│   ├── structured_output.py     # JSON response format mode & Pydantic validation
│   └── cleaning_pipeline.py    # Tasks 1-5: Text extraction cleaning pipeline
├── data/
│   ├── raw_documents/            # Raw, noisy extracted document corpus
│   ├── cleaned_documents/        # Cleaned, retrieval-ready document corpus
│   ├── cleaning_report.md        # Before/after comparative cleaning report
│   ├── cleaning_results.json     # JSON dataset with metrics & text diffs
│   ├── token_cost_report.md      # Markdown summary of token counts & cost estimates
│   ├── token_count_results.json   # JSON dataset of token counts & ratios
│   ├── comparison_report.md      # Side-by-side prompt output comparison report
│   └── structured_output_results.json # Sample parsed JSON outputs
├── prompt/
│   ├── templates.py               # Shared named-placeholder templates
│   ├── example_renders.md         # Example filled prompts
│   └── chosen_prompt.md           # Documentation for chosen system prompt
├── .env.example                  # Template environment variables
├── main.py                       # Application entry point for LLM chat requests
├── requirements.txt              # Project dependencies
└── README.md                     # Project overview & documentation
```

---

## 🚀 Usage & Execution Instructions

### 1. Environment Setup
```bash
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Run Text Extraction Cleaning Pipeline (Tasks 1–5)
```bash
python src/cleaning_pipeline.py
```

### 3. Reusable Prompt Templates
```python
from prompt.templates import render_rag_request

prompt = render_rag_request(
	context="The remote-work policy permits two remote days per week.",
	question="How many remote days can I request?",
)
```

The interactive chat and parameter-experiment batch feature both use this same
`{context}`/`{question}` template. See `prompt/example_renders.md` for complete
rendered examples.

### 4. Run Token Counting & Cost Estimation
```bash
python src/token_counter.py
```

### 5. Run Structured Output Parser
```bash
python src/structured_output.py
```

### 6. Run Main Application
```bash
python main.py
```

---

## 📊 Summary of Tokenization Findings

| Sample / Domain | Characters | Words | Tokens | Chars / Token | Words / Token |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Short Query** | 78 | 12 | 15 | 5.20 | 0.80 |
| **Medium Paragraph** | 612 | 87 | 100 | 6.12 | 0.87 |
| **Long Document** | 2,542 | 351 | 476 | 5.34 | 0.74 |
| **Python Code** | 218 | 23 | 60 | 3.63 | 0.38 |
| **Multilingual Text** | 157 | 21 | 43 | 3.65 | 0.49 |

### 💰 Cost Estimate Summary (1,000 RAG Workload Queries)
- **GPT-4o-mini**: $0.1072 total ($0.0173 input + $0.0900 output)
- **GPT-4o**: $1.7875 total ($0.2875 input + $1.5000 output)