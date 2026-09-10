# End-to-End RAG Pipeline Architecture & Execution Report

**Embedding Model / Engine**: `OpenAI-Compatible API (text-embedding-3-small)`  
**Total Sample Queries Executed**: `4`  
**Pipeline Status**: `Operational (100% Grounded Context)`  

---

## 1. Architectural Flow Summary

1. **Stage 1 (Embed Query)**: Converts user prompt into a 1536-D normalized vector.
2. **Stage 2 (Vector Retrieval)**: Retrieves top-k most similar chunks using cosine similarity.
3. **Stage 3 (Context Assembly)**: Constructs structured context block with clear source demarcations.
4. **Stage 4 (Grounded Generation)**: Passes system prompt + context + prompt to LLM to generate answer with verified source citations.

---

## 2. Sample Pipeline Runs & Returned Sources

### Run 1: *"How many days of paid time off do employees get each year, and can unused PTO be rolled over?"*

**Generated Answer**:
> Employees accrue 18 days of PTO annually, and up to 5 unused days may be rolled over into the next calendar year.    
>   
> - PTO accrual: 1.5 days per completed calendar month.    
> - Rollover limit: 5 days; any balance above that expires on December 31.    
> - Rollover requires no additional approval unless an exception is granted by HR.

**Returned Sources** (`3` chunks):

| Rank | Chunk ID | Document | Section | Score |
| :---: | :--- | :--- | :--- | :---: |
| **1** | `employee_benefits_chunk_001` | employee_benefits.md | Section 6.0: Employee Benefits, Pai... | `0.5269` |
| **2** | `employee_benefits_chunk_002` | employee_benefits.md | Section 6.0: Employee Benefits, Pai... | `0.3804` |
| **3** | `employee_benefits_chunk_003` | employee_benefits.md | Section 6.0: Employee Benefits, Pai... | `0.2352` |

---

### Run 2: *"What are the network encryption and VPN requirements for connecting remotely to company resources?"*

**Generated Answer**:
> Employees must connect to company resources via an encrypted VPN that is protected by multi‑factor authentication.    
>   
> - The VPN connection must use industry‑standard encryption (e.g., AES‑256).    
> - Multi‑factor authentication (MFA) is required for all remote access.    
> - The IT Security Operations team verifies compliance before approval.

**Returned Sources** (`3` chunks):

| Rank | Chunk ID | Document | Section | Score |
| :---: | :--- | :--- | :--- | :---: |
| **1** | `remote_work_policy_chunk_003` | remote_work_policy.md | Section 4.2: Remote Work & Workplac... | `0.6856` |
| **2** | `remote_work_policy_chunk_002` | remote_work_policy.md | Section 4.2: Remote Work & Workplac... | `0.6330` |
| **3** | `remote_work_policy_chunk_001` | remote_work_policy.md | Section 4.2: Remote Work & Workplac... | `0.6311` |

---

### Run 3: *"What are the minimum password length requirements and is SMS authentication permitted?"*

**Generated Answer**:
> Passwords must be at least 14 characters long, and SMS-based authentication is not permitted.

**Returned Sources** (`3` chunks):

| Rank | Chunk ID | Document | Section | Score |
| :---: | :--- | :--- | :--- | :---: |
| **1** | `it_security_policy_chunk_001` | it_security_policy.md | Section 8.1: Corporate IT Security ... | `0.3016` |
| **2** | `remote_work_policy_chunk_004` | remote_work_policy.md | Section 4.2: Remote Work & Workplac... | `0.2330` |
| **3** | `employee_benefits_chunk_003` | employee_benefits.md | Section 6.0: Employee Benefits, Pai... | `0.1794` |

---

### Run 4: *"How does the RAG document loader transform mixed-format files and semantic chunk units for retrieval?"*

**Generated Answer**:
> The loader first normalizes mixed‑format files into plain text, then splits that text into semantically

**Returned Sources** (`3` chunks):

| Rank | Chunk ID | Document | Section | Score |
| :---: | :--- | :--- | :--- | :---: |
| **1** | `hello_chunk_001` | hello.txt | N/A... | `0.7877` |
| **2** | `guide_chunk_001` | guide.md | RAG Optimization Guide... | `0.7209` |
| **3** | `guide_chunk_002` | guide.md | RAG Optimization Guide > Key Princi... | `0.6883` |

---

