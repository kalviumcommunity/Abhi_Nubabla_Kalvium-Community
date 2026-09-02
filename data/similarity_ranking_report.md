# RAG Query-Chunk Similarity Ranking & Retrieval Report

**Similarity Metric**: `Cosine Similarity` (L2 Normalized Space)  
**Embedding Dimension ($D$)**: `1536` floating-point components  
**Corpus Chunks Evaluated**: `25` chunks  
**Benchmark Queries**: `1` distinct test scenarios  

---

## Benchmark Scenario 1: Custom User Query

**User Query**: *"How many days of paid time off do employees get?"*  

### 🥇 Top-3 Most Similar Chunks (High Relevance)

| Rank | Cosine Sim | Chunk ID | Source Document | Section Header | Tokens |
| :---: | :---: | :--- | :--- | :--- | :---: |
| **#1** | **`0.6526`** | `employee_benefits_chunk_001` | `employee_benefits.md` | Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 1. Paid Time Off (PTO) Accrual | `79` |
| **#2** | **`0.1732`** | `it_security_policy_chunk_005` | `it_security_policy.md` | Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure | `112` |
| **#3** | **`0.1629`** | `remote_work_policy_chunk_001` | `remote_work_policy.md` | Section 4.2: Remote Work & Workplace Flexibility Policy > 1. Overview & Scope | `60` |

**Top Match Snippet**:
> *"Full-time regular employees accrue 18 days of Paid Time Off annually, calculated at a rate of 1.5 days per completed calendar month of active service. Employees may roll over a maximum of 5 unused PTO days into the following calendar year. Any unused balance exceeding 5 days on December 31 will expire without cash compensation, unless an exception is approved by HR due to operational necessity."*

### ❌ Bottom-3 Least Similar Chunks (Orthogonal / Unrelated)

| Rank | Cosine Sim | Chunk ID | Source Document | Section Header | Tokens |
| :---: | :---: | :--- | :--- | :--- | :---: |
| **#23** | `-0.0051` | `page_chunk_003` | `page.html` | H2: Rules of Engagement | `5` |
| **#24** | `-0.0179` | `guide_chunk_001` | `guide.md` | RAG Optimization Guide | `14` |
| **#25** | `-0.0244` | `page_chunk_001` | `page.html` | H1: Community Knowledge Base | `11` |

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
