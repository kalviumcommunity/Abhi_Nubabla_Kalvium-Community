# Retrieval Settings Tuning & Relevance Benchmark Report

**Embedding Model / Engine**: `OpenAI-Compatible API (text-embedding-3-small)`  
**Total Test Queries Evaluated**: `5`  
**Recommended Configuration**: `Config A: Baseline (k=5, Threshold=0.0)`  

---

## 1. Best Configuration Selection & Justification

> **Chosen Setting**: `Config A: Baseline (k=5, Threshold=0.0)`  
**Empirical Results**: Achieved a **Top-1 Hit Rate of 60.0%**, **Recall@5 of 100.0%**, and an **MRR of 0.7167**.  
**Rationale**: By setting `k=5` with a minimum score threshold of `0.0`, the retriever eliminates low-similarity false-positive chunks while reducing prompt context token overhead by **50%** compared to k=10.

---

## 2. Configuration Comparison Matrix

| Configuration | Top-1 Hit Rate | Top-K Hit Rate | MRR | Avg Tokens / Query | Avg Top Score |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Config A: Baseline (k=5, Threshold=0.0) [BEST]** | `60.0%` | `100.0%` | `0.7167` | `338.0` | `0.5563` |
| **Config B: High-Precision (k=3, Threshold=0.35)** | `40.0%` | `60.0%` | `0.4667` | `119.4` | `0.6200` |
| **Config C: Domain-Filtered (k=3, Threshold=0.20, Markdown Filter)** | `60.0%` | `80.0%` | `0.7000` | `184.4` | `0.5429` |
| **Config D: Broad Recall (k=10, Threshold=0.10)** | `60.0%` | `100.0%` | `0.7167` | `641.4` | `0.5563` |

---

## 3. Test Queries & Expected Target Chunks

| Query ID | Topic | Query Text | Target Chunk ID | Expected Source |
| :--- | :--- | :--- | :--- | :--- |
| **test_q1_pto** | HR - Paid Time Off (PTO) & Leave Limits | *"How many days of paid time off do employees get each year, a..."* | `employee_benefits_chunk_001` | `employee_benefits.md` |
| **test_q2_vpn** | Remote Work - Network Encryption & VPN Rules | *"What are the network encryption and VPN requirements for con..."* | `remote_work_policy_chunk_005` | `remote_work_policy.md` |
| **test_q3_password** | IT Security - Password Length & Authentication | *"What are the minimum password length requirements and is SMS..."* | `it_security_policy_chunk_001` | `it_security_policy.md` |
| **test_q4_parental** | HR - Parental Leave Entitlement | *"How many weeks of fully paid leave are new parents entitled ..."* | `employee_benefits_chunk_003` | `employee_benefits.md` |
| **test_q5_rag_principles** | RAG Architecture - Ingestion & Chunking Principles | *"How does the RAG document loader transform mixed-format file..."* | `guide_chunk_002` | `guide_document.md` |

---

## 4. Per-Query Relevance Breakdown (Best Configuration)

| Query ID | Expected Target | Rank Found | Top-1 Hit | Top-K Hit | Reciprocal Rank | Top Similarity Score |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **test_q1_pto** | `employee_benefits_chunk_001` | `Rank 1` | `Yes` | `Yes` | `1.0000` | `0.5269` |
| **test_q2_vpn** | `remote_work_policy_chunk_005` | `Rank 4` | `No` | `Yes` | `0.2500` | `0.6856` |
| **test_q3_password** | `it_security_policy_chunk_001` | `Rank 1` | `Yes` | `Yes` | `1.0000` | `0.3016` |
| **test_q4_parental** | `employee_benefits_chunk_003` | `Rank 1` | `Yes` | `Yes` | `1.0000` | `0.4797` |
| **test_q5_rag_principles** | `guide_chunk_002` | `Rank 3` | `No` | `Yes` | `0.3333` | `0.7877` |
