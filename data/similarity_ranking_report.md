# RAG Query-Chunk Similarity Ranking & Retrieval Report

**Similarity Metric**: `Cosine Similarity` (L2 Normalized Space)  
**Embedding Dimension ($D$)**: `1536` floating-point components  
**Corpus Chunks Evaluated**: `25` chunks  
**Benchmark Queries**: `4` distinct test scenarios  

---

## Benchmark Scenario 1: HR - Paid Time Off (PTO) & Leave Accrual

**User Query**: *"How many days of paid time off do employees get each year, and can unused PTO be rolled over?"*  

### 🥇 Top-3 Most Similar Chunks (High Relevance)

| Rank | Cosine Sim | Chunk ID | Source Document | Section Header | Tokens |
| :---: | :---: | :--- | :--- | :--- | :---: |
| **#1** | **`0.8066`** | `employee_benefits_chunk_001` | `employee_benefits.md` | Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 1. Paid Time Off (PTO) Accrual | `79` |
| **#2** | **`0.2455`** | `remote_work_policy_chunk_001` | `remote_work_policy.md` | Section 4.2: Remote Work & Workplace Flexibility Policy > 1. Overview & Scope | `60` |
| **#3** | **`0.1996`** | `it_security_policy_chunk_005` | `it_security_policy.md` | Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure | `112` |

**Top Match Snippet**:
> *"Full-time regular employees accrue 18 days of Paid Time Off annually, calculated at a rate of 1.5 days per completed calendar month of active service. Employees may roll over a maximum of 5 unused PTO days into the following calendar year. Any unused balance exceeding 5 days on December 31 will expire without cash compensation, unless an exception is approved by HR due to operational necessity."*

### ❌ Bottom-3 Least Similar Chunks (Orthogonal / Unrelated)

| Rank | Cosine Sim | Chunk ID | Source Document | Section Header | Tokens |
| :---: | :---: | :--- | :--- | :--- | :---: |
| **#23** | `-0.0031` | `page_chunk_005` | `page.html` | H2: Rules of Engagement | `6` |
| **#24** | `-0.0134` | `page_chunk_001` | `page.html` | H1: Community Knowledge Base | `11` |
| **#25** | `-0.0220` | `guide_chunk_001` | `guide.md` | RAG Optimization Guide | `14` |

---

## Benchmark Scenario 2: IT Security - Incident Response & Hotline

**User Query**: *"What is the procedure for reporting a suspected malware infection or active data compromise?"*  

### 🥇 Top-3 Most Similar Chunks (High Relevance)

| Rank | Cosine Sim | Chunk ID | Source Document | Section Header | Tokens |
| :---: | :---: | :--- | :--- | :--- | :---: |
| **#1** | **`0.7026`** | `it_security_policy_chunk_003` | `it_security_policy.md` | Section 8.1: Corporate IT Security & Incident Response Protocols > 3. Security Incident Classification & Severity Levels | `96` |
| **#2** | **`0.6581`** | `it_security_policy_chunk_005` | `it_security_policy.md` | Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure | `112` |
| **#3** | **`0.4893`** | `it_security_policy_chunk_004` | `it_security_policy.md` | Section 8.1: Corporate IT Security & Incident Response Protocols > 3. Security Incident Classification & Severity Levels | `53` |

**Top Match Snippet**:
> *"Security incidents are classified into four severity tiers: - **Severity 1 (Critical)**: Active data breach, ransomware deployment, or unauthorized administrative privilege escalation. Incident Commander must be notified within 15 minutes. - **Severity 2 (High)**: Compromised employee credential, malware detected on internal host, or unauthenticated API exposure. Response required within 1 hour. - **Severity 3 (Medium)**: Targeted phishing attempt reported by employee or failed brute-force"*

### ❌ Bottom-3 Least Similar Chunks (Orthogonal / Unrelated)

| Rank | Cosine Sim | Chunk ID | Source Document | Section Header | Tokens |
| :---: | :---: | :--- | :--- | :--- | :---: |
| **#23** | `0.0347` | `guide_chunk_001` | `guide.md` | RAG Optimization Guide | `14` |
| **#24** | `0.0295` | `guide_chunk_002` | `guide.md` | RAG Optimization Guide > Key Principles of RAG | `53` |
| **#25** | `0.0293` | `page_chunk_004` | `page.html` | H2: Rules of Engagement | `5` |

---

## Benchmark Scenario 3: Remote Work - Hardware & VPN Tunnel Security

**User Query**: *"What are the network encryption and VPN requirements for connecting remotely to company resources?"*  

### 🥇 Top-3 Most Similar Chunks (High Relevance)

| Rank | Cosine Sim | Chunk ID | Source Document | Section Header | Tokens |
| :---: | :---: | :--- | :--- | :--- | :---: |
| **#1** | **`0.7605`** | `remote_work_policy_chunk_005` | `remote_work_policy.md` | Section 4.2: Remote Work & Workplace Flexibility Policy > 4. Technical Equipment & Information Security | `106` |
| **#2** | **`0.6908`** | `it_security_policy_chunk_002` | `it_security_policy.md` | Section 8.1: Corporate IT Security & Incident Response Protocols > 2. Workstation Security & Encryption | `79` |
| **#3** | **`0.4185`** | `remote_work_policy_chunk_002` | `remote_work_policy.md` | Section 4.2: Remote Work & Workplace Flexibility Policy > 2. Eligibility Requirements | `101` |

