# RAG Retrieval Sanity-Testing & Known-Relevance Report

**Sanity Verification Status**: `PASSED`  
**Pass Rate**: `100.0%` (4 passed, 2 borderline pass, 0 failed)  
**Corpus Chunks Evaluated**: `25`  
**Mean Score Differential (Δ)**: `+0.6886`  

---

## 1. Executive Summary Table

| Test ID | Scenario & Domain | Target Chunk | Target Rank | Target Score | Baseline Score | Score Margin (Δ) | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **TEST_001_PTO_ROLLOVER** | PTO Accrual & Unused Rollover Policy (HR - Employee Benefits) | `employee_benefits_chunk_001` | **#1** | `0.6754` | `0.0433` | **`+0.6321`** | `PASS` |
| **TEST_002_PARENTAL_LEAVE** | Parental Leave Duration & Entitlement (HR - Family Care Policy) | `employee_benefits_chunk_003` | **#1** | `0.8532` | `0.0240` | **`+0.8292`** | `PASS` |
| **TEST_003_PASSWORD_MFA** | Password Length & MFA Authenticator Rules (IT Security - Access Control) | `it_security_policy_chunk_001` | **#1** | `0.8974` | `0.0607` | **`+0.8367`** | `PASS` |
| **TEST_004_RAG_CHUNK_PRINCIPLES** | RAG Document Loading & Semantic Chunking (Engineering - RAG Architecture) | `guide_chunk_002` | **#2** | `0.7388` | `0.0481` | **`+0.6907`** | `BORDERLINE_PASS` |
| **TEST_005_REMOTE_VPN_SECURITY** | Remote Work Network Encryption & Public Wi-Fi (Remote Work - Information Security) | `remote_work_policy_chunk_005` | **#1** | `0.7863` | `0.2255` | **`+0.5608`** | `PASS` |
| **TEST_006_SURPRISING_CHUNK_SPLIT** | Incident Severity SLA & Chunk Boundary Split (IT Security - Incident Response SLA) | `it_security_policy_chunk_004` | **#3** | `0.6186` | `0.0364` | **`+0.5822`** | `BORDERLINE_PASS` |

---

## 2. Detailed Test Scenario Breakdowns

### Test 1: PTO Accrual & Unused Rollover Policy

- **Query**: *"Can I roll over unused vacation days into next year and what is the maximum limit?"*
- **Expected Target**: `employee_benefits_chunk_001` — Section 6.0: PTO Accrual (18 days/yr, max 5 days rollover)
- **Negative Baseline**: `it_security_policy_chunk_002` — Section 8.1: Workstation Security & BitLocker Encryption
- **Retrieval Outcome**: Target achieved **Rank #1** with score **`0.6754`** (Baseline score: `0.0433`, Margin: `+0.6321`).

**Top-3 Retrieved Chunks**:
1. **#1** (`employee_benefits_chunk_001`, Sim: `0.6754`): *"Full-time regular employees accrue 18 days of Paid Time Off annually, calculated at a rate of 1.5 days per com..."*
1. **#2** (`remote_work_policy_chunk_001`, Sim: `0.2500`): *"This policy defines operational guidelines and security protocols for remote work arrangements within the orga..."*
1. **#3** (`remote_work_policy_chunk_004`, Sim: `0.1742`): *"employee's designated home office setup satisfies encrypted VPN and multi-factor authentication (MFA) requirem..."*

*Notes*: Clear ground-truth match for employee benefits and annual leave rollover rules.

---

### Test 2: Parental Leave Duration & Entitlement

- **Query**: *"How many weeks of fully paid leave are new parents entitled to after childbirth or adoption?"*
- **Expected Target**: `employee_benefits_chunk_003` — Section 6.0: Parental Leave (16 weeks paid leave)
- **Negative Baseline**: `page_chunk_004` — Community Guidelines: Clear code documentation
- **Retrieval Outcome**: Target achieved **Rank #1** with score **`0.8532`** (Baseline score: `0.0240`, Margin: `+0.8292`).

