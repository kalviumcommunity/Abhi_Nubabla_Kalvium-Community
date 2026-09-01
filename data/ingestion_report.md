# Corpus Ingestion & Completeness Validation Report

**Run Timestamp**: `2026-08-31T14:10:45.359751`  
**Corpus Directory**: `C:/Users/Abhi Vignesh Samala/OneDrive/Desktop/Abhi_Nubabla_Kalvium-Community/data/corpus`  
**Completeness Validation**: `✅ PASSED (100% Accounted For)`  

---

## 📊 Task 2: Ingestion Executive Summary

| Metric | Value | Notes / Reconciliation |
| :--- | :---: | :--- |
| **Total Source Documents** | **8** | Total files discovered on disk |
| **Successfully Ingested** | **7** | Cleaned, chunked & tagged without errors |
| **Recorded Failures** | **1** | Corrupt/invalid files caught & audited |
| **Silent Drops / Unaccounted** | **0** | Mathematical proof verified |
| **Total Chunks Created** | **25** | Atomic retrieval units ready for RAG |
| **Total Ingested Tokens** | **1,470** | Measured using `tiktoken` (`cl100k_base`) |
| **Avg Tokens / Chunk** | **58.8** | Clean context size per retrieval unit |
| **Avg Chars / Chunk** | **316.64** | Character distribution |

---

## 🔒 Task 3: Completeness Validation & Reconciliation Audit

> [!IMPORTANT]
> **Reconciliation Formula Proof**:
> `$$\text{Total Documents (8)} = \text{Ingested (7)} + \text{Failures (1)} + \text{Skipped (0)}$$`
> **Audit Status**: `8 Total == 7 Ingested + 1 Failures + 0 Skipped` — **Zero Silent Drops Guaranteed**.

### Document-by-Document Audit Registry

| Document Name | Type | Size (Bytes) | Status | Chunks | Tokens | Error Reason |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `corrupt.pdf` | `.pdf` | 223 | ❌ FAILED | 0 | 0 | PdfStreamError: Stream has ended unexpectedly |
| `document.pdf` | `.pdf` | 1,919 | ✅ SUCCESS | 1 | 78 | — |
| `employee_benefits.md` | `.md` | 1,862 | ✅ SUCCESS | 4 | 363 | — |
| `guide.md` | `.md` | 512 | ✅ SUCCESS | 3 | 102 | — |
| `hello.txt` | `.txt` | 324 | ✅ SUCCESS | 1 | 61 | — |
| `it_security_policy.md` | `.md` | 2,390 | ✅ SUCCESS | 5 | 470 | — |
| `page.html` | `.html` | 926 | ✅ SUCCESS | 5 | 44 | — |
| `remote_work_policy.md` | `.md` | 2,851 | ✅ SUCCESS | 6 | 523 | — |

---

## 🔍 Task 4: Sample Chunks Boundary & Metadata Inspection

Below are sample inspected chunks demonstrating cleaned text, sensible boundary offsets, and metadata tags:

### Chunk `document_chunk_001` (`.pdf` | 78 tokens | 438 chars)
- **Source**: `data/corpus/document.pdf`
- **Section / Breadcrumb**: `RAG System Documentation`
- **Page**: `1`
- **Start Position**: `0`
- **Cleaned Flag**: `True`
```text
RAG System Documentation
This PDF document contains reference guide for Retrieval-Augmented Generation.
Retrieval-Augmented Generation (RAG) is a technique that combines retrieval and generation.
It leverages external knowledge sources to improve LLM generation accuracy and relevance.
Our loader module parses this PDF cleanly to feed it to downstream processes.
Verify that page-by-page text extraction works and is formatted correctly.
```

### Chunk `employee_benefits_chunk_001` (`.md` | 79 tokens | 397 chars)
- **Source**: `data/corpus/employee_benefits.md`
- **Section / Breadcrumb**: `Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 1. Paid Time Off (PTO) Accrual`
- **Page**: `N/A`
- **Start Position**: `68`
- **Cleaned Flag**: `True`
```text
Full-time regular employees accrue 18 days of Paid Time Off annually, calculated at a rate of 1.5 days per completed calendar month of active service. Employees may roll over a maximum of 5 unused PTO days into the following calendar year. Any unused balance exceeding 5 days on December 31 will expire without cash compensation, unless an exception is approved by HR due to operational necessity.
```

### Chunk `hello_chunk_001` (`.txt` | 61 tokens | 318 chars)
- **Source**: `data/corpus/hello.txt`
- **Section / Breadcrumb**: `N/A`
- **Page**: `N/A`
- **Start Position**: `0`
- **Cleaned Flag**: `True`
```text
Welcome to the RAG Document Loader test.
This is a plain text file that contains unstructured information.
It is designed to be loaded by our document loader and parsed into plain text.
RAG systems need simple text format to compute embeddings and search for matching chunks.
This concludes the plain text sample file.
```

### Chunk `page_chunk_001` (`.html` | 11 tokens | 77 chars)
- **Source**: `data/corpus/page.html`
- **Section / Breadcrumb**: `H1: Community Knowledge Base`
- **Page**: `N/A`
- **Start Position**: `327`
- **Cleaned Flag**: `True`
```text
This HTML page contains reference information about our community guidelines.
```

### Chunk `employee_benefits_chunk_001` (`.md` | 79 tokens | 397 chars)
- **Source**: `data/corpus/employee_benefits.md`
- **Section / Breadcrumb**: `Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 1. Paid Time Off (PTO) Accrual`
- **Page**: `N/A`
- **Start Position**: `68`
- **Cleaned Flag**: `True`
```text
Full-time regular employees accrue 18 days of Paid Time Off annually, calculated at a rate of 1.5 days per completed calendar month of active service. Employees may roll over a maximum of 5 unused PTO days into the following calendar year. Any unused balance exceeding 5 days on December 31 will expire without cash compensation, unless an exception is approved by HR due to operational necessity.
```

### Chunk `remote_work_policy_chunk_006` (`.md` | 68 tokens | 361 chars)
- **Source**: `data/corpus/remote_work_policy.md`
- **Section / Breadcrumb**: `Section 4.2: Remote Work & Workplace Flexibility Policy > 5. Working Hours, Availability & Communication`
- **Page**: `N/A`
- **Start Position**: `2412`
- **Cleaned Flag**: `True`
```text
Remote employees are expected to maintain core operational hours from 9:00 AM to 5:00 PM local time. Employees must remain reachable via official communication channels (Slack, Microsoft Teams, corporate email) during working hours. Any scheduled absence or temporary unavailability must be logged in the shared department calendar at least 24 hours in advance.
```

---

## 📦 Task 5: Exported Artifacts Summary

- **Structured Ingestion Summary**: `data/ingestion_summary.json`
- **Full Tagged Chunks Store**: `data/ingested_chunks.json`
- **Reviewer Audit Report**: `data/ingestion_report.md`