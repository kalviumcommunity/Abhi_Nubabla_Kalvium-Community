# Corpus Embedding Generation & Retrieval Metadata Report

**Embedding Model / Engine**: `DenseSemanticEmbedder (Local Fallback, D=1536)`  
**Total Chunks Embedded**: `25`  
**Vector Length (Dimension $D$)**: `1536` floating-point coordinates  
**Uniform Vector Dimensions**: `Confirmed (100% Uniform)`  

---

## 1. Environment & API Configuration

| Setting | Value / Status |
| :--- | :--- |
| **API Key Configured** | `Yes (Loaded from .env)` |
| **API Base URL** | `https://api.groq.com/openai/v1` |
| **Target Model** | `text-embedding-3-small` |

---

## 2. Sample Stored Embedded Chunks

| Chunk ID | Document | Section | Page | Tokens | Vector Dim | Trimmed Vector Values (First 3 & Last 3) |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **document_chunk_001** | document.pdf | RAG System Documentation | 1 | 78 | `1536` | `[+0.0000, +0.0000, +0.0003, ... , -0.0340, +0.0000, +0.0000]` |
| **employee_benefits_chunk_001** | employee_benefits.md | Section 6.0: Employee Benefits, Pai... | - | 79 | `1536` | `[+0.0000, +0.0000, +0.0000, ... , +0.0000, +0.0000, +0.0040]` |
| **employee_benefits_chunk_002** | employee_benefits.md | Section 6.0: Employee Benefits, Pai... | - | 67 | `1536` | `[-0.0363, +0.0000, +0.0000, ... , +0.0112, +0.0000, +0.0047]` |
| **employee_benefits_chunk_003** | employee_benefits.md | Section 6.0: Employee Benefits, Pai... | - | 73 | `1536` | `[+0.0000, +0.0048, +0.0000, ... , +0.0107, +0.0000, +0.0000]` |
| **employee_benefits_chunk_004** | employee_benefits.md | Section 6.0: Employee Benefits, Pai... | - | 79 | `1536` | `[+0.0000, -0.0120, +0.0000, ... , +0.0000, +0.0000, -0.0276]` |

---

## 3. Stored Text & Metadata Verification

### Chunk: `document_chunk_001`
- **Source Document**: `document.pdf`
- **Chunk Index**: `0`
- **Section**: `RAG System Documentation`
- **Vector Length**: `1536`
- **Sample Vector Slice (First 5 Values)**: `[0.0, 0.0, 0.000344, 0.0, 0.0]`
- **Stored Source Text Snippet**:
  > *"RAG System Documentation
This PDF document contains reference guide for Retrieval-Augmented Generation.
Retrieval-Augmented Generation (RAG) is a tech..."*

### Chunk: `employee_benefits_chunk_001`
- **Source Document**: `employee_benefits.md`
- **Chunk Index**: `68`
- **Section**: `Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 1. Paid Time Off (PTO) Accrual`
- **Vector Length**: `1536`
- **Sample Vector Slice (First 5 Values)**: `[0.0, 0.0, 0.0, 0.051707, 0.0]`
- **Stored Source Text Snippet**:
  > *"Full-time regular employees accrue 18 days of Paid Time Off annually, calculated at a rate of 1.5 days per completed calendar month of active service...."*

### Chunk: `employee_benefits_chunk_002`
- **Source Document**: `employee_benefits.md`
- **Chunk Index**: `501`
- **Section**: `Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 2. Sick Leave & Medical Appointments`
- **Vector Length**: `1536`
- **Sample Vector Slice (First 5 Values)**: `[-0.036305, 0.0, 0.0, 0.0, 0.0]`
- **Stored Source Text Snippet**:
  > *"Employees receive 10 dedicated sick days per calendar year. Sick leave is available from the first day of employment and does not require advance noti..."*

