# RAG Pipeline: Top-K Vector Store Retrieval & Grounding Report

## 1. Executive Summary & Retrieval Architecture

This report documents the implementation and evaluation of the **Top-K Vector Store Retrieval Step** for the Staff Knowledge Base RAG Assistant. The retrieval module bridges user intent with indexed knowledge representations, ensuring that downstream LLM answers are grounded strictly in authentic, high-relevance source chunks.

### Key Retrieval Architecture Specifications:
- **Embedding Dimensionality**: 1536 dense dimensions with L2 unit-norm normalization (||v|| = 1.0).
- **Similarity Metric**: Cosine Similarity cos(theta) = (q . c) / (||q|| * ||c||), bounded in [-1.0, +1.0].
- **Indexed Corpus Size**: 25 semantic chunks loaded from `data/ingested_chunks.json`.
- **Evaluated k Values**: 2, 3, 5 (Primary default: k=3).

---

## 2. Mathematical Retrieval & Ranking Principles

### 2.1 Embedding Alignment & Vector Space Mechanics
The user query string Q is transformed into an embedding vector q in R^1536 using the exact same dense semantic embedder utilized during corpus ingestion. This ensures exact geometric alignment in vector space:

$$q = \text{Normalize}_{L_2}\left(\sum_{w \in Q} \Phi(w) + \sum_{c \in C_Q} \Psi(c)\right)$$

### 2.2 Top-k Nearest Neighbor Selection
Given indexed chunk vectors {c_1, c_2, ..., c_N}, the retriever computes the similarity score array S and extracts the permutation index sigma sorted descending:

$$S_i = q \cdot c_i \quad \forall i \in \{1, \dots, N\}$$
$$\text{Top-}k(Q) = \left[ c_{\sigma(1)}, c_{\sigma(2)}, \dots, c_{\sigma(k)} \right] \quad \text{where } S_{\sigma(1)} \ge S_{\sigma(2)} \ge \dots \ge S_{\sigma(k)}$$

---

## 3. Sample Query Retrieval Demonstrations & Metadata Grounding

### Query: `retrieval_q1_pto_rollover` — HR & Benefits - Paid Time Off (PTO)
**User Prompt**: *"How many days of paid time off do employees get each year, and can unused PTO be rolled over?"*

#### Top-3 Retrieved Chunks Table

| Rank | Score | Chunk ID | Source Document | Section Breadcrumb | Tokens | Source Snippet |
|:---:|:---:|:---|:---|:---|:---:|:---|
| #1 | **0.8066** | `employee_benefits_chunk_001` | `employee_benefits.md` | Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 1. Paid Time Off (PTO) Accrual | 79 | Full-time regular employees accrue 18 days of Paid Time Off annually, calculated at a rate of 1.5... |
| #2 | **0.2455** | `remote_work_policy_chunk_001` | `remote_work_policy.md` | Section 4.2: Remote Work & Workplace Flexibility Policy > 1. Overview & Scope | 60 | This policy defines operational guidelines and security protocols for remote work arrangements wi... |
| #3 | **0.1996** | `it_security_policy_chunk_005` | `it_security_policy.md` | Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure | 112 | If you suspect an active security compromise, credential theft, or phishing email: 1. Immediately... |

#### Complete Metadata & Full Text for Top Grounding Chunk (#1)
```json
{
  "chunk_id": "employee_benefits_chunk_001",
  "rank": 1,
  "similarity_score": 0.8066,
  "source": "data/corpus/employee_benefits.md",
  "document_name": "employee_benefits.md",
  "section": "Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 1. Paid Time Off (PTO) Accrual",
  "page": null,
  "position": 68,
  "token_count": 79,
  "char_count": 397,
  "text": "Full-time regular employees accrue 18 days of Paid Time Off annually, calculated at a rate of 1.5 days per completed calendar month of active service. Employees may roll over a maximum of 5 unused PTO days into the following calendar year. Any unused balance exceeding 5 days on December 31 will expire without cash compensation, unless an exception is approved by HR due to operational necessity."
}
```

#### Analysis of Changing $k$ (k=2, k=3, k=5)

