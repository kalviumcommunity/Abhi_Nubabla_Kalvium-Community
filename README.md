# Staff RAG Assistant - Tokenization, Ingestion, Embeddings, Similarity Search & Retrieval

This repository implements tools, benchmark reports, and system prompt architectures for an internal Staff RAG Assistant.

---

## 📋 Features & Tasks Implemented

### 1. Top-K Vector Database Similarity Search & Retrieval (`Similarity-Search` Branch)
- **Task 1 — Query Embedding**: Embeds user queries using the identical 1536-dimensional embedding model and normalization scale as the indexed corpus chunks (`data/embedded_chunks.json`).
- **Task 2 — Top-K Vector Search**: Computes cosine similarities ($\mathbf{q} \cdot \mathbf{c}_i$) against the indexed vector database and retrieves the top-$k$ most relevant chunks.
- **Task 3 — Scores & Metadata Inclusion**: Every retrieved chunk includes similarity scores, cleaned source text, source document path, section breadcrumb, chunk position, page number, and token counts.
- **Task 4 — Changing $k$ Demonstration**: Benchmarks queries across $k=1$, $k=3$, and $k=5$, demonstrating the trade-off between precision (low token cost at $k=1$) and recall (broader context with score drop-off at $k=5$).
- **Task 5 — Query Results Export**: Serialized benchmark outputs saved to `data/similarity_search_results.json` and human-readable audit report to `data/similarity_search_report.md`.

### 2. Full Corpus Ingestion & Completeness Validation (`Corpus-Preparation` Branch)
- **Task 1 — End-to-End Pipeline**: Multi-format ingestion pipeline (`src/ingestion_pipeline.py`) supporting `.md`, `.pdf`, `.html`, and `.txt` files with automated text cleaning and structure-aware chunking.
- **Task 2 — Ingestion Summary Report**: Comprehensive accounting of total source documents, successfully ingested files, chunk counts, token totals, and structured error logs exported to `data/ingestion_summary.json` and `data/ingestion_report.md`.
- **Task 3 — Completeness Validation**: Mathematical reconciliation proving zero silent drops ($$\text{Total} = \text{Ingested} + \text{Failures} + \text{Skipped}$$) with failure detection for corrupted files (e.g. `corrupt.pdf`).
- **Task 4 — Sample Chunks Inspection**: Serialized chunks with breadcrumb section headers, page numbers, character offsets, and `tiktoken` counts exported to `data/ingested_chunks.json`.
- **Task 5 — Integration Tests & Commit**: Full test suite (`tests/test_ingestion_pipeline.py`) verifying 100% document accounting and error boundary isolation.

### 3. Document Chunking Strategies (`Chunking-Strategies` Branch)
- **Task 1 — Split Using Defined Strategies**: Implementation of three distinct chunking algorithms in `src/chunker.py`:
  - **Fixed-Size with Overlap (Sliding Window)** (400 chars, 80 char overlap)
  - **Sentence-Based Chunking** (Max 100 tokens, 1 sentence overlap)
  - **Paragraph / Structure-Aware Chunking** (Section hierarchy preservation, complete policy lists, max 220 tokens)
- **Task 2 — Strategy Comparison**: Side-by-side boundary and coherence comparison on identical corpus documents (`data/corpus/`).
- **Task 3 — Statistical Reporting**: Quantitative metrics including chunk counts, mean/min/max token and character sizes, standard deviations, and overlap overhead percentages exported to `data/chunking_stats.json`.
- **Task 4 — Strategy Justification**: Technical evaluation demonstrating why **Paragraph / Structure-Aware Chunking** is optimal for staff policy and procedure retrieval (preventing fragmented bullet points and maintaining context without overlap bloat).
- **Task 5 — Sample Chunks & Verification**: Serialized sample chunks with exact boundary offsets exported to `data/sample_chunks.json` and documented in `data/chunk_comparison_report.md`.

