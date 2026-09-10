# Verifiable Source Citations & Metadata Attribution Report

**Total Queries Executed**: `4`  
**Verified Citation Rate**: `100%`  
**Fallback Safeguard Triggered**: `1 query (out-of-domain)`  

---

## 1. Citation Architecture & Metadata Schema

Generated answers include bracketed inline citations `[1]`, `[2]` attached directly to claims.
Each citation tag maps to a complete metadata payload:
```json
{
  "[1]": {
    "citation_tag": "[1]",
    "chunk_id": "chunk_001",
    "source_document": "hr_remote_policy_raw.txt",
    "chunk_index": 0,
    "section": "Remote Work Eligibility & Equipment",
    "page": 1,
    "similarity_score": 0.8542,
    "source_text_snippet": "..."
  }
}
```

---

## 2. Sample Cited Answers & Source Verification Results

### Sample 1: *"How many days of paid time off do employees get each year, and can unused PTO be rolled over?"*

**Is Fallback**: `False` | **Verification Status**: `True`  

**Generated Answer**:
> Employees accrue 18 days of Paid Time Off (PTO) annually, and up to 5 unused PTO days may be rolled over into the next calendar year.    
>   
> - PTO accrual is 1.5 days per completed calendar month of active service.    
> - Any balance exceeding 5 days on December 31 expires without cash compensation unless HR grants an exception.    
> - Rollover applies only to unused PTO, not to sick leave.    
>   
> [1]

**Citation-to-Source Metadata Mapping**:

| Citation Tag | Chunk ID | Source Document | Section | Page | Score |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **[1]** | `employee_benefits_chunk_001` | employee_benefits.md | Section 6.0: Employee Benefits... | N/A | `0.5269` |
| **[2]** | `employee_benefits_chunk_002` | employee_benefits.md | Section 6.0: Employee Benefits... | N/A | `0.3804` |

**Verification Reason**: *All inline citations successfully verified against retrieved source chunks.*  

---

### Sample 2: *"What are the network encryption and VPN requirements for connecting remotely to company resources?"*

**Is Fallback**: `False` | **Verification Status**: `True`  

**Generated Answer**:
> Employees must connect to company resources through an encrypted VPN and use multi‑factor authentication, which the IT Security Operations team verifies before approval.    
>   
> - The VPN connection must be encrypted (e.g., TLS/SSL).    
> - Multi‑factor authentication (MFA) is required for all remote access.    
> - IT Security confirms compliance with these requirements during the remote‑work application review. [1]

**Citation-to-Source Metadata Mapping**:

| Citation Tag | Chunk ID | Source Document | Section | Page | Score |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **[1]** | `remote_work_policy_chunk_003` | remote_work_policy.md | Section 4.2: Remote Work & Wor... | N/A | `0.6856` |
| **[2]** | `remote_work_policy_chunk_002` | remote_work_policy.md | Section 4.2: Remote Work & Wor... | N/A | `0.6330` |
| **[3]** | `remote_work_policy_chunk_001` | remote_work_policy.md | Section 4.2: Remote Work & Wor... | N/A | `0.6311` |

**Verification Reason**: *All inline citations successfully verified against retrieved source chunks.*  

---

### Sample 3: *"What are the minimum password length requirements and is SMS authentication permitted?"*

**Is Fallback**: `True` | **Verification Status**: `True`  

**Generated Answer**:
> I don't have access to sufficient verified internal policy guidelines to answer this question. Please contact HR at hr@company.com or submit a ticket via the IT Helpdesk portal. (No relevant supporting sources were retrieved from the verified repository).

**Verification Reason**: *No-source fallback safely returned without fabricating citations.*  

---

### Sample 4: *"What is the company policy regarding interplanetary travel subsidies to Mars colonies?"*

**Is Fallback**: `False` | **Verification Status**: `True`  

**Generated Answer**:
> I don't have access to this information. Please contact HR at hr@company.com or submit a ticket via the IT Helpdesk portal.

**Citation-to-Source Metadata Mapping**:

| Citation Tag | Chunk ID | Source Document | Section | Page | Score |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **[1]** | `it_security_policy_chunk_002` | it_security_policy.md | Section 8.1: Corporate IT Secu... | N/A | `0.4144` |
| **[2]** | `it_security_policy_chunk_005` | it_security_policy.md | Section 8.1: Corporate IT Secu... | N/A | `0.4134` |
| **[3]** | `it_security_policy_chunk_003` | it_security_policy.md | Section 8.1: Corporate IT Secu... | N/A | `0.3857` |

**Verification Reason**: *Fallback answer correctly returned without fabricated citations.*  

---