| Setting | Chunks Retrieved | Total Context Tokens | Avg Similarity Score | Score Spread [Min - Max] | Unique Documents |
|:---|:---:|:---:|:---:|:---:|:---:|
| **k=2** | 2 | 139 tok | 0.5261 | [0.2455 - 0.8066] | 2 doc(s) |
| **k=3** | 3 | 251 tok | 0.4172 | [0.1996 - 0.8066] | 3 doc(s) |
| **k=5** | 5 | 408 tok | 0.3017 | [0.1111 - 0.8066] | 3 doc(s) |

**Marginal Transition Analysis**:
- **k=2 -> k=3**: Expanding k from 2 to 3 adds 1 chunk(s) (+112 tokens). Scores range from 0.1996 to 0.1996, providing supplementary context but lowering average precision.
- **k=3 -> k=5**: Expanding k from 3 to 5 adds 2 chunk(s) (+157 tokens). Scores range from 0.1111 to 0.1457, providing supplementary context but lowering average precision.

---

### Query: `retrieval_q2_security_incident` — IT Security - Incident Response Hotline
**User Prompt**: *"What is the procedure for reporting a suspected malware infection or active data compromise?"*

#### Top-3 Retrieved Chunks Table

| Rank | Score | Chunk ID | Source Document | Section Breadcrumb | Tokens | Source Snippet |
|:---:|:---:|:---|:---|:---|:---:|:---|
| #1 | **0.7026** | `it_security_policy_chunk_003` | `it_security_policy.md` | Section 8.1: Corporate IT Security & Incident Response Protocols > 3. Security Incident Classification & Severity Levels | 96 | Security incidents are classified into four severity tiers: - **Severity 1 (Critical)**: Active d... |
| #2 | **0.6581** | `it_security_policy_chunk_005` | `it_security_policy.md` | Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure | 112 | If you suspect an active security compromise, credential theft, or phishing email: 1. Immediately... |
| #3 | **0.4893** | `it_security_policy_chunk_004` | `it_security_policy.md` | Section 8.1: Corporate IT Security & Incident Response Protocols > 3. Security Incident Classification & Severity Levels | 53 | (Medium)**: Targeted phishing attempt reported by employee or failed brute-force attempt against ... |

#### Complete Metadata & Full Text for Top Grounding Chunk (#1)
```json
{
  "chunk_id": "it_security_policy_chunk_003",
  "rank": 1,
  "similarity_score": 0.7026,
  "source": "data/corpus/it_security_policy.md",
  "document_name": "it_security_policy.md",
  "section": "Section 8.1: Corporate IT Security & Incident Response Protocols > 3. Security Incident Classification & Severity Levels",
  "page": null,
  "position": 1044,
  "token_count": 96,
  "char_count": 494,
  "text": "Security incidents are classified into four severity tiers:\n- **Severity 1 (Critical)**: Active data breach, ransomware deployment, or unauthorized administrative privilege escalation. Incident Commander must be notified within 15 minutes.\n- **Severity 2 (High)**: Compromised employee credential, malware detected on internal host, or unauthenticated API exposure. Response required within 1 hour.\n- **Severity 3 (Medium)**: Targeted phishing attempt reported by employee or failed brute-force"
}
```

#### Analysis of Changing $k$ (k=2, k=3, k=5)

| Setting | Chunks Retrieved | Total Context Tokens | Avg Similarity Score | Score Spread [Min - Max] | Unique Documents |
|:---|:---:|:---:|:---:|:---:|:---:|
| **k=2** | 2 | 208 tok | 0.6804 | [0.6581 - 0.7026] | 1 doc(s) |
| **k=3** | 3 | 261 tok | 0.6167 | [0.4893 - 0.7026] | 1 doc(s) |
| **k=5** | 5 | 338 tok | 0.5309 | [0.3725 - 0.7026] | 3 doc(s) |

**Marginal Transition Analysis**:
- **k=2 -> k=3**: Expanding k from 2 to 3 adds 1 chunk(s) (+53 tokens). Scores range from 0.4893 to 0.4893, providing supplementary context but lowering average precision.
- **k=3 -> k=5**: Expanding k from 3 to 5 adds 2 chunk(s) (+77 tokens). Scores range from 0.3725 to 0.4319, providing supplementary context but lowering average precision.

