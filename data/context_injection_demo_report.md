# Context Injection & Augmented Prompt Demonstration Report
**Generated:** 2026-09-07T13:29:52.197529
**Query:** What are the paid time off policies for full-time employees?
**Grounding Style:** Professional

---
## Stage 1: Retrieved Chunks
Initial retrieval results from vector similarity search:

| Rank | Score | Source | Tokens |
|------|-------|--------|--------|
| 1 | employee_benefits_chunk_004 | employee_benefits.md | 80 |
| 2 | employee_benefits_chunk_001 | employee_benefits.md | 85 |
| 3 | it_security_policy_chunk_005 | it_security_policy.md | 107 |
| 4 | remote_work_policy_chunk_006 | remote_work_policy.md | 68 |
| 5 | remote_work_policy_chunk_002 | remote_work_policy.md | 100 |

## Stage 2: Token Budget Analysis
**Model:** gpt-3.5-turbo
**Max Tokens:** 4096
**Context Budget (50%):** 2048

### Token Allocation
- Grounding Instructions: 106 tokens
- Context (Chunks): 440 tokens
- User Question: 13 tokens
- Reserved for Answer: 1000 tokens
- **Total: 1559 tokens**

✓ **Budget Status:** OK (1608 tokens remaining)

## Stage 3: Source Markers
Chunks are annotated with source markers [1], [2], etc. for citation:

### [1] (employee_benefits.md - Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 4. Health Insurance & Wellness Reimbursement)
- **Chunk ID:** employee_benefits_chunk_004
- **Section:** Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 4. Health Insurance & Wellness Reimbursement
- **Tokens:** 80
- **Text:** The company sponsors 90% of the premium for comprehensive medical, dental, and vision insurance for ...

### [2] (employee_benefits.md - Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 1. Paid Time Off (PTO) Accrual)
- **Chunk ID:** employee_benefits_chunk_001
- **Section:** Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 1. Paid Time Off (PTO) Accrual
- **Tokens:** 85
- **Text:** Full-time regular employees accrue 18 days of Paid Time Off annually, calculated at a rate of 1.5 da...

### [3] (it_security_policy.md - Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure)
- **Chunk ID:** it_security_policy_chunk_005
- **Section:** Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure
- **Tokens:** 107
- **Text:** If you suspect an active security compromise, credential theft, or phishing email:
1. Immediately di...

### [4] (remote_work_policy.md - Section 4.2: Remote Work & Workplace Flexibility Policy > 5. Working Hours, Availability & Communication)
- **Chunk ID:** remote_work_policy_chunk_006
- **Section:** Section 4.2: Remote Work & Workplace Flexibility Policy > 5. Working Hours, Availability & Communication
- **Tokens:** 68
- **Text:** Remote employees are expected to maintain core operational hours from 9:00 AM to 5:00 PM local time....

### [5] (remote_work_policy.md - Section 4.2: Remote Work & Workplace Flexibility Policy > 2. Eligibility Requirements)
- **Chunk ID:** remote_work_policy_chunk_002
- **Section:** Section 4.2: Remote Work & Workplace Flexibility Policy > 2. Eligibility Requirements
- **Tokens:** 100
- **Text:** To qualify for regular or hybrid remote work:
- The employee must have completed a minimum of 6 mont...


## Stage 4: Grounding Instructions
The following instructions are prepended to enforce context-only answering:

```
You are a professional assistant answering based on company policies and documentation.

**Context Guidelines:**
1. Provide accurate, sourced answers from the official documentation provided below.
2. Use source citations [1], [2], etc., to indicate where information comes from.
3. When information is incomplete or ambiguous in the documentation, acknowledge this limitation.
4. Follow the hierarchy: documented policy > supporting context > admit insufficient information.
5. Format answers clearly with proper citations and section references.
6. For policy questions, prioritize accuracy over brevity.

```

## Stage 5: Complete Augmented Prompt
Full prompt ready for LLM inference:

```
You are a professional assistant answering based on company policies and documentation.

**Context Guidelines:**
1. Provide accurate, sourced answers from the official documentation provided below.
2. Use source citations [1], [2], etc., to indicate where information comes from.
3. When information is incomplete or ambiguous in the documentation, acknowledge this limitation.
4. Follow the hierarchy: documented policy > supporting context > admit insufficient information.
5. Format answers clearly with proper citations and section references.
6. For policy questions, prioritize accuracy over brevity.


---

**Context:**
[1] (employee_benefits.md - Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 4. Health Insurance & Wellness Reimbursement)
The company sponsors 90% of the premium for comprehensive medical, dental, and vision insurance for full-time employees and 70% for enrolled dependents. In addition, each employee is eligible for an annual \$600 wellness stipend to cover gym memberships, mental health counseling, fitness equipment, or ergonomic home office furniture. Claims must be submitted with valid receipts before November 30 of each calendar year.

[2] (employee_benefits.md - Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 1. Paid Time Off (PTO) Accrual)
Full-time regular employees accrue 18 days of Paid Time Off annually, calculated at a rate of 1.5 days per completed calendar month of active service. Employees may roll over a maximum of 5 unused PTO days into the following calendar year. Any unused balance exceeding 5 days on December 31 will expire without cash compensation, unless an exception is approved by HR due to operational necessity.

[3] (it_security_policy.md - Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure)
If you suspect an active security compromise, credential theft, or phishing email:
1. Immediately disconnect your machine from the network (unplug Ethernet or turn off Wi-Fi).
2. Do not power off or reboot the computer, as volatile RAM evidence must be preserved for forensic analysis.
3. Call the 24/7 IT Security Hotline at extension 4357 (HELP) or alert the `#security-incident` Slack channel using a secondary mobile device.
4. Provide the time of occurrence, observed system symptoms, and suspicious email headers or files involved.

[4] (remote_work_policy.md - Section 4.2: Remote Work & Workplace Flexibility Policy > 5. Working Hours, Availability & Communication)
Remote employees are expected to maintain core operational hours from 9:00 AM to 5:00 PM local time. Employees must remain reachable via official communication channels (Slack, Microsoft Teams, corporate email) during working hours. Any scheduled absence or temporary unavailability must be logged in the shared department calendar at least 24 hours in advance.

[5] (remote_work_policy.md - Section 4.2: Remote Work & Workplace Flexibility Policy > 2. Eligibility Requirements)
To qualify for regular or hybrid remote work:
- The employee must have completed a minimum of 6 months of continuous full-time employment.
- The employee's latest performance evaluation rating must meet or exceed 'Satisfactory' standards.
- The employee's role must be classified as 'Remote-Eligible' by the Department Head. Roles requiring mandatory physical presence (e.g., facilities maintenance, hardware support, physical security) are excluded.
- The employee must maintain a dedicated, private home workspace free from background disruptions.

---

**Question:** What are the paid time off policies for full-time employees?

**Answer:**
```

## Key Insights
1. **Context Injection:** Retrieved chunks are injected with source markers [1], [2], etc.
2. **Token Enforcement:** Total token count stays within model's capacity with buffer for answer.
3. **Source Attribution:** Each chunk is labeled with its source for traceability.
4. **Grounding Instructions:** Model is instructed to use ONLY provided context.
5. **Citation Discipline:** Model should reference sources when claiming facts.
