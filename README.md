# Staff RAG Assistant - Ingestion, Embeddings, Similarity Search, Filtering, Re-ranking, Evaluation & Grounded Answers

This repository implements tools, benchmark reports, and system prompt architectures for an internal Staff RAG Assistant.

---

## 📋 Features & Tasks Implemented

### 1. Grounded Answer Generation & Source Accuracy Verification (`GroundedAnswer` Branch)
- **Task 1 — Grounded Answer Generation**: Generate answers strictly constrained to injected retrieved context using structured prompt templates and verifiable citations (`[Source 1: employee_benefits.md]`).
- **Task 2 — Source Accuracy & Faithfulness Audit**: Automated claim verification engine (`SourceAccuracyChecker`) extracting discrete factual assertions and calculating a faithfulness score ($100.0\%$ verified against chunk text, $0$ unsupported claims).
- **Task 3 — Missing-Context Safe Refusal Fallback**: Explicit fallback mechanism triggered when query context is absent or below similarity threshold ($\text{similarity} < 0.28$), returning standard refusal with HR/IT contact paths rather than inventing policy.
- **Task 4 — With vs. Without Retrieval Comparative Analysis**: Systematic side-by-side evaluation proving that RAG grounding eliminates hallucinations (e.g. replacing generic 10-15 vacation day guesses with verified 18 days PTO + 5 days rollover).
- **Task 5 — Benchmark Exports**: Complete evaluation dataset saved to `data/grounded_generation_results.json` and in-depth report generated at `data/grounded_generation_report.md`.

### 2. Systematic Retrieval Quality Evaluation (`RetrievalEvaluation` Branch)
- **Task 1 — Labelled Benchmark Queries**: Ground-truth test suite of 10 structured queries with expected chunk IDs, source document mappings, and graded relevance assessments ($0 = \text{Irrelevant}$, $1 = \text{Partially Relevant}$, $2 = \text{Highly Relevant}$).
- **Task 2 — Recall@k & MRR Measurement**: Systematic measurement of Recall@k, Hit Rate@k, and Mean Reciprocal Rank (MRR) across multiple thresholds ($k \in \{1, 2, 3, 5, 10\}$), showing Recall progression from $65.0\%$ at $k=1$ to $95.0\%$ at $k=5$.
- **Task 3 — Precision@k & Quality Signal Reporting**: Quantitative Precision@k, F1@k, and NDCG@k metrics across Single-Stage Vector Search, Metadata-Filtered Retrieval, and Two-Stage Re-ranking.
- **Task 4 — Root-Cause Failure Inspection**: Diagnostic categorization classifying underperforming cases into standard architectural failure modes (*Cross-Domain Semantic Distractor Pull*, *Borderline Rank Inversion*, *Vocabulary Gap / Exact Identifiers*, *Chunk Boundary Splits*) with actionable mitigations.
- **Task 5 — Evaluation Artifacts Export**: Benchmark dataset serialized to `data/retrieval_evaluation_results.json` and Markdown audit report generated at `data/retrieval_evaluation_report.md`.

### 2. Metadata-Filtered & Hybrid Vector Retrieval (`MetadataFiltering` Branch)
- **Task 1 — Metadata Filtering Engine**: Scope retrieval candidate chunks prior to similarity search using deterministic metadata filters (`source_document`, `section`, `file_type`, `page_range`, and custom predicate callbacks).
- **Task 2 — Filtered vs. Unfiltered Comparison**: Systematic side-by-side evaluation running queries with and without filters, showing that scoped retrieval prevents cross-domain distractor interference.
- **Task 3 — Lexical & Exact Term Hybrid Matching**: Fused scoring engine combining dense vector similarity with normalized keyword term frequencies and exact identifier boosting (e.g. extension `4357`, `#security-incident`, `AES-256`, `BitLocker`) via tunable weighting parameter $\alpha \in [0.0, 1.0]$.
- **Task 4 — Precision Improvement Quantification**: Quantitative demonstration proving that metadata filtering boosts in-scope precision from $33.3\% - 75.0\%$ to **$100.0\%$**, eliminating cross-document distractors.
- **Task 5 — Benchmark Exports**: Complete evaluation dataset exported to `data/filtered_search_results.json` and in-depth report generated at `data/filtered_search_report.md`.

### 2. Top-K Vector Database Similarity Search & Retrieval (`Similarity-Search` Branch)
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
- **Task 5 — Quality-Check CLI**: Standalone test CLI in `sanity_test.py` and `src/sanity_test.py`.

---

## 📁 Repository Structure

