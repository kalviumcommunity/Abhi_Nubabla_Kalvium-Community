# Staff RAG Assistant - Tokenization, Prompt Engineering, Structured Output, Chunking & Ingestion Pipeline

This repository implements tools, benchmark reports, and system prompt architectures for an internal Staff RAG Assistant.

---

## 📋 Features & Tasks Implemented

### 1. Full Corpus Ingestion & Completeness Validation (`Corpus-Preparation` Branch)
- **Task 1 — End-to-End Pipeline**: Multi-format ingestion pipeline (`src/ingestion_pipeline.py`) supporting `.md`, `.pdf`, `.html`, and `.txt` files with automated text cleaning and structure-aware chunking.
- **Task 2 — Ingestion Summary Report**: Comprehensive accounting of total source documents, successfully ingested files, chunk counts, token totals, and structured error logs exported to `data/ingestion_summary.json` and `data/ingestion_report.md`.
- **Task 3 — Completeness Validation**: Mathematical reconciliation proving zero silent drops ($$\text{Total} = \text{Ingested} + \text{Failures} + \text{Skipped}$$) with failure detection for corrupted files (e.g. `corrupt.pdf`).
- **Task 4 — Sample Chunks Inspection**: Serialized chunks with breadcrumb section headers, page numbers, character offsets, and `tiktoken` counts exported to `data/ingested_chunks.json`.
- **Task 5 — Integration Tests & Commit**: Full test suite (`tests/test_ingestion_pipeline.py`) verifying 100% document accounting and error boundary isolation.

### 2. Document Chunking Strategies (`Chunking-Strategies` Branch)
- **Task 1 — Split Using Defined Strategies**: Implementation of three distinct chunking algorithms in `src/chunker.py`:
  - **Fixed-Size with Overlap (Sliding Window)** (400 chars, 80 char overlap)
  - **Sentence-Based Chunking** (Max 100 tokens, 1 sentence overlap)
  - **Paragraph / Structure-Aware Chunking** (Section hierarchy preservation, complete policy lists, max 220 tokens)
- **Task 2 — Strategy Comparison**: Side-by-side boundary and coherence comparison on identical corpus documents (`data/corpus/`).
- **Task 3 — Statistical Reporting**: Quantitative metrics including chunk counts, mean/min/max token and character sizes, standard deviations, and overlap overhead percentages exported to `data/chunking_stats.json`.
- **Task 4 — Strategy Justification**: Technical evaluation demonstrating why **Paragraph / Structure-Aware Chunking** is optimal for staff policy and procedure retrieval (preventing fragmented bullet points and maintaining context without overlap bloat).
- **Task 5 — Sample Chunks & Verification**: Serialized sample chunks with exact boundary offsets exported to `data/sample_chunks.json` and documented in `data/chunk_comparison_report.md`.

### 3. Tokenization & Cost Estimation (`Tokenization-Cost-Estimation` Branch)
- **Task 1 — Token Counting with Tiktoken**: Token counting module built using OpenAI's `tiktoken` tokenizer (`cl100k_base` / `o200k_base`).
- **Task 2 — Sample Token Counts**: Benchmark reports measuring token usage across short user queries, medium paragraph contexts, and long employee handbook documents.
- **Task 3 — Cost Estimation Engine**: Differential input vs. output token cost calculation supporting multiple pricing tiers (`GPT-4o-mini`, `GPT-4o`).
- **Task 4 — Length–Token Relationship Analysis**: Empirical analysis demonstrating why character/word count does not map 1:1 to tokens across plain prose, code syntax, technical jargon, and multilingual text.
- **Task 5 — Report Generation & Exports**: Automated export of JSON data to `data/token_count_results.json` and formatted markdown report to `data/token_cost_report.md`.

### 4. System Prompt Engineering (`Prompt-Construction` Branch)
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
│   ├── ingestion_pipeline.py  # Tasks 1-5: Full ingestion pipeline & completeness validation
│   ├── chunker.py             # Modular chunking engine & benchmark runner
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
│   ├── chunker.py             # Tasks 1-5: Modular chunking engine, stats calculator & benchmark runner
│   ├── token_counter.py       # Tiktoken token counting & cost estimation engine
│   ├── structured_output.py   # Structured JSON parsing and validation module
│   ├── prompts.py             # System prompt definitions & test scenarios
│   ├── compare_prompts.py     # Prompt engineering benchmark runner
│   └── structured_output.py   # JSON response format mode & Pydantic validation
├── data/
│   ├── corpus/                # Multi-format corpus documents (.md, .pdf, .html, .txt)
│   ├── ingestion_summary.json # Ingestion accounting summary & completeness proof
│   ├── ingested_chunks.json   # Full repository of tagged chunks with metadata
│   ├── ingestion_report.md    # Markdown ingestion audit report & boundary inspection
│   ├── chunking_stats.json    # JSON dataset of chunk counts, size distributions & std dev
│   ├── sample_chunks.json     # Serialized sample chunks with boundary metadata
│   ├── chunk_comparison_report.md # Side-by-side chunk boundary report
│   ├── token_cost_report.md   # Markdown summary of token counts & cost estimates
│   ├── token_count_results.json # JSON dataset of token counts & length-token ratios
│   ├── comparison_report.md   # Side-by-side prompt output comparison report
│   └── comparison_results.json # Raw LLM benchmark results
├── prompt/
│   ├── templates.py            # Shared named-placeholder templates and renderer
│   ├── example_renders.md      # Example filled prompts for chat and batch paths
│   └── chosen_prompt.md        # Documentation for chosen system prompt
├── tests/
│   ├── test_ingestion_pipeline.py # Unit tests for ingestion and reconciliation
│   └── test_chunker.py        # Unit tests for chunking strategies
├── document_loader.py         # Multi-format loader CLI tool
├── .env.example               # Template environment variables
├── .gitignore                 # Git ignore configuration
├── main.py                    # Application entry point for LLM chat requests
├── requirements.txt           # Project dependencies (openai, tiktoken, rich, pydantic, pypdf, bs4)
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

### 2. Run Full Ingestion Pipeline & Completeness Validation
```bash
python src/ingestion_pipeline.py
# or using document_loader.py:
python document_loader.py data/corpus --validate
```

### 3. Run All Test Suites
```bash
python -m unittest discover -s tests -p "*.py" -v
```

### 4. Run Document Chunking Strategies Benchmark
```bash
python src/chunker.py
python src/structured_output.py
```

### 5. Run Token Counting & Cost Estimation
```bash
python src/token_counter.py
```

---

## 📊 Summary of Ingestion & Completeness Findings

| Metric | Value | Audit / Reconciliation Result |
| :--- | :---: | :--- |
| **Total Discovered Documents** | **8** | 100% of files scanned in `data/corpus/` |
| **Successfully Ingested** | **7** | Cleaned, chunked, and tagged without errors |
| **Recorded Failures** | **1** | `corrupt.pdf` caught and audited (`PdfStreamError`) |
| **Silent Drops** | **0** | Mathematical proof verified |
| **Total Chunks Created** | **25** | Tagged with section, page, position, tokens |
| **Total Ingested Tokens** | **1,470** | Tiktoken `cl100k_base` measurement |
| **Reconciliation Status** | **PASSED** | `8 Total == 7 Ingested + 1 Failures + 0 Skipped` |
