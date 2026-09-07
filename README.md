# Staff RAG Assistant - Ingestion, Chunking, Embeddings, Top-K Retrieval & Grounding Verification

This repository implements tools, benchmark reports, and system prompt architectures for an internal Staff RAG Assistant.

---

## 📋 Features & Tasks Implemented

### 1. Top-K Vector Store Retrieval & Grounding Step
- **Task 1 — Embed User Query**: Transform natural language user queries into continuous 1536-dimensional normalized vectors ($\|\mathbf{q}\|_2 = 1.0$) matching the corpus chunk embedding geometry.
- **Task 2 — Top-K Similarity Search**: Query the indexed vector store using Cosine Similarity ($\cos \theta = \mathbf{q} \cdot \mathbf{c}$) and extract the $k$ highest-scoring chunks.
- **Task 3 — Scores & Rich Metadata Enrichment**: Format retrieved chunks with similarity scores, unique chunk IDs, source document names, section breadcrumb hierarchies, page numbers, character/token offsets, and raw source text.
- **Task 4 — Changing $k$ Comparative Analysis**: Evaluate multi-$k$ retrieval configurations ($k=2$ vs. $k=3$ vs. $k=5$) to benchmark the precision vs. recall trade-off, token budget consumption, and grounding coverage for downstream LLM prompts.
- **Task 5 — JSON & Markdown Artifacts**: Complete benchmark dataset exported to `data/retrieval_results.json` and comprehensive technical grounding report saved to `data/retrieval_report.md`.

### 2. Retrieval Sanity-Testing & Known-Relevance Verification
- **Task 1 — Known Relevance Dataset**: Curated ground-truth test cases covering PTO rollover, parental leave, password MFA, RAG chunking, and remote VPN rules.
- **Task 2 — Rank & Margin Verification**: Automatic verification that target chunks rank above unrelated baselines with large positive score margins ($\Delta \ge +0.56$).
- **Task 3 — Borderline / Edge-Case Diagnostic**: Deep-dive analysis of fixed-window chunk boundary splits (`it_security_policy_chunk_003` vs `004`), proving why structure-aware chunking is critical.
- **Task 4 — Sanity Test Reports**: Export of full verification results to `data/sanity_test_results.json` and formatted report to `data/sanity_report.md`.
- **Task 5 — Quality-Check CLI**: Standalone test CLI in `sanity_test.py` and `src/sanity_test.py`.

### 2. Document Chunking Strategies (`Chunking-Strategies` Branch)
- **Task 1 — Split Using Defined Strategies**: Implementation of three distinct chunking algorithms in `src/chunker.py`:
  - **Fixed-Size with Overlap (Sliding Window)** (400 chars, 80 char overlap)
  - **Sentence-Based Chunking** (Max 100 tokens, 1 sentence overlap)
  - **Paragraph / Structure-Aware Chunking** (Section hierarchy preservation, complete policy lists, max 220 tokens)
- **Task 2 — Strategy Comparison**: Side-by-side boundary and coherence comparison on identical corpus documents (`data/corpus/`).
- **Task 3 — Statistical Reporting**: Quantitative metrics including chunk counts, mean/min/max token and character sizes, standard deviations, and overlap overhead percentages exported to `data/chunking_stats.json`.
- **Task 4 — Strategy Justification**: Technical evaluation demonstrating why **Paragraph / Structure-Aware Chunking** is optimal for staff policy and procedure retrieval (preventing fragmented bullet points and maintaining context without overlap bloat).
- **Task 5 — Sample Chunks & Verification**: Serialized sample chunks with exact boundary offsets exported to `data/sample_chunks.json` and documented in `data/chunk_comparison_report.md`.

