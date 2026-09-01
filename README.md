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

---

### 3. Text Embeddings & Semantic Similarity Demonstration
- **Task 1 — Generate Embeddings**: Dense continuous embeddings generation for short sample texts across HR leave queries, policy chunks, and unrelated infrastructure/ML domains.
- **Task 2 — Vector Dimension Verification**: Automatic verification confirming that every sample text yields an embedding of identical length ($D = 1536$).
- **Task 3 — Cosine Similarity Comparison**: Measurement and validation proving that semantically similar query-paraphrase and query-context pairs score significantly higher than unrelated topics.
- **Task 4 — Conceptual Explanation**: Architectural explanation of why embeddings represent geometric semantic meaning rather than random IDs or sparse keyword counts.
- **Task 5 — Artifact Exports**: Automatic export of structured results to `data/embedding_results.json` and comprehensive markdown report to `data/embedding_report.md`.

---

## 📁 Repository Structure

```text
.
├── src/
│   ├── embedding_demo.py      # Text embedding generation, dimensionality verification & cosine similarity
│   ├── token_counter.py       # Tiktoken token counting & cost estimation engine
│   ├── prompts.py             # System prompt definitions & test scenarios
│   ├── compare_prompts.py     # Prompt engineering benchmark runner
│   └── structured_output.py   # Structured JSON responses with Pydantic validation
├── data/
│   ├── embedding_report.md    # Markdown summary of embeddings, shapes & similarity comparisons
│   ├── embedding_results.json # JSON dataset of embeddings, previews & similarity matrix
│   ├── token_cost_report.md   # Markdown summary of token counts & cost estimates
│   ├── token_count_results.json# JSON dataset of token counts & length-token ratios
│   ├── comparison_report.md   # Side-by-side prompt output comparison report
│   └── comparison_results.json# Raw LLM benchmark results
├── prompt/
│   ├── templates.py           # Shared named-placeholder templates and renderer
│   ├── example_renders.md     # Example filled prompts for chat and batch paths
│   └── chosen_prompt.md       # Documentation for chosen system prompt
├── embedding_demo.py          # Root CLI entry point for embedding demonstration
├── document_loader.py         # Multi-format document loader with metadata tagging
├── trace_demo.py              # Chunk-to-source traceability demo
├── .env.example               # Template environment variables
├── .gitignore                 # Git ignore configuration
├── main.py                    # Application entry point for LLM chat requests
├── requirements.txt           # Project dependencies (openai, tiktoken, rich, etc.)
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

### 2. Run Text Embeddings Demonstration (Tasks 1–5)
```bash
python embedding_demo.py
# or
python src/embedding_demo.py
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

### 5. Run Prompt Benchmark Comparison
```bash
python src/compare_prompts.py
```

### 6. Run Main Application
```bash
python main.py
```

---

## 📊 Summary of Embeddings & Semantic Similarity Findings

| Comparison Pair | Domain Relationship | Expected | Cosine Similarity | Result |
| :--- | :--- | :---: | :---: | :--- |
| **Text A vs. Text B** | Paraphrased Query (Vacation vs. Time Off) | `HIGH` | **`0.7199`** | ✅ High Semantic Match |
| **Text A vs. Text C** | Query vs. HR Portal Policy Chunk | `HIGH` | **`0.6704`** | ✅ High Semantic Match |
| **Text A vs. Text D** | Vacation Query vs. AWS Cloud DB Migration | `LOW` | **`-0.0034`** | ✅ Orthogonal / Dissimilar |
| **Text A vs. Text E** | Vacation Query vs. CNN Image Tensors | `LOW` | **`-0.0037`** | ✅ Orthogonal / Dissimilar |

**Key Takeaway**: Continuous vector embeddings map concepts into geometric space where meaning translates directly to directional proximity, allowing RAG pipelines to match user intent even with zero keyword overlap.

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