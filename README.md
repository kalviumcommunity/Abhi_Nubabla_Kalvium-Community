# Staff RAG Assistant - Tokenization, Prompt Engineering, Structured Output & Document Chunking

This repository implements tools, benchmark reports, and system prompt architectures for an internal Staff RAG Assistant.

---

## 📋 Features & Tasks Implemented

### 1. Document Chunking Strategies (`Chunking-Strategies` Branch)
- **Task 1 — Split Using Defined Strategies**: Implementation of three distinct chunking algorithms in `src/chunker.py`:
  - **Fixed-Size with Overlap (Sliding Window)** (400 chars, 80 char overlap)
  - **Sentence-Based Chunking** (Max 100 tokens, 1 sentence overlap)
  - **Paragraph / Structure-Aware Chunking** (Section hierarchy preservation, complete policy lists, max 220 tokens)
- **Task 2 — Strategy Comparison**: Side-by-side boundary and coherence comparison on identical corpus documents (`data/corpus/`).
- **Task 3 — Statistical Reporting**: Quantitative metrics including chunk counts, mean/min/max token and character sizes, standard deviations, and overlap overhead percentages exported to `data/chunking_stats.json`.
- **Task 4 — Strategy Justification**: Technical evaluation demonstrating why **Paragraph / Structure-Aware Chunking** is optimal for staff policy and procedure retrieval (preventing fragmented bullet points and maintaining context without overlap bloat).
- **Task 5 — Sample Chunks & Verification**: Serialized sample chunks with exact boundary offsets exported to `data/sample_chunks.json` and documented in `data/chunk_comparison_report.md`.

### 2. Tokenization & Cost Estimation (`Tokenization-Cost-Estimation` Branch)
- **Task 1 — Token Counting with Tiktoken**: Token counting module built using OpenAI's `tiktoken` tokenizer (`cl100k_base` / `o200k_base`).
- **Task 2 — Sample Token Counts**: Benchmark reports measuring token usage across short user queries, medium paragraph contexts, and long employee handbook documents.
- **Task 3 — Cost Estimation Engine**: Differential input vs. output token cost calculation supporting multiple pricing tiers (`GPT-4o-mini`, `GPT-4o`).
- **Task 4 — Length–Token Relationship Analysis**: Empirical analysis demonstrating why character/word count does not map 1:1 to tokens across plain prose, code syntax, technical jargon, and multilingual text.
- **Task 5 — Report Generation & Exports**: Automated export of JSON data to `data/token_count_results.json` and formatted markdown report to `data/token_cost_report.md`.

### 3. System Prompt Engineering (`Prompt-Construction` Branch)
- **Distinct System & User Roles**: Standardized Chat Completion payload structures (`system` behavior vs. `user` query).
- **Constrained System Prompt**: Explicit Role definition, In/Out-of-Scope boundaries, length limits (<150 words / max 4 bullet points), and deterministic safety fallback redirecting to `hr@company.com`.
- **Empirical Prompt Benchmark**: Side-by-side comparison of baseline vague system prompt vs. constrained prompt.

---

## 📁 Repository Structure

```text
.
├── src/
│   ├── chunker.py             # Tasks 1-5: Modular chunking engine, stats calculator & benchmark runner
│   ├── token_counter.py       # Tiktoken token counting & cost estimation engine
│   ├── structured_output.py   # Structured JSON parsing and validation module
│   ├── prompts.py             # System prompt definitions & test scenarios
│   └── compare_prompts.py     # Prompt engineering benchmark runner
├── data/
│   ├── corpus/                # Cleaned markdown documents for chunking benchmarks
│   │   ├── remote_work_policy.md
│   │   ├── it_security_policy.md
│   │   └── employee_benefits.md
│   ├── chunking_stats.json    # JSON dataset of chunk counts, size distributions & std dev
│   ├── sample_chunks.json     # Serialized sample chunks with boundary metadata
│   ├── chunk_comparison_report.md # Side-by-side chunk boundary report & strategy justification
│   ├── token_cost_report.md   # Markdown summary of token counts & cost estimates
│   ├── token_count_results.json # JSON dataset of token counts & length-token ratios
│   ├── comparison_report.md   # Side-by-side prompt output comparison report
│   └── comparison_results.json # Raw LLM benchmark results
├── prompt/
│   ├── templates.py            # Shared named-placeholder templates and renderer
│   ├── example_renders.md      # Example filled prompts for chat and batch paths
│   └── chosen_prompt.md        # Documentation for chosen system prompt
├── tests/
│   └── test_chunker.py        # Automated unit tests for chunking strategies
├── .env.example               # Template environment variables
├── .gitignore                 # Git ignore configuration
├── main.py                    # Application entry point for LLM chat requests
├── requirements.txt           # Project dependencies (openai, tiktoken, rich, pydantic)
└── README.md                  # Project overview & documentation
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

### 2. Run Chunking Benchmark & Report Generation (Tasks 1–5)
```bash
python src/chunker.py
```

### 3. Run Chunking Unit Tests
```bash
python -m unittest tests/test_chunker.py -v
```

### 4. Run Token Counting & Cost Estimation
```bash
python src/token_counter.py
```

### 5. Run Prompt Benchmark Comparison
```bash
python src/compare_prompts.py
```

### 6. Run Main Application
```bash
python main.py
```

---

## 📊 Summary of Chunking Strategies Findings

| Strategy | Total Chunks | Avg Tokens / Chunk | Avg Chars / Chunk | Overlap Overhead (%) | Best Suited For |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Fixed-Size (Chars)** | 23 | 71.5 | 370.6 | +21.2% | Unstructured, homogeneous text without formatting |
| **Sentence-Based** | 20 | 83.2 | 429.0 | +21.8% | Narrative prose & transcripts |
| **Paragraph / Structure-Aware** ⭐ *(Chosen)* | 13 | 115.5 | 587.1 | +10.9% | Policy documents, handbooks, numbered workflows |

### 🎯 Strategy Decision: Paragraph / Structure-Aware Chunking
- **Zero List Fragmentation**: Keeps eligibility bullet points and numbered procedures contiguous in single chunks.
- **Section Breadcrumbs**: Prepends section hierarchy (e.g. `[Section 4.2 > 2. Eligibility Requirements]`) for standalone context in vector retrieval.
- **Context Efficiency**: Optimal chunk sizes (~80–160 tokens) that fit into prompt templates without redundant token bloat.