### 3. Text Extraction Cleaning Pipeline (`Text-Extraction-Cleaning-Pipeline` Branch)
- **Task 1 — Remove Boilerplate**: Automatic stripping of repeated headers, footers, page numbers ("Page X of Y"), breadcrumbs ("Home > HR > Policies"), legal disclaimers, and section dividers.
- **Task 2 — Normalise Whitespace & Encoding**: Unicode NFKC normalization, ligatures repair (`ﬁ` $\rightarrow$ `fi`), removal of soft hyphens and zero-width spaces, mid-sentence and hyphenated line break unwrapping, horizontal/vertical space collapsing.
- **Task 3 — Apply Consistently Across Corpus**: Uniform batch processing engine running identical cleaning stages across all documents in `data/raw_documents/`.
- **Task 4 — Show Before/After Evidence**: Detailed reports (`data/cleaning_report.md`, `data/cleaning_results.json`) featuring side-by-side comparative text snippets and token reduction metrics via `tiktoken`.
- **Task 5 — Commit with Sample Output**: Exported clean document files saved to `data/cleaned_documents/` ready for vector retrieval.

### 4. Text Embeddings & Semantic Similarity Demonstration
- **Task 1 — Generate Embeddings**: Dense continuous embeddings generation for short sample texts across HR leave queries, policy chunks, and unrelated infrastructure/ML domains.
- **Task 2 — Vector Dimension Verification**: Automatic verification confirming that every sample text yields an embedding of identical length ($D = 1536$).
- **Task 3 — Cosine Similarity Comparison**: Measurement and validation proving that semantically similar query-paraphrase and query-context pairs score significantly higher than unrelated topics.
- **Task 4 — Conceptual Explanation**: Architectural explanation of why embeddings represent geometric semantic meaning rather than random IDs or sparse keyword counts.
- **Task 5 — Artifact Exports**: Automatic export of structured results to `data/embedding_results.json` and comprehensive markdown report to `data/embedding_report.md`.

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

### 7. Tokenization & Cost Estimation (`Tokenization-Cost-Estimation` Branch)
- **Task 1 — Token Counting with Tiktoken**: Token counting module built using OpenAI's `tiktoken` tokenizer (`cl100k_base` / `o200k_base`).
- **Task 2 — Sample Token Counts**: Benchmark reports measuring token usage across short user queries, medium paragraph contexts, and long employee handbook documents.
- **Task 3 — Cost Estimation Engine**: Differential input vs. output token cost calculation supporting multiple pricing tiers (`GPT-4o-mini`, `GPT-4o`).
- **Task 4 — Length–Token Relationship Analysis**: Empirical analysis demonstrating why character/word count does not map 1:1 to tokens across plain prose, code syntax, technical jargon, and multilingual text.
- **Task 5 — Report Generation & Exports**: Automated export of JSON data to `data/token_count_results.json` and formatted markdown report to `data/token_cost_report.md`.

---

## 📁 Repository Structure