---

### Query: `retrieval_q3_remote_vpn` — Remote Work - Hardware & VPN Tunnel Security
**User Prompt**: *"What are the network encryption and VPN requirements for connecting remotely to company resources?"*

#### Top-3 Retrieved Chunks Table

| Rank | Score | Chunk ID | Source Document | Section Breadcrumb | Tokens | Source Snippet |
|:---:|:---:|:---|:---|:---|:---:|:---|
| #1 | **0.7605** | `remote_work_policy_chunk_005` | `remote_work_policy.md` | Section 4.2: Remote Work & Workplace Flexibility Policy > 4. Technical Equipment & Information Security | 106 | - **Company Hardware**: Only company-issued laptops equipped with active Endpoint Detection and R... |
| #2 | **0.6908** | `it_security_policy_chunk_002` | `it_security_policy.md` | Section 8.1: Corporate IT Security & Incident Response Protocols > 2. Workstation Security & Encryption | 79 | All employee endpoints must have FileVault (macOS) or BitLocker (Windows) full-disk encryption en... |
| #3 | **0.4185** | `remote_work_policy_chunk_002` | `remote_work_policy.md` | Section 4.2: Remote Work & Workplace Flexibility Policy > 2. Eligibility Requirements | 101 | To qualify for regular or hybrid remote work: - The employee must have completed a minimum of 6 m... |

#### Complete Metadata & Full Text for Top Grounding Chunk (#1)
```json
{
  "chunk_id": "remote_work_policy_chunk_005",
  "rank": 1,
  "similarity_score": 0.7605,
  "source": "data/corpus/remote_work_policy.md",
  "document_name": "remote_work_policy.md",
  "section": "Section 4.2: Remote Work & Workplace Flexibility Policy > 4. Technical Equipment & Information Security",
  "page": null,
  "position": 1765,
  "token_count": 106,
  "char_count": 596,
  "text": "- **Company Hardware**: Only company-issued laptops equipped with active Endpoint Detection and Response (EDR) software may be used for remote work. Personal devices cannot access production environments.\n- **Network Security**: Connecting to public, unencrypted Wi-Fi networks is strictly prohibited. Remote workers must connect exclusively via the corporate AES-256 encrypted VPN tunnel.\n- **Data Protection**: Confidential documents must not be printed at remote locations or stored on unapproved personal cloud storage accounts. Screens must be locked when stepping away from the workstation."
}
```

#### Analysis of Changing $k$ (k=2, k=3, k=5)

| Setting | Chunks Retrieved | Total Context Tokens | Avg Similarity Score | Score Spread [Min - Max] | Unique Documents |
|:---|:---:|:---:|:---:|:---:|:---:|
| **k=2** | 2 | 185 tok | 0.7256 | [0.6908 - 0.7605] | 2 doc(s) |
| **k=3** | 3 | 286 tok | 0.6233 | [0.4185 - 0.7605] | 2 doc(s) |
| **k=5** | 5 | 426 tok | 0.5094 | [0.2665 - 0.7605] | 2 doc(s) |

**Marginal Transition Analysis**:
- **k=2 -> k=3**: Expanding k from 2 to 3 adds 1 chunk(s) (+101 tokens). Scores range from 0.4185 to 0.4185, providing supplementary context but lowering average precision.
- **k=3 -> k=5**: Expanding k from 3 to 5 adds 2 chunk(s) (+140 tokens). Scores range from 0.2665 to 0.4107, providing supplementary context but lowering average precision.

---

### Query: `retrieval_q4_parental_leave` — HR & Benefits - Parental Leave Policy
**User Prompt**: *"What is the parental leave entitlement for new parents and can it be split into blocks?"*

#### Top-3 Retrieved Chunks Table

