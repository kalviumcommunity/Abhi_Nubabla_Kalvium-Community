# Full RAG System Evaluation & Answer Quality Scoring Report

**Overall Quality Score**: `76.1%`  
**Total Queries Evaluated**: `8`  
**Timestamp**: `2026-09-10T13:28:11.951991`  

---

## 1. Executive Quality Summary

| Evaluation Metric | Score | Target Threshold | Status |
| :--- | :---: | :---: | :---: |
| **Factual Correctness** | `68.8%` | 85.0% | ⚠️ Needs Review |
| **Context Grounding** | `73.1%` | 90.0% | ⚠️ Needs Review |
| **Citation Precision** | `100.0%` | 90.0% | ✅ Pass |
| **Citation Recall** | `93.8%` | 80.0% | ✅ Pass |
| **Fallback Accuracy** | `100.0%` | 100.0% | ✅ Pass |

---

## 2. Test Set Benchmark Results

### `eval_q01_pto_accrual`: *"How many days of paid time off do employees get each year, and can unused PTO be rolled over into the next year?"*

- **Category**: Factual Policy | **Fallback**: `False`  
- **Correctness**: `100.0%` | **Grounding**: `60.0%` | **Citation Precision**: `100.0%`  

**Generated Answer**:
> Full‑time regular employees accrue 18 days of PTO annually, and up to 5 unused days may be rolled over into the next calendar year.    
>   
> - PTO accrues at 1.5 days per completed calendar month of active service.    
> - Any balance exceeding 5 days on December 31 will expire without cash compensation unless HR approves an exception.    
> - Sick leave is separate and not counted toward PTO.    
>   
> [1]

**Citations Found**: `['[1]']`  

---

### `eval_q02_sick_leave`: *"What is the policy for taking sick leave and when is a medical certificate required?"*

- **Category**: Factual Policy | **Fallback**: `False`  
- **Correctness**: `75.0%` | **Grounding**: `75.0%` | **Citation Precision**: `100.0%`  

**Generated Answer**:
> Employees receive 10 dedicated sick days per calendar year, available from day one, with no advance notice required in emergencies but a manager must be notified before 09:00 local time, and a medical certificate is required for absences exceeding three consecutive working days.    
>   
> - 10 sick days per calendar year, usable from the first day of employment.    
> - No advance notice needed for emergencies; notify manager before 09:00 local time.    
> - Medical certificate required for absences longer than 3 consecutive working days. [1]

**Citations Found**: `['[1]']`  

---

### `eval_q03_remote_security`: *"What are the network encryption and VPN requirements for connecting remotely to company resources?"*

- **Category**: Procedural Security | **Fallback**: `False`  
- **Correctness**: `75.0%` | **Grounding**: `0.0%` | **Citation Precision**: `100.0%`  

**Generated Answer**:
> Employees must connect to company resources through an encrypted VPN that is verified by IT Security and must use multi‑factor authentication.    
>   
> - Use an encrypted VPN connection for all remote access.    
> - Enable multi‑factor authentication (MFA) on the VPN.    
> - IT Security Operations verifies that the home office setup meets these encryption and MFA requirements before approval. [1]

**Citations Found**: `['[1]']`  

---

### `eval_q04_equipment_stipend`: *"What equipment does the company provide for remote workers and what is the reimbursement stipend?"*

- **Category**: Factual Policy | **Fallback**: `False`  
- **Correctness**: `0.0%` | **Grounding**: `100.0%` | **Citation Precision**: `100.0%`  

**Generated Answer**:
> I don't have access to this information. Please contact HR at hr@company.com or submit a ticket via the IT Helpdesk portal.

**Citations Found**: `[]`  

---

### `eval_q05_mars_travel_fallback`: *"What is the company policy regarding interplanetary travel subsidies to Mars colonies?"*

- **Category**: Out-Of-Domain Fallback | **Fallback**: `True`  
- **Correctness**: `100.0%` | **Grounding**: `100.0%` | **Citation Precision**: `100.0%`  

**Generated Answer**:
> I don't have access to sufficient verified internal policy guidelines to answer this question. Please contact HR at hr@company.com or submit a ticket via the IT Helpdesk portal. (No relevant supporting sources were retrieved from the verified repository).