```text
.
├── src/
│   ├── retriever.py           # Tasks 1-5: Top-K Vector Store Retriever & dynamic k comparison
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
│   ├── retrieval_report.md    # Comprehensive Markdown report of Top-K retrieval & k-comparisons
│   ├── retrieval_results.json # Full JSON dataset of Top-K retrieved chunks with scores & metadata
│   ├── sanity_report.md       # Markdown summary of sanity test passes, margins & diagnostics
│   ├── sanity_test_results.json # Full JSON dataset of sanity test runs and scores
│   ├── similarity_ranking_report.md # Markdown report of top-k and bottom-k chunk rankings
│   ├── similarity_ranking_results.json # Full JSON dataset of query rankings and scores
│   ├── embedding_report.md    # Markdown summary of embeddings, shapes & similarity comparisons
│   ├── embedding_results.json # JSON dataset of embeddings, previews & similarity matrix
│   ├── corpus/                # Multi-format corpus documents (.md, .pdf, .html, .txt)
│   ├── ingestion_summary.json # Ingestion accounting summary & completeness proof
│   ├── ingested_chunks.json   # Full repository of tagged chunks with metadata
│   ├── ingestion_report.md    # Markdown ingestion audit report & boundary inspection
│   ├── chunking_stats.json    # JSON dataset of chunk counts, size distributions & std dev
│   ├── sample_chunks.json     # Serialized sample chunks with boundary metadata
│   ├── chunk_comparison_report.md # Side-by-side chunk boundary report
│   ├── raw_documents/         # Raw, noisy extracted document corpus
│   ├── cleaned_documents/     # Cleaned, retrieval-ready document corpus
│   ├── cleaning_report.md     # Before/after comparative cleaning report
│   ├── cleaning_results.json  # JSON dataset with metrics & text diffs
│   ├── token_cost_report.md   # Markdown summary of token counts & cost estimates
│   ├── token_count_results.json # JSON dataset of token counts & ratios
│   ├── comparison_report.md   # Side-by-side prompt output comparison report
│   └── structured_output_results.json # Sample parsed JSON outputs
├── prompt/
│   ├── templates.py           # Shared named-placeholder templates and renderer
│   ├── example_renders.md     # Example filled prompts for chat and batch paths
│   └── chosen_prompt.md       # Documentation for chosen system prompt
├── tests/
│   ├── test_retriever.py      # Unit tests for Top-K Vector Store Retriever & k-invariance
│   ├── test_ingestion_pipeline.py # Unit tests for ingestion and reconciliation
│   ├── test_chunker.py        # Unit tests for chunking strategies
│   └── test_token_aware_chunker.py # Unit tests for token-aware chunker
├── retriever.py               # Root CLI entry point for Top-K Vector Store Retriever
├── sanity_test.py             # Root CLI entry point for retrieval sanity tests
├── similarity_ranking.py      # Root CLI entry point for similarity ranking demo
├── embedding_demo.py          # Root CLI entry point for embedding demonstration
├── document_loader.py         # Multi-format loader CLI tool
├── trace_demo.py              # Chunk-to-source traceability demo
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

### 2. Run Top-K Vector Store Retrieval & Multi-K Analysis
```bash
# Run default retrieval suite (k=3 with k=2, 3, 5 comparisons)
python retriever.py

# Run retrieval for a custom user query with specific k
python retriever.py --query "What is the policy on roll over of unused PTO?" -k 3

# Run custom multi-k comparison
python retriever.py --query "What are the VPN and encryption protocols?" --compare-k 2 4 6
```

### 3. Run Retrieval Sanity Verification Test Suite
```bash
python sanity_test.py
```

### 4. Run Query-Chunk Similarity Ranking Demo
```bash
python similarity_ranking.py --query "What is the policy for 16 weeks parental leave?"
```

### 5. Run Text Embeddings Demonstration
```bash
python embedding_demo.py
```

### 6. Run Full Ingestion Pipeline & Completeness Validation
```bash
python src/ingestion_pipeline.py
```

### 7. Run All Test Suites
```bash
python -m unittest discover -s tests -p "*.py" -v
```

---

## 📊 Summary of Top-K Retrieval & Grounding Evaluation

| Sample Query | Domain | Top Grounding Chunk ID | Top Score | k=2 Token Budget | k=5 Token Budget | Grounding Decision |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **PTO Rollover & Accrual** | HR Benefits | `employee_benefits_chunk_001` | **`0.8066`** | 139 tokens | 408 tokens | ✅ Direct Grounding |
| **Security Incident Hotline** | IT Security | `it_security_policy_chunk_003` | **`0.7026`** | 208 tokens | 338 tokens | ✅ Direct Grounding |
| **Remote VPN & Encryption** | Remote Work | `remote_work_policy_chunk_005` | **`0.7605`** | 185 tokens | 426 tokens | ✅ Direct Grounding |
| **Parental Leave Blocks** | HR Benefits | `employee_benefits_chunk_003` | **`0.7695`** | 134 tokens | 320 tokens | ✅ Direct Grounding |

**Key Takeaway on Changing $k$**:
- **$k=2$ to $k=3$**: Ideal for targeted prompt injection. High signal-to-noise ratio, average similarity $> 0.60$, minimal token overhead ($\le 250$ tokens).
- **$k=5$**: Maximizes context recall for multi-part synthesis across adjacent policy documents, while keeping total context below $450$ tokens.