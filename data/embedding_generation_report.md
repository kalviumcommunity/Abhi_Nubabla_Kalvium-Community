# Batch Embedding Pipeline & Rate/Cost Management Report

**Embedding Model / Engine**: `OpenAI-Compatible API (text-embedding-3-small)`  
**Total Corpus Chunks**: `25`  
**Chunks Embedded This Run**: `0`  
**Skipped Chunks (Already Embedded)**: `25`  
**Failed Batches**: `0`  
**Estimated Run Cost ($USD)**: `$0.000000`  
**Vector Length (Dimension $D$)**: `1536` floating-point coordinates  

---

## 1. Batch Execution & Retry Metrics

| Metric | Value |
| :--- | :--- |
| **Configured Batch Size** | `8` chunks/batch |
| **Max Retries Allowed** | `3` retries |
| **Total Batches Processed** | `0` |
| **Successful Batches** | `0` |
| **Failed Batches** | `0` |
| **Total API Requests Made** | `0` |
| **Retries Attempted** | `0` |
| **Tokens Embedded This Run** | `0` tokens |
| **Estimated Run Cost ($USD)** | `$0.000000` |
| **Total Corpus Cost ($USD)** | `$0.000029` |

---

## 2. Environment Configuration

| Setting | Value / Status |
| :--- | :--- |
| **API Key Configured** | `Yes (Loaded from .env)` |
| **API Base URL** | `https://api.groq.com/openai/v1` |
| **Target Model** | `text-embedding-3-small` |

---

## 3. Sample Stored Embedded Chunks

| Chunk ID | Document | Section | Page | Tokens | Vector Dim | Trimmed Vector Values (First 3 & Last 3) |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **document_chunk_001** | document.pdf | RAG System Documentation | 1 | 78 | `1536` | `[+0.0000, +0.0000, +0.0003, ... , -0.0340, +0.0000, +0.0000]` |
| **employee_benefits_chunk_001** | employee_benefits.md | Section 6.0: Employee Benefits, Pai... | - | 79 | `1536` | `[+0.0000, +0.0000, +0.0000, ... , +0.0000, +0.0000, +0.0040]` |
| **employee_benefits_chunk_002** | employee_benefits.md | Section 6.0: Employee Benefits, Pai... | - | 67 | `1536` | `[-0.0363, +0.0000, +0.0000, ... , +0.0112, +0.0000, +0.0047]` |
| **employee_benefits_chunk_003** | employee_benefits.md | Section 6.0: Employee Benefits, Pai... | - | 73 | `1536` | `[+0.0000, +0.0048, +0.0000, ... , +0.0107, +0.0000, +0.0000]` |
| **employee_benefits_chunk_004** | employee_benefits.md | Section 6.0: Employee Benefits, Pai... | - | 79 | `1536` | `[+0.0000, -0.0120, +0.0000, ... , +0.0000, +0.0000, -0.0276]` |

---

## 4. Deduplication & Idempotency Proof

> On re-running the embedding script, `25` out of `25` chunks were detected as already embedded and skipped. This prevented `25` redundant API calls and saved approximate execution cost.