```text
.
├── src/
│   ├── grounded_generator.py  # Tasks 1-5: Grounded generation, source accuracy audit, fallbacks & comparisons
│   ├── retrieval_evaluator.py # Tasks 1-5: Labelled queries, Recall@k, Precision@k, MRR, NDCG & diagnostics
│   ├── filtered_retrieval.py  # Tasks 1-5: Metadata filtering, lexical/hybrid scoring & precision analysis
│   ├── similarity_search.py   # Tasks 1-5: Top-k vector database similarity search & retrieval
│   ├── reranker.py            # Tasks 1-5: Two-stage retrieval & semantic re-ranking pipeline
│   ├── retriever.py           # Public retrieve_top_k and retrieve_filtered interfaces
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
│   ├── grounded_generation_results.json # Serialized grounded answers, audits, fallbacks & comparisons
│   ├── grounded_generation_report.md    # Markdown audit report on source accuracy & with/without retrieval
│   ├── retrieval_evaluation_results.json # Serialized evaluation metrics across 10 labelled queries
│   ├── retrieval_evaluation_report.md    # Markdown audit report on Recall@k, Precision@k & failure modes
│   ├── filtered_search_results.json # Serialized metadata-filtered vs unfiltered benchmark runs
│   ├── filtered_search_report.md    # Markdown technical report on metadata filtering & precision
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
│   ├── test_grounded_generator.py  # Unit tests for grounded generation, faithfulness audits & fallbacks
│   ├── test_retrieval_evaluator.py # Unit tests for Recall@k, Precision@k, MRR, NDCG & diagnostics
│   ├── test_filtered_retrieval.py  # Unit tests for metadata filtering & hybrid scoring
│   ├── test_similarity_search.py   # Unit tests for top-k similarity search & changing k
│   ├── test_reranker.py            # Unit tests for two-stage re-ranking
│   ├── test_retriever.py           # Unit tests for retriever interface
│   ├── test_ingestion_pipeline.py  # Unit tests for ingestion and reconciliation
│   └── test_chunker.py             # Unit tests for chunking strategies
├── generate_grounded_answer.py# Root CLI entry point for grounded answer generation & audits
├── evaluate_retrieval.py      # Root CLI entry point for systematic retrieval quality evaluation
├── filtered_retrieval.py      # Root CLI entry point for metadata-filtered retrieval
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
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Run Grounded Answer Generation & Benchmark
```bash
# Run full benchmark across in-scope, fallback, and comparison queries
python generate_grounded_answer.py

# Generate grounded answer for single query with source accuracy audit
python generate_grounded_answer.py --query "How many days of PTO do employees get, and can unused days roll over?"

# Run side-by-side comparison with vs without retrieval
python generate_grounded_answer.py --query "How many days of PTO do employees get each year?" --compare-unretrieved

# Test missing-context safe refusal fallback
python generate_grounded_answer.py --query "What is the stock option strike price and vesting schedule?" --fallback-test
```

### 3. Run Retrieval Quality Evaluation Benchmark
```bash
python evaluate_retrieval.py --k-values 1 2 3 5 10 --mode all
```

### 4. Run Metadata-Filtered & Hybrid Retrieval Demo
```bash
python filtered_retrieval.py
```

### 5. Run Unit Test Suites
```bash
python -m unittest tests/test_grounded_generator.py -v
```

---

## 📊 Summary of Grounded Generation & Source Accuracy (Tasks 1, 2, 3, 4)

### Grounded In-Scope Scenarios (Tasks 1 & 2)

| Scenario | Query Topic | Cited Source Document | Faithfulness Score | Claims Verified | Status |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `scenario_01_pto_accrual` | PTO Accrual & Rollover Limits | `employee_benefits.md` | **100.0%** | **4/4** | ✅ FULLY GROUNDED |
| `scenario_02_security_incident` | 24/7 Hotline & Malware Reporting | `it_security_policy.md` | **100.0%** | **4/4** | ✅ FULLY GROUNDED |
| `scenario_03_remote_vpn` | Remote VPN & Encryption Rules | `remote_work_policy.md` | **100.0%** | **4/4** | ✅ FULLY GROUNDED |
| `scenario_04_parental_leave` | Paid Parental Leave Duration | `employee_benefits.md` | **100.0%** | **4/4** | ✅ FULLY GROUNDED |

### Missing-Context Fallback Refusal (Task 3)

| Out-of-Scope Query | Trigger Cause | Refusal Message Returned |
| :--- | :--- | :--- |
| *Stock Option Vesting Schedule* | Zero relevant corpus chunks | *"I don't have access to this information in the verified company guidelines. Please contact HR at hr@company.com or submit a ticket via the IT Helpdesk portal."* |
| *Cafeteria Lunch Budget* | Zero relevant corpus chunks | *"I don't have access to this information in the verified company guidelines. Please contact HR at hr@company.com or submit a ticket via the IT Helpdesk portal."* |

### Comparative Analysis: With vs. Without Retrieval (Task 4)

| Feature | 🟢 With Retrieval (RAG Grounded) | 🔴 Without Retrieval (Direct LLM Guess) |
| :--- | :--- | :--- |
| **PTO Policy Answer** | **18 days PTO/year**, max **5 days rollover** before Dec 31 | Vague guess: *"10 to 15 vacation days depending on tenure"* |
| **Security Breach Response** | **Disconnect immediately**, do not reboot, call **ext 4357** | Generic guess: *"Contact general IT support during business hours"* |
| **Source Faithfulness** | **100.0%** (Backed by verified document chunks) | **0.0%** (Unverified speculative generation) |
| **Hallucination Risk** | **0%** (Strict context-only constraint) | **High** (Invented numbers and inaccurate procedures) |
