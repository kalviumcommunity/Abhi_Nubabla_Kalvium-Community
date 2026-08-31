# Corpus Text Extraction Cleaning Pipeline Report

This report documents the performance and before/after evidence of the Text Extraction Cleaning Pipeline across the document corpus.

## 📊 1. Corpus-Wide Performance Metrics

| Document Name | Orig Chars | Clean Chars | Orig Tokens | Clean Tokens | Token Reduction | Total Noise Removed |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `hr_remote_policy_raw.txt` | 2,467 | 1,953 | 513 | 345 | **32.75%** | 40 items |
| `it_security_guide_raw.txt` | 1,637 | 1,273 | 326 | 225 | **30.98%** | 22 items |
| `travel_expense_policy_raw.txt` | 1,426 | 988 | 300 | 177 | **41.0%** | 19 items |
| **CORPUS TOTAL** | **5,530** | **4,214** | **1,139** | **747** | **34.42%** | - |

## 🔍 2. Detailed Noise Breakdown

| Document Name | NFKC Norm | Invisible Chars | Page Numbers | Breadcrumbs | Headers/Footers | Dividers | Hyphens Joined | Sentence Wraps | Blank Lines Collapsed |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `hr_remote_policy_raw.txt` | 6 | 0 | 4 | 1 | 7 | 2 | 2 | 16 | 2 |
| `it_security_guide_raw.txt` | 0 | 0 | 3 | 1 | 2 | 2 | 2 | 9 | 3 |
| `travel_expense_policy_raw.txt` | 0 | 0 | 2 | 1 | 5 | 2 | 1 | 5 | 3 |

---

## 📸 3. Before vs After Samples (Task 4 Evidence)

### Sample 1: `hr_remote_policy_raw.txt`

#### ❌ RAW EXTRACTED TEXT (Before Cleaning):

```text
Home > HR Department > Policies > Remote Work

CONFIDENTIAL & PROPRIETARY — ACME CORP
Acme Corporation Internal HR Policy Guide 2026
Page 1 of 4

==================================================
# Section 4.2: Remote Work & Workplace Flexibility Policy
==================================================

1. Overview & Scope
This policy defines the operational guidelines and security protocols for remote
work arrangements within the organization. It applies to all full-time and
part-time administrative, technical, and operational personnel. Remote work
is a privilege designed to support work-l
... [truncated]
```

#### ✅ CLEANED RETRIEVAL-READY TEXT (After Cleaning):

```text
# Section 4.2: Remote Work & Workplace Flexibility Policy

1. Overview & Scope
This policy defines the operational guidelines and security protocols for remote work arrangements within the organization. It applies to all full-time and part-time administrative, technical, and operational personnel. Remote work is a privilege designed to support work-life balance while ensuring organizational productivity, client confidentiality, and data security remain uncompromised.

2. Eligibility Requirements
To qualify for regular or hybrid remote work:
- The employee must have completed a minimum of 6 mon
... [truncated]
```

---

### Sample 2: `it_security_guide_raw.txt`

#### ❌ RAW EXTRACTED TEXT (Before Cleaning):

```text
Nav: Home / IT Department / Information Security / Access Rules

Doc ID: IT-SEC-9081  |  Page 1

--------------------------------------------------
# IT Security & System Access Guidelines
--------------------------------------------------

1. Password & Authentication Standards
All corporate user accounts MUST utilize multi-factor authentication (MFA)
with mandatory hardware token or push notification verification. Passwords must
be at least 16 characters in length, containing a mix of uppercase letters,
lowercase letters, numbers, and special characters.

Doc ID: IT-SEC-9081  |  Page 2

2. V
... [truncated]
```

#### ✅ CLEANED RETRIEVAL-READY TEXT (After Cleaning):

```text
# IT Security & System Access Guidelines

1. Password & Authentication Standards
All corporate user accounts MUST utilize multi-factor authentication (MFA) with mandatory hardware token or push notification verification. Passwords must be at least 16 characters in length, containing a mix of uppercase letters, lowercase letters, numbers, and special characters.

2. Virtual Private Network (VPN) Usage
Employees accessing corporate resources remotely are required to establish an encrypted VPN session using approved corporate credentials. Split-tunneling is strictly prohibited to ensure all traff
... [truncated]
```

---

### Sample 3: `travel_expense_policy_raw.txt`

#### ❌ RAW EXTRACTED TEXT (Before Cleaning):

```text
Navigation: Home > Finance > Corporate Policies > Travel & Reimbursements

*** ACME CORP TRAVEL & EXPENSE POLICY 2026 ***
- Page 1 -

==================================================
# Travel & Business Expense Reimbursement Policy
==================================================

1. Expense Eligibility & Guidelines
Employees traveling on official company business are entitled to full reim-
bursement for legitimate, documented, and pre-approved travel expenses. All expense
reports must be submitted via the Ｆｉｎａｎｃｅ Portal within 30 days of trip completion.

- Page 2 -

*** ACME CORP TRAVEL 
... [truncated]
```

#### ✅ CLEANED RETRIEVAL-READY TEXT (After Cleaning):

```text
# Travel & Business Expense Reimbursement Policy

1. Expense Eligibility & Guidelines
Employees traveling on official company business are entitled to full reimbursement for legitimate, documented, and pre-approved travel expenses. All expense reports must be submitted via the Finance Portal within 30 days of trip completion.

2. Lodging & Per Diem Allowance
Daily meal per diem limits are established based on the destination city tier. Domestic travel per diem is capped at $75 per day, while international destination caps vary by location schedule. Lodging expenses must not exceed standard bus
... [truncated]
```

---

## 💡 4. Conclusion & Retrieval Benefits

1. **Noise-Free Vector Embeddings**: Stripping page numbers, header banners, and disclaimers prevents semantic vector matches on irrelevant boilerplate.
2. **Seamless Chunk Coherence**: Rejoining broken line wraps and split hyphen words restores context continuity across vector chunk boundaries.
3. **Token & Cost Efficiency**: Cleaned text saves **~10-25% in token consumption**, lowering LLM prompt costs while increasing high-value context density.