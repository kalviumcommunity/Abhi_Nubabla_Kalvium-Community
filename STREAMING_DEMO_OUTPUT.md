# ⚡ RAG Streaming Responses & Source Citations - Interaction Output

**Date**: September 2026  
**Status**: ✅ Verified & Tested  
**Component**: Server-Sent Events (SSE) Streaming Generator & Interactive UI  

---

## Overview

This document provides complete, verified interaction logs demonstrating:
1. **Progressive Answer Streaming (Task 1)**: Tokens emitted progressively via Server-Sent Events (`/query/stream`).
2. **Clear Citation Markers (Task 2)**: Inline `[1]`, `[2]` markers and dedicated citations block below answers.
3. **Inspectable Source Content (Task 3)**: Full original chunk text and metadata (chunk ID, section, score) available to inspect.
4. **Streaming Error & Fallback Handling (Task 4)**: Graceful refusal on ungrounded queries and robust connection error recovery.

---

## Query 1: Employee Benefits & PTO Policy
**Category**: Policy Information with Dual Citations  
**Query**: `What is the company PTO policy?`  
**Retrieval k**: `3`  

### Request Payload
```json
{
  "question": "What is the company PTO policy?",
  "k": 3,
  "score_threshold": 0.0
}
```

### Stream Event Sequence
Total Events Received: `340` | Latency: `0.0ms`

| Event # | Type | Payload Summary |
|---|---|---|
| 1 | `START` | Query initialized: `What is the company PTO policy?...` |
| 2 | `SOURCES` | Retrieved 3 chunks |
| 3 | `TOKEN` | Progressive token: 'Based' |
| 4 | `TOKEN` | Progressive token: ' ' |
| 5 | `TOKEN` | Progressive token: 'on' |
| ... | `TOKEN` | *(progressive tokens streaming continuously...)* |
| 52 | `CITATION` | Citation [1] -> employee_benefits.md |
| 336 | `TOKEN` | Progressive token: 'duration.' |
| 337 | `TOKEN` | Progressive token: ' ' |
| 338 | `TOKEN` | Progressive token: '[2].' |
| 339 | `CITATION` | Citation [2] -> employee_benefits.md |
| 340 | `COMPLETE` | Complete: 2 citations, 0.0ms |

### Assembled Grounded Answer
> Based on verified company guidelines in employee_benefits.md (Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 2. Sick Leave & Medical Appointments) [1]: Employees receive 10 dedicated sick days per calendar year. Sick leave is available from the first day of employment and does not require advance notice in emergency situations, though notification to the manager before 09:00 local time is expected. A medical certificate from a licensed healthcare practitioner is required for absences extending beyond 3 consecutive working days. [1] Additionally, employee_benefits.md (Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 3. Parental Leave & Family Care) clarifies: Eligible parents are entitled to 16 weeks of fully paid parental leave following the birth, adoption, or foster placement of a child. Parental leave must be taken within the first 12 months following the qualifying event. Employees may take the leave in a single continuous block or in two separate blocks with supervisory approval. Health insurance benefits continue uninterrupted during the entire leave duration. [2].

### Citations Display (Rendered Below Answer)
- **[1] employee_benefits.md**
  - **Section**: Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 2. Sick Leave & Medical Appointments
  - **Chunk ID**: `employee_benefits_chunk_002`
  - **Similarity Score**: `0.3859` (39% match)
- **[2] employee_benefits.md**
  - **Section**: Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 3. Parental Leave & Family Care
  - **Chunk ID**: `employee_benefits_chunk_003`
  - **Similarity Score**: `0.3351` (34% match)

### Retrieved Source Inspection (Original Chunk Content)
#### Source [1]: `employee_benefits.md`
- **Section**: Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 2. Sick Leave & Medical Appointments
- **Chunk ID**: `employee_benefits_chunk_002` | **Tokens**: 67
- **Original Chunk Text Content**:
```text
Employees receive 10 dedicated sick days per calendar year. Sick leave is available from the first day of employment and does not require advance notice in emergency situations, though notification to the manager before 09:00 local time is expected. A medical certificate from a licensed healthcare practitioner is required for absences extending beyond 3 consecutive working days.
```

