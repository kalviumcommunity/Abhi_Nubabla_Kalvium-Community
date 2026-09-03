# Top-K Vector Database Similarity Search & Retrieval Report

**Run Timestamp**: `2026-09-03T13:24:55.850266`  
**Vector Store**: `data/embedded_chunks.json` (25 chunks indexed)  
**Embedding Model**: `DenseSemanticEmbedder (Local Fallback, D=1536)`  
**Values of $k$ Tested**: `1, 3, 5`  

---

## 🔍 Task 4: Demonstration of Changing $k$ (Precision vs. Recall)

Retrieval in RAG systems balances **precision** against **recall**:
- **$k=1$ (High Precision)**: Fetches only the single highest-scoring chunk. Minimizes LLM prompt token consumption, but risks missing secondary conditions or adjacent procedural steps.
- **$k=3$ (Balanced - Recommended)**: Provides primary policy context plus supporting clauses and workflows, maintaining high average relevance while remaining concise.
- **$k=5$ (High Recall)**: Encompasses broader document context, but introduces lower similarity scores and consumes significantly more context tokens.

### Score & Context Progression Across $k$

| Query ID | $k$ | Chunks | Top Score | Lowest Score | Score Spread | Total Tokens | Top Source Document |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `query_pto_rollover` | **1** | 1 | **0.5269** | 0.5269 | 0.0000 | 79 | `employee_benefits.md` |
| `query_pto_rollover` | **3** | 3 | **0.5269** | 0.2352 | 0.2917 | 219 | `employee_benefits.md` |
| `query_pto_rollover` | **5** | 5 | **0.5269** | 0.1981 | 0.3288 | 366 | `employee_benefits.md` |
| `query_security_incident` | **1** | 1 | **0.5100** | 0.5100 | 0.0000 | 112 | `it_security_policy.md` |
| `query_security_incident` | **3** | 3 | **0.5100** | 0.4138 | 0.0962 | 287 | `it_security_policy.md` |
| `query_security_incident` | **5** | 5 | **0.5100** | 0.3115 | 0.1985 | 453 | `it_security_policy.md` |
| `query_remote_vpn` | **1** | 1 | **0.6856** | 0.6856 | 0.0000 | 89 | `remote_work_policy.md` |
| `query_remote_vpn` | **3** | 3 | **0.6856** | 0.6311 | 0.0545 | 250 | `remote_work_policy.md` |
| `query_remote_vpn` | **5** | 5 | **0.6856** | 0.5339 | 0.1517 | 407 | `remote_work_policy.md` |
| `query_rag_principles` | **1** | 1 | **0.7877** | 0.7877 | 0.0000 | 61 | `hello.txt` |
| `query_rag_principles` | **3** | 3 | **0.7877** | 0.6883 | 0.0994 | 128 | `hello.txt` |
| `query_rag_principles` | **5** | 5 | **0.7877** | 0.5425 | 0.2453 | 211 | `hello.txt` |

---

## 📋 Detailed Query Inspections (Tasks 1, 2, 3)

### Query: "How many days of paid time off do employees get each year, and can unused PTO be rolled over?"
- **Category**: HR Policy & Paid Time Off
- **Intent**: Retrieve policy rules regarding annual PTO accrual limits and December 31 rollover rules.

#### Retrieved Chunks at $k=3$:

##### Rank 1: `employee_benefits_chunk_001` (Score: **0.5269**)
- **Document**: `employee_benefits.md`
- **Section**: `Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 1. Paid Time Off (PTO) Accrual`
- **Page**: `N/A`
- **Chunk Index**: `68`
- **Token Count**: `79`
```text
Full-time regular employees accrue 18 days of Paid Time Off annually, calculated at a rate of 1.5 days per completed calendar month of active service. Employees may roll over a maximum of 5 unused PTO days into the following calendar year. Any unused balance exceeding 5 days on December 31 will expire without cash compensation, unless an exception is approved by HR due to operational necessity.
```

---

### Query: "What is the procedure for reporting a suspected malware infection or active data compromise?"
- **Category**: IT Security & Incident Response
- **Intent**: Retrieve step-by-step reporting protocols and the 24/7 IT Security hotline phone extension.

#### Retrieved Chunks at $k=3$:

##### Rank 1: `it_security_policy_chunk_005` (Score: **0.5100**)
- **Document**: `it_security_policy.md`
- **Section**: `Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure`
- **Page**: `N/A`
- **Chunk Index**: `1785`
- **Token Count**: `112`
```text
If you suspect an active security compromise, credential theft, or phishing email:
1. Immediately disconnect your machine from the network (unplug Ethernet or turn off Wi-Fi).
2. Do not power off or reboot the computer, as volatile RAM evidence must be preserved for forensic analysis.
3. Call the 24/7 IT Security Hotline at extension 4357 (HELP) or alert the `#security-incident` Slack channel using a secondary mobile device.
4. Provide the time of occurrence, observed system symptoms, and suspicious email headers or files involved.
```

---

### Query: "What are the network encryption and VPN requirements for connecting remotely to company resources?"
- **Category**: Workplace Flexibility & Remote Work
- **Intent**: Retrieve VPN AES-256 encryption requirements and prohibition of public Wi-Fi.

#### Retrieved Chunks at $k=3$:

##### Rank 1: `remote_work_policy_chunk_003` (Score: **0.6856**)
- **Document**: `remote_work_policy.md`
- **Section**: `Section 4.2: Remote Work & Workplace Flexibility Policy > 3. Request & Approval Workflow`
- **Page**: `N/A`
- **Chunk Index**: `1054`
- **Token Count**: `89`
```text
1. **Submission**: Employees must submit a formal Remote Work Application via the HR Portal at least 14 calendar days prior to the desired effective date.
2. **Managerial Review**: Direct supervisors evaluate the application considering team coverage, project deliverables, and communication plans within 5 business days.
3. **IT Security Verification**: The IT Security Operations team verifies that the employee's designated home office setup satisfies encrypted VPN and multi-factor
```

---

### Query: "How does the RAG document loader transform mixed-format files and semantic chunk units for retrieval?"
- **Category**: Engineering & RAG Architecture
- **Intent**: Retrieve documentation on multi-format extraction and semantic chunking.

#### Retrieved Chunks at $k=3$:

##### Rank 1: `hello_chunk_001` (Score: **0.7877**)
- **Document**: `hello.txt`
- **Section**: `N/A`
- **Page**: `N/A`
- **Chunk Index**: `0`
- **Token Count**: `61`
```text
Welcome to the RAG Document Loader test.
This is a plain text file that contains unstructured information.
It is designed to be loaded by our document loader and parsed into plain text.
RAG systems need simple text format to compute embeddings and search for matching chunks.
This concludes the plain text sample file.
```

---

## 📦 Task 5: Exported Deliverables Summary

- **JSON Query Results**: `data/similarity_search_results.json`
- **Markdown Retrieval Report**: `data/similarity_search_report.md`
- **Retriever Python Module**: `src/similarity_search.py` & `src/retriever.py`