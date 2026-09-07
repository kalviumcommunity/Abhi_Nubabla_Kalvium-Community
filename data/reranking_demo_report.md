# Chunk Re-Ranking Demonstration Report
**Reranker Used:** SemanticRelevanceReranker
**Initial Candidates (k_candidate):** 10
**Final Results (k_final):** 3
**Query:** How many days of paid time off do employees get each year?

---
## Stage 1: Initial Retrieval (Vector Similarity)
Candidates retrieved and ranked by cosine similarity:

| Rank | Vector Score | Chunk ID | Token Count | Source Document |
|------|--------------|----------|-------------|------------------|
| 1 | 0.507166 | employee_benefits_chunk_001 | 79 | employee_benefits.md |
| 2 | 0.257980 | employee_benefits_chunk_002 | 67 | employee_benefits.md |
| 3 | 0.158830 | remote_work_policy_chunk_006 | 68 | remote_work_policy.md |
| 4 | 0.252493 | employee_benefits_chunk_004 | 79 | employee_benefits.md |
| 5 | 0.104071 | remote_work_policy_chunk_003 | 89 | remote_work_policy.md |
| 6 | 0.122270 | remote_work_policy_chunk_002 | 101 | remote_work_policy.md |
| 7 | 0.122662 | employee_benefits_chunk_003 | 73 | employee_benefits.md |
| 8 | 0.104732 | guide_chunk_002 | 53 | guide.md |
| 9 | 0.107007 | hello_chunk_001 | 61 | hello.txt |
| 10 | 0.128975 | page_chunk_004 | 5 | page.html |


## Stage 2: Re-Ranking Results
Candidates re-ranked by semantic relevance:

| Rank | Re-rank Score | Vector Score | Chunk ID | Improvement |
|------|---------------|--------------|----------|-------------|
| 1 | 0.475800 | 0.507166 | employee_benefits_chunk_001 | Moved from #1 |
| 2 | 0.467200 | 0.257980 | employee_benefits_chunk_002 | Moved from #2 |
| 3 | 0.467200 | 0.158830 | remote_work_policy_chunk_006 | Moved from #3 |


## Detailed Scoring Breakdown

### Top Result #1: employee_benefits_chunk_001
- **Vector Similarity Score:** 0.507166
- **Re-rank Score:** 0.475800
- **Source Document:** employee_benefits.md
- **Section:** Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 1. Paid Time Off (PTO) Accrual
- **Token Count:** 79
- **Scoring Components:**
  - query_term_score: 0.252000
  - semantic_concept_score: 0.500000
  - info_density_score: 0.800000

**Text:**
```
Full-time regular employees accrue 18 days of Paid Time Off annually, calculated at a rate of 1.5 days per completed calendar month of active service. Employees may roll over a maximum of 5 unused PTO days into the following calendar year. Any unused balance exceeding 5 days on December 31 will expire without cash compensation, unless an exception is approved by HR due to operational necessity.
```

### Top Result #2: employee_benefits_chunk_002
- **Vector Similarity Score:** 0.257980
- **Re-rank Score:** 0.467200
- **Source Document:** employee_benefits.md
- **Section:** Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 2. Sick Leave & Medical Appointments
- **Token Count:** 67
- **Scoring Components:**
  - query_term_score: 0.168000
  - semantic_concept_score: 0.500000
  - info_density_score: 0.900000

**Text:**
```
Employees receive 10 dedicated sick days per calendar year. Sick leave is available from the first day of employment and does not require advance notice in emergency situations, though notification to the manager before 09:00 local time is expected. A medical certificate from a licensed healthcare practitioner is required for absences extending beyond 3 consecutive working days.
```

### Top Result #3: remote_work_policy_chunk_006
- **Vector Similarity Score:** 0.158830
- **Re-rank Score:** 0.467200
- **Source Document:** remote_work_policy.md
- **Section:** Section 4.2: Remote Work & Workplace Flexibility Policy > 5. Working Hours, Availability & Communication
- **Token Count:** 68
- **Scoring Components:**
  - query_term_score: 0.168000
  - semantic_concept_score: 0.500000
  - info_density_score: 0.900000

**Text:**
```
Remote employees are expected to maintain core operational hours from 9:00 AM to 5:00 PM local time. Employees must remain reachable via official communication channels (Slack, Microsoft Teams, corporate email) during working hours. Any scheduled absence or temporary unavailability must be logged in the shared department calendar at least 24 hours in advance.
```


## Key Insights
1. **Re-ranking Effectiveness:** Semantic re-ranking scores differ from vector similarity,
   indicating that additional relevance signals are being captured.

2. **Candidate Set Diversity:** The initial 10 candidates contain varied semantic content,
   allowing the re-ranker to select the most relevant subset.

3. **Scoring Transparency:** Each chunk is scored on multiple dimensions:
   - Query term overlap
   - Semantic concept alignment
   - Information density