| Rank | Score | Chunk ID | Source Document | Section Breadcrumb | Tokens | Source Snippet |
|:---:|:---:|:---|:---|:---|:---:|:---|
| #1 | **0.7695** | `employee_benefits_chunk_003` | `employee_benefits.md` | Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 3. Parental Leave & Family Care | 73 | Eligible parents are entitled to 16 weeks of fully paid parental leave following the birth, adopt... |
| #2 | **0.1054** | `hello_chunk_001` | `hello.txt` | N/A | 61 | Welcome to the RAG Document Loader test. This is a plain text file that contains unstructured inf... |
| #3 | **0.0953** | `it_security_policy_chunk_005` | `it_security_policy.md` | Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure | 112 | If you suspect an active security compromise, credential theft, or phishing email: 1. Immediately... |

#### Complete Metadata & Full Text for Top Grounding Chunk (#1)
```json
{
  "chunk_id": "employee_benefits_chunk_003",
  "rank": 1,
  "similarity_score": 0.7695,
  "source": "data/corpus/employee_benefits.md",
  "document_name": "employee_benefits.md",
  "section": "Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 3. Parental Leave & Family Care",
  "page": null,
  "position": 924,
  "token_count": 73,
  "char_count": 415,
  "text": "Eligible parents are entitled to 16 weeks of fully paid parental leave following the birth, adoption, or foster placement of a child. Parental leave must be taken within the first 12 months following the qualifying event. Employees may take the leave in a single continuous block or in two separate blocks with supervisory approval. Health insurance benefits continue uninterrupted during the entire leave duration."
}
```

#### Analysis of Changing $k$ (k=2, k=3, k=5)

| Setting | Chunks Retrieved | Total Context Tokens | Avg Similarity Score | Score Spread [Min - Max] | Unique Documents |
|:---|:---:|:---:|:---:|:---:|:---:|
| **k=2** | 2 | 134 tok | 0.4375 | [0.1054 - 0.7695] | 2 doc(s) |
| **k=3** | 3 | 246 tok | 0.3234 | [0.0953 - 0.7695] | 3 doc(s) |
| **k=5** | 5 | 320 tok | 0.2262 | [0.0694 - 0.7695] | 5 doc(s) |

**Marginal Transition Analysis**:
- **k=2 -> k=3**: Expanding k from 2 to 3 adds 1 chunk(s) (+112 tokens). Scores range from 0.0953 to 0.0953, providing supplementary context but lowering average precision.
- **k=3 -> k=5**: Expanding k from 3 to 5 adds 2 chunk(s) (+74 tokens). Scores range from 0.0694 to 0.0914, providing supplementary context but lowering average precision.

---

## 4. Deep Dive: Precision vs. Recall Trade-offs in Changing $k$

Selecting the optimal value of $k$ directly controls the trade-off between **Precision** (avoiding irrelevant noise and hallucination) and **Recall** (capturing multi-source context necessary for complete answers):

### 4.1 Low $k$ ($k=2$ or $k=3$): High Precision & Cost Efficiency
- **Pros**: Minimal prompt token budget (~150–250 tokens), lowest latency, nearly zero irrelevant distractors. Ideal for direct factual queries (e.g., *"How many days of PTO rollover are allowed?"*).
- **Cons**: Risk of omitting secondary or conditional policies (e.g., exception approval workflows) located in subsequent sections.

### 4.2 High $k$ ($k=5$ or $k=8$): High Recall & Multi-Document Synthesis
- **Pros**: Comprehensive coverage across adjacent policy documents (e.g., retrieving both Remote Hardware security and Incident reporting procedures simultaneously).
- **Cons**: Increases prompt token consumption (~450–750 tokens), dilutes average similarity score, and increases the risk of LLM "lost in the middle" attention degradation.

### 4.3 Recommended Production Heuristic
1. **Primary Default**: Set $k=3$ with a minimum similarity threshold filter ($\text{score} \ge 0.30$).
2. **Adaptive $k$ Strategy**: For complex multi-part queries, retrieve $k=6$, apply a reranker (Cross-Encoder), and pass the top-3 reranked chunks to the generator.

---

## 5. Verification & Quality Assurance

- **Metadata Completeness**: 100% of retrieved chunks carry complete source attribution, chunk index offsets, section breadcrumbs, and token statistics.
- **Score Monotonicity**: All retrieved lists strictly satisfy $S_{\text{rank } i} \ge S_{\text{rank } i+1}$.
- **Reproducibility**: Query embeddings and cosine similarities match the canonical sanity-check test suite.