### 4. Text Extraction Cleaning Pipeline (`Text-Extraction-Cleaning-Pipeline` Branch)
- **Task 1 — Remove Boilerplate**: Automatic stripping of repeated headers, footers, page numbers ("Page X of Y"), breadcrumbs ("Home > HR > Policies"), legal disclaimers, and section dividers.
- **Task 2 — Normalise Whitespace & Encoding**: Unicode NFKC normalization, ligatures repair (`ﬁ` $\rightarrow$ `fi`), removal of soft hyphens and zero-width spaces, mid-sentence and hyphenated line break unwrapping, horizontal/vertical space collapsing.
- **Task 3 — Apply Consistently Across Corpus**: Uniform batch processing engine running identical cleaning stages across all documents in `data/raw_documents/`.
- **Task 4 — Show Before/After Evidence**: Detailed reports (`data/cleaning_report.md`, `data/cleaning_results.json`) featuring side-by-side comparative text snippets and token reduction metrics via `tiktoken`.
- **Task 5 — Commit with Sample Output**: Exported clean document files saved to `data/cleaned_documents/` ready for vector retrieval.

### 5. Query-Chunk Similarity Ranking & Retrieval
- **Task 1 — Similarity Metrics**: Implementation of Cosine Similarity, Euclidean Distance ($L_2$), and Dot Product for vector similarity evaluation.
- **Task 2 — Query-to-Chunk Evaluation**: Systematic comparison of domain queries (PTO, Incident Response, Remote VPN, RAG Loader) against the corpus chunk repository.
- **Task 3 — Ranking & Result Segmentation**: Dynamic sorting and presentation of Top-K (most relevant) vs. Bottom-K (orthogonal/least relevant) chunks with rich metadata.
- **Task 4 — Metric Selection Justification**: Architectural rationale for Cosine Similarity based on length invariance, bounded $[-1.0, 1.0]$ ranges, and dot product equivalence on unit spheres.
- **Task 5 — Benchmark Exports**: Automated export of ranking runs to `data/similarity_ranking_results.json` and formatted report to `data/similarity_ranking_report.md`.

### 6. Retrieval Sanity-Testing & Known-Relevance Verification
- **Task 1 — Known Relevance Dataset**: Curated ground-truth test cases covering PTO rollover, parental leave, password MFA, RAG chunking, and remote VPN rules.
- **Task 2 — Rank & Margin Verification**: Automatic verification that target chunks rank above unrelated baselines with large positive score margins ($\Delta \ge +0.56$).
- **Task 3 — Borderline / Edge-Case Diagnostic**: Deep-dive analysis of fixed-window chunk boundary splits (`it_security_policy_chunk_003` vs `004`), proving why structure-aware chunking is critical.
- **Task 4 — Sanity Test Reports**: Export of full verification results to `data/sanity_test_results.json` and formatted report to `data/sanity_report.md`.
- **Task 5 — Quality-Check CLI**: Standalone test CLI in `sanity_test.py` and `src/sanity_test.py`.

---

## 📁 Repository Structure