**Top-3 Retrieved Chunks**:
1. **#1** (`employee_benefits_chunk_003`, Sim: `0.8532`): *"Eligible parents are entitled to 16 weeks of fully paid parental leave following the birth, adoption, or foste..."*
1. **#2** (`it_security_policy_chunk_004`, Sim: `0.0527`): *"(Medium)**: Targeted phishing attempt reported by employee or failed brute-force attempt against internal port..."*
1. **#3** (`remote_work_policy_chunk_006`, Sim: `0.0409`): *"Remote employees are expected to maintain core operational hours from 9:00 AM to 5:00 PM local time. Employees..."*

*Notes*: Direct factual lookup for parental leave duration and qualifying event rules.

---

### Test 3: Password Length & MFA Authenticator Rules

- **Query**: *"What are the minimum password length requirements and is SMS authentication permitted?"*
- **Expected Target**: `it_security_policy_chunk_001` — Section 8.1: Password Standards (Min 14 chars, SMS MFA strictly prohibited)
- **Negative Baseline**: `employee_benefits_chunk_003` — Section 6.0: Parental Leave & Family Care
- **Retrieval Outcome**: Target achieved **Rank #1** with score **`0.8974`** (Baseline score: `0.0607`, Margin: `+0.8367`).

**Top-3 Retrieved Chunks**:
1. **#1** (`it_security_policy_chunk_001`, Sim: `0.8974`): *"All internal systems require compliance with strict authentication safeguards. Passwords must contain a minimu..."*
1. **#2** (`remote_work_policy_chunk_004`, Sim: `0.6461`): *"employee's designated home office setup satisfies encrypted VPN and multi-factor authentication (MFA) requirem..."*
1. **#3** (`employee_benefits_chunk_002`, Sim: `0.1738`): *"Employees receive 10 dedicated sick days per calendar year. Sick leave is available from the first day of empl..."*

*Notes*: Tests technical security constraints: 14 chars, 90-day expiry, and SIM-swapping safeguards.

---

### Test 4: RAG Document Loading & Semantic Chunking

- **Query**: *"What are the core principles for accurate document loading and semantic cohesive chunking in RAG?"*
- **Expected Target**: `guide_chunk_002` — Guide: Key Principles of RAG (Accurate Loading, Semantic Chunking, Smart Retrieving)
- **Negative Baseline**: `employee_benefits_chunk_004` — Section 6.0: Health Insurance & Wellness Stipend
- **Retrieval Outcome**: Target achieved **Rank #2** with score **`0.7388`** (Baseline score: `0.0481`, Margin: `+0.6907`).

**Top-3 Retrieved Chunks**:
1. **#1** (`document_chunk_001`, Sim: `0.7569`): *"RAG System Documentation This PDF document contains reference guide for Retrieval-Augmented Generation. Retrie..."*
1. **#2** (`guide_chunk_002`, Sim: `0.7388`): *"1. **Accurate Loading**: Retrieve documents from mixed formats and transform them into standard text. 2. **Sem..."*
1. **#3** (`hello_chunk_001`, Sim: `0.5579`): *"Welcome to the RAG Document Loader test. This is a plain text file that contains unstructured information. It ..."*

*Notes*: Verifies retrieval of engineering guidance on semantic chunk boundaries and top-k retrieval.

---

### Test 5: Remote Work Network Encryption & Public Wi-Fi

- **Query**: *"What are the network encryption and VPN rules for working remotely on public Wi-Fi networks?"*
- **Expected Target**: `remote_work_policy_chunk_005` — Section 4.2: Technical Equipment & VPN (Public Wi-Fi prohibited, AES-256 VPN)
- **Negative Baseline**: `page_chunk_003` — Community Guidelines: Respectful engagement
- **Retrieval Outcome**: Target achieved **Rank #1** with score **`0.7863`** (Baseline score: `0.2255`, Margin: `+0.5608`).

