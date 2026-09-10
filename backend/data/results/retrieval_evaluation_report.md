# Systematic RAG Retrieval Quality Evaluation & Diagnostic Audit

## 1. Executive Summary & Evaluation Framework

This report establishes an empirical evaluation framework for the Staff RAG Assistant retrieval engine. Rather than assuming retrieval quality, this framework measures **Recall@k**, **Precision@k**, **Mean Reciprocal Rank (MRR)**, and **NDCG@k** across a labelled ground-truth query suite, while diagnosing failure modes to guide production tuning.

### Key Framework Specifications:
- **Labelled Benchmark Queries**: 10 ground-truth test cases across HR, IT Security, Remote Work, and Engineering.
- **Evaluated Values of $k$**: 1, 2, 3, 5, 10
- **Retrieval Architectures Evaluated**: Single-Stage Vector Search, Metadata-Filtered Retrieval, Two-Stage Semantic Re-ranking.
- **Evaluation Timestamp**: `2026-09-07T14:06:42.794203`

---

## 2. Global Metric Summary by Retrieval Architecture

| Retrieval Pipeline Mode | MRR | HitRate@3 | Recall@3 | Precision@3 | F1@3 | NDCG@3 | Recall@5 | Precision@5 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Direct Vector Search (Baseline)** | **0.7950** | **80.0%** | 80.0% | 33.3% | 0.4600 | 0.6787 | 95.0% | 24.0% |
| **2. Metadata-Filtered Retrieval** | **0.7667** | **70.0%** | 65.0% | 26.7% | 0.3700 | 0.6301 | 85.0% | 20.0% |
| **3. Two-Stage Re-ranked Retrieval** | **0.8700** | **90.0%** | 80.0% | 30.0% | 0.4300 | 0.6857 | 85.0% | 20.0% |

---

## 3. Recall@k & Precision@k Progression Curve (Direct Vector Search)

| Parameter $k$ | Mean Recall@k | Mean Precision@k | Mean Hit Rate@k | Mean F1@k | Mean NDCG@k | Context Token Tradeoff |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **k=1** | **65.0%** | 70.0% | 70.0% | 0.6667 | 0.6333 | Ultra-low token budget (~75 tokens), zero distractor overhead, risk of missing supporting chunks. |
| **k=2** | **75.0%** | 45.0% | 80.0% | 0.5500 | 0.6662 | Compact context (~150 tokens), high precision for single-chunk queries. |
| **k=3** | **80.0%** | 33.3% | 80.0% | 0.4600 | 0.6787 | Optimal balance (~240 tokens), captures primary and secondary policy clauses. |
| **k=5** | **95.0%** | 24.0% | 100.0% | 0.3762 | 0.7498 | High recall (~380 tokens), introduces lower-scoring adjacent distractors. |
| **k=10** | **100.0%** | 13.0% | 100.0% | 0.2273 | 0.7808 | Maximum recall (~700 tokens), significant noise and prompt token bloat. |

---

## 4. Per-Query Breakdown & Relevance Judgements (Tasks 1, 2, 3)

| Query ID | Domain | Difficulty | First Relevant Rank | Recall@3 | Precision@3 | NDCG@3 | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `eval_q01_pto_rollover` | HR & Employee Benefits | Easy | **#1** | 100.0% | 33.3% | 1.0000 | ✅ PASS (Rank #1) |
| `eval_q02_sick_leave_policy` | HR & Employee Benefits | Easy | **#1** | 100.0% | 33.3% | 0.8262 | ✅ PASS (Rank #1) |
| `eval_q03_parental_leave` | HR & Employee Benefits | Easy | **#1** | 100.0% | 33.3% | 0.8262 | ✅ PASS (Rank #1) |
| `eval_q04_incident_reporting_hotline` | IT Security & Compliance | Medium | **#1** | 100.0% | 66.7% | 0.7003 | ✅ PASS (Rank #1) |
| `eval_q05_password_mfa_rules` | IT Security & Compliance | Easy | **#1** | 100.0% | 33.3% | 0.8262 | ✅ PASS (Rank #1) |
| `eval_q06_remote_vpn_encryption` | Remote Work Policy | Medium | **#4** | 0.0% | 0.0% | 0.1527 | ❌ MISS |
| `eval_q07_remote_work_eligibility` | Remote Work Policy | Easy | **#1** | 100.0% | 33.3% | 1.0000 | ✅ PASS (Rank #1) |
| `eval_q08_rag_system_loader` | Engineering & Architecture | Medium | **#2** | 100.0% | 66.7% | 0.6291 | ⚠️ BORDERLINE (Rank #2-3) |
| `eval_q09_borderline_incident_slas` | IT Security & Compliance | Hard/Borderline | **#1** | 100.0% | 33.3% | 0.8262 | ✅ PASS (Rank #1) |
| `eval_q10_cross_domain_distractor` | Cross-Domain Synthesis | Hard/Borderline | **#5** | 0.0% | 0.0% | 0.0000 | ❌ MISS |