**Citations Found**: `[]`  

---

### `eval_q06_password_policy`: *"What are the minimum password length requirements and is SMS authentication permitted?"*

- **Category**: Procedural Security | **Fallback**: `True`  
- **Correctness**: `0.0%` | **Grounding**: `100.0%` | **Citation Precision**: `100.0%`  

**Generated Answer**:
> I don't have access to sufficient verified internal policy guidelines to answer this question. Please contact HR at hr@company.com or submit a ticket via the IT Helpdesk portal. (No relevant supporting sources were retrieved from the verified repository).

**Citations Found**: `[]`  

---

### `eval_q07_stock_options_fallback`: *"What is the vesting schedule and exercise window for executive stock option grants?"*

- **Category**: Out-Of-Domain Fallback | **Fallback**: `True`  
- **Correctness**: `100.0%` | **Grounding**: `100.0%` | **Citation Precision**: `100.0%`  

**Generated Answer**:
> I don't have access to sufficient verified internal policy guidelines to answer this question. Please contact HR at hr@company.com or submit a ticket via the IT Helpdesk portal. (No relevant supporting sources were retrieved from the verified repository).

**Citations Found**: `[]`  

---

### `eval_q08_parental_leave`: *"How many weeks of fully paid parental leave are provided for primary caregivers?"*

- **Category**: Factual Policy | **Fallback**: `False`  
- **Correctness**: `100.0%` | **Grounding**: `50.0%` | **Citation Precision**: `100.0%`  

**Generated Answer**:
> Primary caregivers are entitled to **16 weeks of fully paid parental leave**.    
> - Must be taken within the first 12 months after the qualifying event.    
> - Can be taken as one continuous block or split into two blocks with supervisory approval.    
> - Health insurance benefits remain uninterrupted during the leave. [1]

**Citations Found**: `['[1]']`  

---

## 3. Notable Failures & Root-Cause Diagnosis

### ❌ Failure Case: `eval_q01_pto_accrual` (Partial Grounding / Extrapolated Claim)

- **Severity**: `Medium`  
- **Observed Issue**: Answer contained 2 unsupported claims.  
- **Likely Cause**: Generator extrapolated beyond injected context details.  
- **Recommended Fix**: Lower temperature parameter (e.g. 0.0 - 0.1) and enforce strict grounding system prompt.  

### ❌ Failure Case: `eval_q03_remote_security` (Partial Grounding / Extrapolated Claim)

- **Severity**: `Medium`  
- **Observed Issue**: Answer contained 4 unsupported claims.  
- **Likely Cause**: Generator extrapolated beyond injected context details.  
- **Recommended Fix**: Lower temperature parameter (e.g. 0.0 - 0.1) and enforce strict grounding system prompt.  

### ❌ Failure Case: `eval_q04_equipment_stipend` (Retrieval Miss / Incorrect Coverage)

- **Severity**: `High`  
- **Observed Issue**: Answer missed key expected ground-truth facts: ['laptop', 'monitor', '$500', 'stipend', 'home office']  
- **Likely Cause**: Top-k retrieval missed essential chunk context or chunk granularity lost key facts.  
- **Recommended Fix**: Increase top-k retrieval parameter (e.g. k=5) or refine semantic embedding model.  

### ❌ Failure Case: `eval_q06_password_policy` (Retrieval Miss / Incorrect Coverage)

- **Severity**: `High`  
- **Observed Issue**: Answer missed key expected ground-truth facts: ['14 characters', 'sms', 'disallowed', 'authenticator app', 'hardware']  
- **Likely Cause**: Top-k retrieval missed essential chunk context or chunk granularity lost key facts.  
- **Recommended Fix**: Increase top-k retrieval parameter (e.g. k=5) or refine semantic embedding model.  

### ❌ Failure Case: `eval_q08_parental_leave` (Partial Grounding / Extrapolated Claim)

- **Severity**: `Medium`  
- **Observed Issue**: Answer contained 2 unsupported claims.  
- **Likely Cause**: Generator extrapolated beyond injected context details.  
- **Recommended Fix**: Lower temperature parameter (e.g. 0.0 - 0.1) and enforce strict grounding system prompt.  