```text
.
├── src/
│   ├── similarity_search.py   # Tasks 1-5: Top-k vector database similarity search & retrieval
│   ├── retriever.py           # Public retrieve_top_k interface for RAG generation
│   ├── sanity_test.py         # Tasks 1-5: Retrieval sanity tests & ground-truth verification
│   ├── similarity_ranking.py  # Tasks 1-5: Query-to-chunk similarity ranking & retrieval
│   ├── embedding_demo.py      # Tasks 1-5: Text embedding generation, dimensionality & similarity
│   ├── ingestion_pipeline.py  # Tasks 1-5: Full ingestion pipeline & completeness validation
│   ├── chunker.py             # Tasks 1-5: Modular chunking engine & benchmark runner
│   ├── cleaning_pipeline.py   # Tasks 1-5: Text extraction cleaning pipeline
│   ├── token_counter.py       # Tasks 1-5: Token counting & cost estimation engine
│   ├── prompts.py             # System prompt definitions & test scenarios
│   ├── compare_prompts.py     # Prompt engineering benchmark runner
│   └── structured_output.py   # JSON response format mode & Pydantic validation
├── data/
│   ├── similarity_search_results.json # Serialized query retrieval runs for k=1, 3, 5
│   ├── similarity_search_report.md    # Markdown similarity search report with changing k
│   ├── embedded_chunks.json   # Vector store with 1536-D embeddings & metadata
│   ├── sanity_report.md       # Markdown summary of sanity test passes, margins & diagnostics
│   ├── sanity_test_results.json # Full JSON dataset of sanity test runs and scores
│   ├── similarity_ranking_report.md # Markdown report of top-k and bottom-k chunk rankings
│   ├── similarity_ranking_results.json # Full JSON dataset of query rankings and scores
│   ├── corpus/                # Multi-format corpus documents (.md, .pdf, .html, .txt)
│   ├── ingestion_summary.json # Ingestion accounting summary & completeness proof
│   ├── ingested_chunks.json   # Full repository of tagged chunks with metadata
│   ├── ingestion_report.md    # Markdown ingestion audit report & boundary inspection
│   ├── chunking_stats.json    # JSON dataset of chunk counts, size distributions & std dev
│   ├── sample_chunks.json     # Serialized sample chunks with boundary metadata
│   ├── chunk_comparison_report.md # Side-by-side chunk boundary report
│   ├── token_cost_report.md   # Markdown summary of token counts & cost estimates
│   ├── token_count_results.json # JSON dataset of token counts & ratios
│   └── structured_output_results.json # Sample parsed JSON outputs
├── prompt/
│   ├── templates.py           # Shared named-placeholder templates and renderer
│   ├── example_renders.md     # Example filled prompts for chat and batch paths
│   └── chosen_prompt.md       # Documentation for chosen system prompt
├── tests/
│   ├── test_similarity_search.py  # Unit tests for top-k similarity search & changing k
│   ├── test_ingestion_pipeline.py # Unit tests for ingestion and reconciliation
│   └── test_chunker.py        # Unit tests for chunking strategies
├── similarity_search.py       # Root CLI entry point for top-k similarity search
├── sanity_test.py             # Root CLI entry point for retrieval sanity tests
├── similarity_ranking.py      # Root CLI entry point for similarity ranking demo
├── embedding_demo.py          # Root CLI entry point for embedding demonstration
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

### 2. Run Top-K Similarity Search & Changing K Demo
```bash
python similarity_search.py
# or with specific k values:
python similarity_search.py --k-values 1 3 5 10
```

### 3. Programmatic Retrieval in Python
```python
from src.retriever import retrieve_top_k

# Retrieve top 3 relevant chunks for a question
chunks = retrieve_top_k("What are the PTO rollover rules?", k=3)
for chunk in chunks:
    print(f"Rank {chunk.rank} | Score: {chunk.score} | Doc: {chunk.metadata['source_document']}")
    print(chunk.source_text)
```

### 4. Run Retrieval Sanity Verification Test Suite
```bash
python sanity_test.py
```

### 5. Run Full Ingestion Pipeline & Completeness Validation
```bash
python src/ingestion_pipeline.py
```

### 6. Run All Test Suites
```bash
python -m unittest discover -s tests -p "*.py" -v
```

---

## 📊 Summary of Changing $k$ Retrieval Findings

| Query Intent | $k=1$ (Precision) | $k=3$ (Balanced) | $k=5$ (Recall) | Top Retrieved Document & Section |
| :--- | :---: | :---: | :---: | :--- |
| **PTO Accrual & Rollover** | Score: **0.5269** (79 toks) | Scores: **0.5269 – 0.2352** (219 toks) | Scores: **0.5269 – 0.1981** (366 toks) | `employee_benefits.md` > *1. Paid Time Off (PTO) Accrual* |
| **IT Incident Reporting** | Score: **0.5100** (112 toks) | Scores: **0.5100 – 0.4138** (287 toks) | Scores: **0.5100 – 0.3115** (453 toks) | `it_security_policy.md` > *4. Incident Reporting Procedure* |
| **Remote Work VPN Rules** | Score: **0.6856** (89 toks) | Scores: **0.6856 – 0.6311** (250 toks) | Scores: **0.6856 – 0.5339** (407 toks) | `remote_work_policy.md` > *3. Request & Approval Workflow* |
| **RAG Ingestion Principles** | Score: **0.7877** (61 toks) | Scores: **0.7877 – 0.6883** (128 toks) | Scores: **0.7877 – 0.5425** (211 toks) | `hello.txt` & `guide.md` > *RAG Architecture* |