---

## 5. Failure Case Inspection & Diagnostic Root-Cause Analysis (Task 4)

The evaluation script automatically inspected all non-optimal and borderline query runs to identify underlying pipeline bottlenecks:

### Diagnostic #1: `eval_q06_remote_vpn_encryption`
- **User Query**: *"What network encryption and VPN tunnel protocols are required when connecting remotely to corporate infrastructure?"*
- **First Relevant Rank**: **#4** (Top distractor: `remote_work_policy_chunk_003` from `remote_work_policy.md`)
- **Expected Relevant Chunks**: `['remote_work_policy_chunk_005']`
- **Root-Cause Category**: **`Cross-Domain Semantic Distractor Pull`**
- **Detailed Finding**: Dense embeddings for query 'What network encryption and VPN tunnel protoc...' overlapped with adjacent policy files (`remote_work_policy.md`), pulling irrelevant distractor `remote_work_policy_chunk_003` to Rank #1.
- **Recommended Mitigation**: 💡 *Apply pre-retrieval MetadataFilter(source_document='...') to eliminate cross-document interference.*

### Diagnostic #2: `eval_q08_rag_system_loader`
- **User Query**: *"How does the RAG document loader module ingest multi-format files and format page-by-page text extraction?"*
- **First Relevant Rank**: **#2** (Top distractor: `hello_chunk_001` from `hello.txt`)
- **Expected Relevant Chunks**: `['document_chunk_001', 'guide_chunk_001']`
- **Root-Cause Category**: **`Borderline Rank Inversion (Rank #2 or #3)`**
- **Detailed Finding**: The target chunk `document_chunk_001` was retrieved in top-3, but ranked #2 behind general overview chunk `hello_chunk_001` from `hello.txt`.
- **Recommended Mitigation**: 💡 *Use Two-Stage Re-ranking (Cross-Encoder / SemanticRelevanceReranker) to boost deep semantic alignment over broad surface similarity.*

### Diagnostic #3: `eval_q10_cross_domain_distractor`
- **User Query**: *"Can employees take leave for wellness or gym activities while working remotely from home?"*
- **First Relevant Rank**: **#5** (Top distractor: `remote_work_policy_chunk_002` from `remote_work_policy.md`)
- **Expected Relevant Chunks**: `['employee_benefits_chunk_004', 'remote_work_policy_chunk_001']`
- **Root-Cause Category**: **`Cross-Domain Semantic Distractor Pull`**
- **Detailed Finding**: Dense embeddings for query 'Can employees take leave for wellness or gym ...' overlapped with adjacent policy files (`remote_work_policy.md`), pulling irrelevant distractor `remote_work_policy_chunk_002` to Rank #1.
- **Recommended Mitigation**: 💡 *Apply pre-retrieval MetadataFilter(source_document='...') to eliminate cross-document interference.*

---

## 6. Production Recommendations for Retrieval Tuning

1. **Adopt Two-Stage Retrieval as Production Default**: Two-stage retrieval achieved the highest MRR and NDCG@3 by pulling a broader candidate window ($k=10$) and re-scoring with lexical-semantic cross-attention.
2. **Use Pre-Filtering on Known Domains**: For user queries initiated from specific portal views (e.g. Employee HR Portal), apply metadata pre-filtering to eliminate 100% of out-of-domain cross-policy distractors.
3. **Hybrid Exact Term Matching for Security Policies**: Phone numbers, Slack channels (`#security-incident`), and security protocols (`AES-256`, `BitLocker`) must leverage hybrid lexical boosting (alpha=0.30) to guarantee top rank.