**Top Match Snippet**:
> *"- **Company Hardware**: Only company-issued laptops equipped with active Endpoint Detection and Response (EDR) software may be used for remote work. Personal devices cannot access production environments. - **Network Security**: Connecting to public, unencrypted Wi-Fi networks is strictly prohibited. Remote workers must connect exclusively via the corporate AES-256 encrypted VPN tunnel. - **Data Protection**: Confidential documents must not be printed at remote locations or stored on unapproved personal cloud storage accounts. Screens must be locked when stepping away from the workstation."*

### ❌ Bottom-3 Least Similar Chunks (Orthogonal / Unrelated)

| Rank | Cosine Sim | Chunk ID | Source Document | Section Header | Tokens |
| :---: | :---: | :--- | :--- | :--- | :---: |
| **#23** | `-0.0117` | `page_chunk_005` | `page.html` | H2: Rules of Engagement | `6` |
| **#24** | `-0.0174` | `it_security_policy_chunk_003` | `it_security_policy.md` | Section 8.1: Corporate IT Security & Incident Response Protocols > 3. Security Incident Classification & Severity Levels | `96` |
| **#25** | `-0.0352` | `page_chunk_004` | `page.html` | H2: Rules of Engagement | `5` |

---

## Benchmark Scenario 4: RAG Architecture - Ingestion & Chunking Principles

**User Query**: *"How does the RAG document loader transform mixed-format files and semantic chunk units for retrieval?"*  

### 🥇 Top-3 Most Similar Chunks (High Relevance)

| Rank | Cosine Sim | Chunk ID | Source Document | Section Header | Tokens |
| :---: | :---: | :--- | :--- | :--- | :---: |
| **#1** | **`0.7896`** | `document_chunk_001` | `document.pdf` | RAG System Documentation | `78` |
| **#2** | **`0.7213`** | `guide_chunk_002` | `guide.md` | RAG Optimization Guide > Key Principles of RAG | `53` |
| **#3** | **`0.6798`** | `hello_chunk_001` | `hello.txt` | N/A | `61` |

**Top Match Snippet**:
> *"RAG System Documentation This PDF document contains reference guide for Retrieval-Augmented Generation. Retrieval-Augmented Generation (RAG) is a technique that combines retrieval and generation. It leverages external knowledge sources to improve LLM generation accuracy and relevance. Our loader module parses this PDF cleanly to feed it to downstream processes. Verify that page-by-page text extraction works and is formatted correctly."*

### ❌ Bottom-3 Least Similar Chunks (Orthogonal / Unrelated)

| Rank | Cosine Sim | Chunk ID | Source Document | Section Header | Tokens |
| :---: | :---: | :--- | :--- | :--- | :---: |
| **#23** | `-0.0051` | `employee_benefits_chunk_001` | `employee_benefits.md` | Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 1. Paid Time Off (PTO) Accrual | `79` |
| **#24** | `-0.0085` | `it_security_policy_chunk_003` | `it_security_policy.md` | Section 8.1: Corporate IT Security & Incident Response Protocols > 3. Security Incident Classification & Severity Levels | `96` |
| **#25** | `-0.0234` | `page_chunk_004` | `page.html` | H2: Rules of Engagement | `5` |

---

## 📐 Metric Justification: Why Cosine Similarity?

### Metric Selection & Justification: Why Cosine Similarity for Vector Retrieval?

In modern Retrieval-Augmented Generation (RAG) pipelines, **Cosine Similarity** is the industry standard for matching query embeddings against document chunk embeddings. Here is the mathematical and architectural rationale:

1. **Scale & Length Invariance (Direction over Magnitude)**:
   - Chunk text lengths naturally vary (e.g., a concise 14-token overview chunk vs. an exhaustive 112-token procedural chunk).
   - In unnormalized Euclidean space ($L_2$), longer texts often generate vectors with larger magnitudes, artificially increasing Euclidean distance even when the semantic meaning is identical.
   - **Cosine Similarity isolates the angular direction** ($\theta$) of vectors in high-dimensional space ($\cos \theta = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$), measuring conceptual alignment purely independent of text volume.

2. **Bounded and Standardized Metric Space ($[-1.0, +1.0]$)**:
   - Cosine similarity produces values bounded strictly between $-1.0$ (diametrically opposite) and $+1.0$ (identical direction), with $0.0$ indicating orthogonal/unrelated semantics.
   - This bounded property enables reliable global relevance filtering thresholds (e.g., discarding chunks with $\text{score} < 0.35$) across disparate queries and topics.

3. **Computational Equivalence to Dot Product on Unit Spheres**:
   - Modern dense embedding models normalize all output vectors to unit norm ($\|\mathbf{u}\|_2 = 1.0, \|\mathbf{v}\|_2 = 1.0$).
   - On the unit sphere, Cosine Similarity reduces directly to the standard dot product:
     $$\text{Cosine Similarity}(\mathbf{u}, \mathbf{v}) = \mathbf{u} \cdot \mathbf{v}$$
   - And relates monotonically to Euclidean distance:
     $$d_{L_2}(\mathbf{u}, \mathbf{v})^2 = 2 - 2(\mathbf{u} \cdot \mathbf{v})$$
   - This allows high-performance Approximate Nearest Neighbor (ANN) index engines (FAISS, HNSW, pgvector) to perform lightning-fast dot product operations without square roots or runtime magnitude divisions.