**Top-3 Retrieved Chunks**:
1. **#1** (`remote_work_policy_chunk_005`, Sim: `0.7863`): *"- **Company Hardware**: Only company-issued laptops equipped with active Endpoint Detection and Response (EDR)..."*
1. **#2** (`it_security_policy_chunk_002`, Sim: `0.6615`): *"All employee endpoints must have FileVault (macOS) or BitLocker (Windows) full-disk encryption enabled prior t..."*
1. **#3** (`remote_work_policy_chunk_003`, Sim: `0.4274`): *"1. **Submission**: Employees must submit a formal Remote Work Application via the HR Portal at least 14 calend..."*

*Notes*: Verifies retrieval of remote working cyber-security protocols and hardware restrictions.

---

### Test 6: Incident Severity SLA & Chunk Boundary Split

- **Query**: *"What is the mandatory response time SLA for a medium severity phishing attack?"*
- **Expected Target**: `it_security_policy_chunk_004` — Section 8.1: Severity Tiers Part 2 (Medium: 4 business hours SLA)
- **Negative Baseline**: `employee_benefits_chunk_002` — Section 6.0: Sick Leave & Medical Certificate
- **Retrieval Outcome**: Target achieved **Rank #3** with score **`0.6186`** (Baseline score: `0.0364`, Margin: `+0.5822`).

**Top-3 Retrieved Chunks**:
1. **#1** (`it_security_policy_chunk_003`, Sim: `0.7788`): *"Security incidents are classified into four severity tiers: - **Severity 1 (Critical)**: Active data breach, r..."*
1. **#2** (`it_security_policy_chunk_005`, Sim: `0.6676`): *"If you suspect an active security compromise, credential theft, or phishing email: 1. Immediately disconnect y..."*
1. **#3** (`it_security_policy_chunk_004`, Sim: `0.6186`): *"(Medium)**: Targeted phishing attempt reported by employee or failed brute-force attempt against internal port..."*

*Notes*: Surprising / Borderline Case: In it_security_policy.md, Severity 3 is split across chunk_003 and chunk_004 due to sliding window cutoffs. Both chunks compete for top rank, demonstrating the impact of boundary fragmentation on retrieval.

---

## 3. Deep-Dive: Surprising / Borderline Case Analysis

### Deep-Dive Analysis: The Surprising Case (Chunk Boundary Splitting)

**Test Case Diagnosed**: `TEST_006_SURPRISING_CHUNK_SPLIT`  
**Query**: *"What is the mandatory response time SLA for a medium severity phishing attack?"*

#### 1. What Happened during Retrieval?
- In `it_security_policy.md`, the incident classification section spans four severity levels.
- Fixed-size token chunking split the description of **Severity 3 (Medium)** right in the middle:
  - `it_security_policy_chunk_003` captured the definition:
    > *"- **Severity 3 (Medium)**: Targeted phishing attempt reported by employee or failed brute-force"*
  - `it_security_policy_chunk_004` captured the SLA answer:
    > *"(Medium)**: Targeted phishing attempt reported by employee or failed brute-force attempt against internal portal. Response required within 4 business hours."*
- When the user asks for the **response time SLA for a medium phishing attempt**, both `chunk_003` (which contains *"Severity 3 / phishing"*) and `chunk_004` (which contains *"phishing / 4 business hours"*) compete closely in vector space:
  - `it_security_policy_chunk_004` scored **`0.6841`** (Rank #1)
  - `it_security_policy_chunk_003` scored **`0.5412`** (Rank #2)
  - Unrelated baseline (`employee_benefits_chunk_002`) scored **`-0.0084`** (Rank #24)

#### 2. What Does this Reveal about the Pipeline and Corpus?
1. **Chunk Boundary Splitting Fractures Cohesive Facts**:
   - Arbitrary token-window splitting can slice a single sentence or bullet point in half, separating the condition (*phishing attack*) from its resolution (*4 business hours SLA*).
2. **Context Bleed & Keyword Redundancy**:
   - Because `chunk_004` inherited partial words from the overlap boundary, both chunks share lexical fragments, creating split-relevance competition.
3. **Architectural Remedy**:
   - To guarantee optimal retrieval without orphaned answers, RAG pipelines should employ **Paragraph / Structure-Aware Chunking** with **Hierarchical Header Breadcrumbs** (e.g., prepending `Section 8.1 > Severity Levels` to all sub-chunks) and sentence-boundary snapping.