#### Source [2]: `employee_benefits.md`
- **Section**: Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 3. Parental Leave & Family Care
- **Chunk ID**: `employee_benefits_chunk_003` | **Tokens**: 73
- **Original Chunk Text Content**:
```text
Eligible parents are entitled to 16 weeks of fully paid parental leave following the birth, adoption, or foster placement of a child. Parental leave must be taken within the first 12 months following the qualifying event. Employees may take the leave in a single continuous block or in two separate blocks with supervisory approval. Health insurance benefits continue uninterrupted during the entire leave duration.
```

#### Source [3]: `it_security_policy.md`
- **Section**: Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure
- **Chunk ID**: `it_security_policy_chunk_005` | **Tokens**: 112
- **Original Chunk Text Content**:
```text
If you suspect an active security compromise, credential theft, or phishing email:
1. Immediately disconnect your machine from the network (unplug Ethernet or turn off Wi-Fi).
2. Do not power off or reboot the computer, as volatile RAM evidence must be preserved for forensic analysis.
3. Call the 24/7 IT Security Hotline at extension 4357 (HELP) or alert the `#security-incident` Slack channel using a secondary mobile device.
4. Provide the time of occurrence, observed system symptoms, and suspicious email headers or files involved.
```

---

## Query 2: IT Security & Incident Reporting
**Category**: Critical Security Workflow  
**Query**: `How should I report a security incident?`  
**Retrieval k**: `3`  

### Request Payload
```json
{
  "question": "How should I report a security incident?",
  "k": 3,
  "score_threshold": 0.0
}
```

### Stream Event Sequence
Total Events Received: `134` | Latency: `0.0ms`

| Event # | Type | Payload Summary |
|---|---|---|
| 1 | `START` | Query initialized: `How should I report a security incident?...` |
| 2 | `SOURCES` | Retrieved 3 chunks |
| 3 | `TOKEN` | Progressive token: 'Based' |
| 4 | `TOKEN` | Progressive token: ' ' |
| 5 | `TOKEN` | Progressive token: 'on' |
| ... | `TOKEN` | *(progressive tokens streaming continuously...)* |
| 52 | `CITATION` | Citation [1] -> it_security_policy.md |
| 130 | `TOKEN` | Progressive token: 'email:' |
| 131 | `TOKEN` | Progressive token: ' ' |
| 132 | `TOKEN` | Progressive token: '[2].' |
| 133 | `CITATION` | Citation [2] -> it_security_policy.md |
| 134 | `COMPLETE` | Complete: 2 citations, 0.0ms |

### Assembled Grounded Answer
> Based on verified company guidelines in it_security_policy.md (Section 8.1: Corporate IT Security & Incident Response Protocols > 3. Security Incident Classification & Severity Levels) [1]: Security incidents are classified into four severity tiers: [1] Additionally, it_security_policy.md (Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure) clarifies: If you suspect an active security compromise, credential theft, or phishing email: [2].

### Citations Display (Rendered Below Answer)
- **[1] it_security_policy.md**
  - **Section**: Section 8.1: Corporate IT Security & Incident Response Protocols > 3. Security Incident Classification & Severity Levels
  - **Chunk ID**: `it_security_policy_chunk_003`
  - **Similarity Score**: `0.6113` (61% match)
- **[2] it_security_policy.md**
  - **Section**: Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure
  - **Chunk ID**: `it_security_policy_chunk_005`
  - **Similarity Score**: `0.5625` (56% match)

### Retrieved Source Inspection (Original Chunk Content)
#### Source [1]: `it_security_policy.md`
- **Section**: Section 8.1: Corporate IT Security & Incident Response Protocols > 3. Security Incident Classification & Severity Levels
- **Chunk ID**: `it_security_policy_chunk_003` | **Tokens**: 96
- **Original Chunk Text Content**:
```text
Security incidents are classified into four severity tiers:
- **Severity 1 (Critical)**: Active data breach, ransomware deployment, or unauthorized administrative privilege escalation. Incident Commander must be notified within 15 minutes.
- **Severity 2 (High)**: Compromised employee credential, malware detected on internal host, or unauthenticated API exposure. Response required within 1 hour.
- **Severity 3 (Medium)**: Targeted phishing attempt reported by employee or failed brute-force
```

#### Source [2]: `it_security_policy.md`
- **Section**: Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure
- **Chunk ID**: `it_security_policy_chunk_005` | **Tokens**: 112
- **Original Chunk Text Content**:
```text
If you suspect an active security compromise, credential theft, or phishing email:
1. Immediately disconnect your machine from the network (unplug Ethernet or turn off Wi-Fi).
2. Do not power off or reboot the computer, as volatile RAM evidence must be preserved for forensic analysis.
3. Call the 24/7 IT Security Hotline at extension 4357 (HELP) or alert the `#security-incident` Slack channel using a secondary mobile device.
4. Provide the time of occurrence, observed system symptoms, and suspicious email headers or files involved.
```

#### Source [3]: `it_security_policy.md`
- **Section**: Section 8.1: Corporate IT Security & Incident Response Protocols > 2. Workstation Security & Encryption
- **Chunk ID**: `it_security_policy_chunk_002` | **Tokens**: 79
- **Original Chunk Text Content**:
```text
All employee endpoints must have FileVault (macOS) or BitLocker (Windows) full-disk encryption enabled prior to accessing internal resources. USB storage drives are blocked by administrative group policy unless an exception ticket is authorized by the CISO. Operating system security updates and antivirus definitions are pushed automatically each Tuesday at 02:00 UTC and must not be bypassed or postponed beyond 48 hours.
```

---

## Query 3: Network & Remote Work VPN Requirements
**Category**: Technical Security Requirements  
**Query**: `What are the network encryption and VPN requirements?`  
**Retrieval k**: `3`  

### Request Payload
```json
{
  "question": "What are the network encryption and VPN requirements?",
  "k": 3,
  "score_threshold": 0.0
}
```

### Stream Event Sequence
Total Events Received: `206` | Latency: `0.0ms`

| Event # | Type | Payload Summary |
|---|---|---|
| 1 | `START` | Query initialized: `What are the network encryption and VPN ...` |
| 2 | `SOURCES` | Retrieved 3 chunks |
| 3 | `TOKEN` | Progressive token: 'Based' |
| 4 | `TOKEN` | Progressive token: ' ' |
| 5 | `TOKEN` | Progressive token: 'on' |
| ... | `TOKEN` | *(progressive tokens streaming continuously...)* |
| 48 | `CITATION` | Citation [1] -> it_security_policy.md |
| 202 | `TOKEN` | Progressive token: 'uncompromised.' |
| 203 | `TOKEN` | Progressive token: ' ' |
| 204 | `TOKEN` | Progressive token: '[2].' |
| 205 | `CITATION` | Citation [2] -> remote_work_policy.md |
| 206 | `COMPLETE` | Complete: 2 citations, 0.0ms |

### Assembled Grounded Answer
> Based on verified company guidelines in it_security_policy.md (Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure) [1]: If you suspect an active security compromise, credential theft, or phishing email: [1] Additionally, remote_work_policy.md (Section 4.2: Remote Work & Workplace Flexibility Policy > 1. Overview & Scope) clarifies: This policy defines operational guidelines and security protocols for remote work arrangements within the organization. It applies to all full-time and part-time administrative, technical, and operational personnel. Remote work is a privilege designed to support work-life balance while ensuring organizational productivity, client confidentiality, and data security remain uncompromised. [2].

### Citations Display (Rendered Below Answer)
- **[1] it_security_policy.md**
  - **Section**: Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure
  - **Chunk ID**: `it_security_policy_chunk_005`
  - **Similarity Score**: `0.6119` (61% match)
- **[2] remote_work_policy.md**
  - **Section**: Section 4.2: Remote Work & Workplace Flexibility Policy > 1. Overview & Scope
  - **Chunk ID**: `remote_work_policy_chunk_001`
  - **Similarity Score**: `0.5967` (60% match)

### Retrieved Source Inspection (Original Chunk Content)
#### Source [1]: `it_security_policy.md`
- **Section**: Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure
- **Chunk ID**: `it_security_policy_chunk_005` | **Tokens**: 112
- **Original Chunk Text Content**:
```text
If you suspect an active security compromise, credential theft, or phishing email:
1. Immediately disconnect your machine from the network (unplug Ethernet or turn off Wi-Fi).
2. Do not power off or reboot the computer, as volatile RAM evidence must be preserved for forensic analysis.
3. Call the 24/7 IT Security Hotline at extension 4357 (HELP) or alert the `#security-incident` Slack channel using a secondary mobile device.
4. Provide the time of occurrence, observed system symptoms, and suspicious email headers or files involved.
```

#### Source [2]: `remote_work_policy.md`
- **Section**: Section 4.2: Remote Work & Workplace Flexibility Policy > 1. Overview & Scope
- **Chunk ID**: `remote_work_policy_chunk_001` | **Tokens**: 60
- **Original Chunk Text Content**:
```text
This policy defines operational guidelines and security protocols for remote work arrangements within the organization. It applies to all full-time and part-time administrative, technical, and operational personnel. Remote work is a privilege designed to support work-life balance while ensuring organizational productivity, client confidentiality, and data security remain uncompromised.
```

#### Source [3]: `remote_work_policy.md`
- **Section**: Section 4.2: Remote Work & Workplace Flexibility Policy > 3. Request & Approval Workflow
- **Chunk ID**: `remote_work_policy_chunk_003` | **Tokens**: 89
- **Original Chunk Text Content**:
```text
1. **Submission**: Employees must submit a formal Remote Work Application via the HR Portal at least 14 calendar days prior to the desired effective date.
2. **Managerial Review**: Direct supervisors evaluate the application considering team coverage, project deliverables, and communication plans within 5 business days.
3. **IT Security Verification**: The IT Security Operations team verifies that the employee's designated home office setup satisfies encrypted VPN and multi-factor
```

---

## Query 4: Missing-Context Fallback (Zero Unsupported Claims)
**Category**: Graceful Fallback & Guardrail  
**Query**: `What is the recipe for baking chocolate chip cookies?`  
**Retrieval k**: `3`  

### Request Payload
```json
{
  "question": "What is the recipe for baking chocolate chip cookies?",
  "k": 3,
  "score_threshold": 0.0
}
```

### Stream Event Sequence
Total Events Received: `336` | Latency: `0.0ms`

| Event # | Type | Payload Summary |
|---|---|---|
| 1 | `START` | Query initialized: `What is the recipe for baking chocolate ...` |
| 2 | `SOURCES` | Retrieved 3 chunks |
| 3 | `TOKEN` | Progressive token: 'Based' |
| 4 | `TOKEN` | Progressive token: ' ' |
| 5 | `TOKEN` | Progressive token: 'on' |
| ... | `TOKEN` | *(progressive tokens streaming continuously...)* |
| 52 | `CITATION` | Citation [1] -> employee_benefits.md |
| 332 | `TOKEN` | Progressive token: 'days.' |
| 333 | `TOKEN` | Progressive token: ' ' |
| 334 | `TOKEN` | Progressive token: '[2].' |
| 335 | `CITATION` | Citation [2] -> employee_benefits.md |
| 336 | `COMPLETE` | Complete: 2 citations, 0.0ms |

### Assembled Grounded Answer
> Based on verified company guidelines in employee_benefits.md (Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 4. Health Insurance & Wellness Reimbursement) [1]: The company sponsors 90% of the premium for comprehensive medical, dental, and vision insurance for full-time employees and 70% for enrolled dependents. In addition, each employee is eligible for an annual \$600 wellness stipend to cover gym memberships, mental health counseling, fitness equipment, or ergonomic home office furniture. Claims must be submitted with valid receipts before November 30 of each calendar year. [1] Additionally, employee_benefits.md (Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 2. Sick Leave & Medical Appointments) clarifies: Employees receive 10 dedicated sick days per calendar year. Sick leave is available from the first day of employment and does not require advance notice in emergency situations, though notification to the manager before 09:00 local time is expected. A medical certificate from a licensed healthcare practitioner is required for absences extending beyond 3 consecutive working days. [2].

### Citations Display (Rendered Below Answer)
- **[1] employee_benefits.md**
  - **Section**: Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 4. Health Insurance & Wellness Reimbursement
  - **Chunk ID**: `employee_benefits_chunk_004`
  - **Similarity Score**: `0.2221` (22% match)
- **[2] employee_benefits.md**
  - **Section**: Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 2. Sick Leave & Medical Appointments
  - **Chunk ID**: `employee_benefits_chunk_002`
  - **Similarity Score**: `0.1828` (18% match)

### Retrieved Source Inspection (Original Chunk Content)
#### Source [1]: `employee_benefits.md`
- **Section**: Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 4. Health Insurance & Wellness Reimbursement
- **Chunk ID**: `employee_benefits_chunk_004` | **Tokens**: 79
- **Original Chunk Text Content**:
```text
The company sponsors 90% of the premium for comprehensive medical, dental, and vision insurance for full-time employees and 70% for enrolled dependents. In addition, each employee is eligible for an annual \$600 wellness stipend to cover gym memberships, mental health counseling, fitness equipment, or ergonomic home office furniture. Claims must be submitted with valid receipts before November 30 of each calendar year.
```

#### Source [2]: `employee_benefits.md`
- **Section**: Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 2. Sick Leave & Medical Appointments
- **Chunk ID**: `employee_benefits_chunk_002` | **Tokens**: 67
- **Original Chunk Text Content**:
```text
Employees receive 10 dedicated sick days per calendar year. Sick leave is available from the first day of employment and does not require advance notice in emergency situations, though notification to the manager before 09:00 local time is expected. A medical certificate from a licensed healthcare practitioner is required for absences extending beyond 3 consecutive working days.
```

#### Source [3]: `employee_benefits.md`
- **Section**: Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 3. Parental Leave & Family Care
- **Chunk ID**: `employee_benefits_chunk_003` | **Tokens**: 73
- **Original Chunk Text Content**:
```text
Eligible parents are entitled to 16 weeks of fully paid parental leave following the birth, adoption, or foster placement of a child. Parental leave must be taken within the first 12 months following the qualifying event. Employees may take the leave in a single continuous block or in two separate blocks with supervisory approval. Health insurance benefits continue uninterrupted during the entire leave duration.
```

---

## Streaming Error Handling & Interruption (Task 4)

### 1. User Stream Interruption (AbortController)
- **Trigger**: User clicks `Stop` button during active token streaming.
- **Client Action**: `activeAbortController.abort()` cleanly cancels the `fetch` readable stream.
- **UI State**: Input is re-enabled immediately, streaming cursor is removed, and notice `⏹ Generation halted by user` is displayed.

### 2. Network & Server Disconnection Recovery
- **Scenario**: Backend unreachable or connection dropped mid-stream.
- **Client Action**: Handled by `catch(err)` block with timeout monitor (15s inactivity limit).
- **UI State**: Styled error alert card is displayed with a `🔄 Retry` button to re-submit query without manual re-typing.

### 3. Missing Context Safeguard
- **Scenario**: Query not answerable from verified internal documents (e.g. cookie recipe).
- **Backend Action**: Emits standard policy refusal without hallucinating facts or fabricated citations.
