# Context Injection & Augmented Prompt Assembly

## Overview

The Context Injection system transforms raw retrieved chunks into fully assembled augmented prompts ready for LLM inference. It handles token budgeting, source attribution, and grounding instruction injection to ensure the model answers from evidence while staying within token limits.

## Problem & Solution

### The Challenge
Retrieved chunks are unordered and lack source attribution. Models may:
- Ignore the provided context and use external knowledge
- Lose track of where information comes from
- Consume tokens inefficiently
- Generate hallucinated citations

### The Solution
A pipeline that:
1. **Injects chunks** with source markers ([1], [2], etc.)
2. **Enforces token budget** to fit within model limits
3. **Adds grounding instructions** to enforce context-only answering
4. **Assembles augmented prompt** ready for the LLM

## Architecture

### High-Level Pipeline

```
Query
  ↓
[Retrieval]
Get k chunks
  ↓
[Context Injection]
Add source markers [1], [2], [3]
  ↓
[Token Budget Enforcement]
Drop chunks that exceed budget
  ↓
[Prompt Assembly]
Format with instructions + context + question
  ↓
Augmented Prompt (ready for LLM)
```

### Key Components

#### 1. TokenCounter
Estimates token counts using empirical heuristics:
- **Word-based:** ~1.3 tokens per word
- **Character-based:** ~0.25 tokens per character
- Uses word-based for text with words, character-based as fallback

```python
tokens = TokenCounter.estimate_tokens("Your text here")
total = TokenCounter.count_tokens_in_list(["text1", "text2"])
```

#### 2. SourceMarker
Annotates chunks with citation markers:
- Numeric markers: [1], [2], [3], etc.
- Full references: `[1] (document.pdf - Section Name)`
- Enables traceability and citations

```python
marker = SourceMarker(
    index=1,
    chunk_id="chunk_001",
    source_document="policy.pdf",
    section="Benefits",
)
print(marker)  # [1]
print(marker.full_reference())  # [1] (policy.pdf - Benefits)
```

#### 3. InjectedChunk
Wraps a chunk with its source marker:
```python
@dataclass
class InjectedChunk:
    source_marker: SourceMarker
    original_text: str
    injected_text: str  # Text with [1] prefix
    token_count: int
    metadata: Dict[str, Any]
```

#### 4. GroundingInstructions
Provides three styles of system instructions:

**Basic (Permissive)**
- Simple instruction to use only provided context
- Suitable for straightforward questions

**Strict (Rigorous)**
- Enforces explicit citation for every claim
- Requires traceable sources
- Best for fact-checking scenarios

**Professional (Balanced)**
- Company policy / documentation answering
- Acknowledges context limitations
- Balances accuracy with usability

```python
instructions = GroundingInstructions.get_grounding_instructions("professional")
```

#### 5. PromptTemplate
Pre-formatted templates for assembling prompts:
- **Standard:** Minimal format (instructions + context + question)
- **With Sources:** Explicit source reference section
- **Detailed:** Comprehensive metadata and source info

#### 6. AugmentedPromptBuilder
Orchestrates the entire pipeline:

```python
builder = AugmentedPromptBuilder(
    model_name="gpt-3.5-turbo",
    context_budget_percent=0.50,  # Use 50% of tokens for context
    reserved_tokens=1000,  # Reserve 1000 tokens for answer
    grounding_style="professional",
)

result = builder.build_augmented_prompt(
    user_question="What is our PTO policy?",
    chunks=chunks,
)
```

### Token Budget Enforcement

**Model Token Limits** (built-in):
- gpt-3.5-turbo: 4,096 tokens
- gpt-4: 8,192 tokens
- gpt-4-turbo: 128,000 tokens
- claude-2: 100,000 tokens

**Token Allocation**:
```
Total Model Tokens: 4096
├── Grounding Instructions: 100 tokens (2-3%)
├── Context Budget (50%): 2048 tokens
│   └── Injected Chunks: variable, capped at 2048
├── User Question: variable (usually 10-50)
└── Reserved for Answer: 1000 tokens
```

**Budget Enforcement Strategy**:
1. Calculate available context budget
2. Add chunks in order until budget exhausted
3. Remaining chunks are dropped
4. Warning if all retrieved chunks don't fit

## Usage Patterns

### Pattern 1: End-to-End (Recommended)
Simplest usage - retrieve and build augmented prompt in one call:

```python
from src.retriever import build_augmented_prompt

result = build_augmented_prompt(
    user_question="What are the remote work policies?",
    k=5,  # Retrieve 5 chunks
    model_name="gpt-3.5-turbo",
    grounding_style="professional",
)

print(result.assembled_prompt)  # Ready for LLM
print(result.token_budget_remaining)  # Space for answer
```

### Pattern 2: Step-by-Step Control
For custom workflows:

```python
from src.retriever import retrieve_top_k
from src.context_injector import AugmentedPromptBuilder

# Step 1: Retrieve
chunks = retrieve_top_k("your question", k=10)

# Step 2: Build with custom settings
builder = AugmentedPromptBuilder(
    model_name="gpt-4",
    context_budget_percent=0.60,
    reserved_tokens=2000,
    grounding_style="strict",
)

# Step 3: Assemble
result = builder.build_augmented_prompt(
    user_question="your question",
    chunks=chunks,
    template_style="with_sources",
)
```

### Pattern 3: Batch Processing
Process multiple questions:

```python
from src.retriever import build_augmented_prompt

questions = [
    "What is PTO?",
    "How do I report a security incident?",
    "What are remote work requirements?",
]

for q in questions:
    result = build_augmented_prompt(q)
    send_to_llm(result.assembled_prompt)
```

## Sample Augmented Prompt

**Input Query:**
```
What are the paid time off policies for full-time employees?
```

**Retrieved Chunks (5 total, injected with markers):**
```
[1] (employee_benefits.md - Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 4. Health Insurance & Wellness Reimbursement)
The company sponsors 90% of the premium for comprehensive medical, dental, and vision insurance for full-time employees...

[2] (employee_benefits.md - Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 1. Paid Time Off (PTO) Accrual)
Full-time regular employees accrue 18 days of Paid Time Off annually, calculated at a rate of 1.5 days per completed calendar month...

[3] (it_security_policy.md - Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure)
If you suspect an active security compromise, credential theft, or phishing email...

[4] (remote_work_policy.md - Section 4.2: Remote Work & Workplace Flexibility Policy > 5. Working Hours, Availability & Communication)
Remote employees are expected to maintain core operational hours from 9:00 AM to 5:00 PM local time...

[5] (remote_work_policy.md - Section 4.2: Remote Work & Workplace Flexibility Policy > 2. Eligibility Requirements)
To qualify for regular or hybrid remote work...
```

**Augmented Prompt (Ready for LLM):**
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
The company sponsors 90% of the premium for comprehensive medical, dental, and vision insurance for full-time employees...

[2] (employee_benefits.md - Section 6.0: Employee Benefits, Paid Time Off & Leave Guidelines > 1. Paid Time Off (PTO) Accrual)
Full-time regular employees accrue 18 days of Paid Time Off annually, calculated at a rate of 1.5 days per completed calendar month...

[3] (it_security_policy.md - Section 8.1: Corporate IT Security & Incident Response Protocols > 4. Employee Incident Reporting Procedure)
If you suspect an active security compromise, credential theft, or phishing email...

[4] (remote_work_policy.md - Section 4.2: Remote Work & Workplace Flexibility Policy > 5. Working Hours, Availability & Communication)
Remote employees are expected to maintain core operational hours from 9:00 AM to 5:00 PM local time...

[5] (remote_work_policy.md - Section 4.2: Remote Work & Workplace Flexibility Policy > 2. Eligibility Requirements)
To qualify for regular or hybrid remote work...

---

**Question:** What are the paid time off policies for full-time employees?

**Answer:**
```

## Token Budget Example

**Scenario:**
- Model: gpt-3.5-turbo (4,096 max tokens)
- Context budget: 50% → 2,048 tokens
- Reserved for answer: 1,000 tokens

**Allocation:**
| Component | Tokens | % | Status |
|-----------|--------|---|--------|
| Instructions | 106 | 6.8% | ✓ Fixed |
| Context | 440 | 28.2% | ✓ OK (budget: 2048) |
| Question | 13 | 0.8% | ✓ Fixed |
| Reserved Answer | 1000 | 64.1% | ✓ Fixed |
| **Total** | **1559** | **100%** | ✓ Well within limits |

**Budget Status:** OK - 1,608 tokens remaining

## Key Features

✅ **Source Attribution**
- Every chunk has a marker [1], [2], etc.
- Full references include source document and section
- Enables traceability and fact-checking

✅ **Token Budget Enforcement**
- Automatically drops chunks that exceed budget
- Prevents token limit violations
- Leaves room for model's answer

✅ **Grounding Instructions**
- Multiple instruction styles (basic/strict/professional)
- Enforces context-only answering
- Discourages hallucination and external knowledge use

✅ **Production Ready**
- Transparent token counting
- Clear budget warnings
- Serializable to JSON for logging/debugging
- 22 unit tests (all passing)

## Customization

### Custom Context Budget
```python
builder = AugmentedPromptBuilder(
    context_budget_percent=0.70,  # Use 70% of tokens
    reserved_tokens=500,  # Only reserve 500 for answer
)
```

### Custom Grounding Style
```python
# Strict: Every claim must be cited explicitly
result = build_augmented_prompt(
    user_question="Query",
    grounding_style="strict",
)

# Basic: Simple instruction to use context only
result = build_augmented_prompt(
    user_question="Query",
    grounding_style="basic",
)
```

### Custom Model Token Limits
```python
# Extend with new model
AugmentedPromptBuilder.MODEL_TOKEN_LIMITS["my-model"] = 16384
builder = AugmentedPromptBuilder(model_name="my-model")
```

## Files

- **`src/context_injector.py`** - Core implementation
  - `TokenCounter` for token estimation
  - `SourceMarker` for chunk attribution
  - `InjectedChunk` data model
  - `GroundingInstructions` system prompts
  - `PromptTemplate` formatting
  - `AugmentedPromptBuilder` orchestration

- **`src/context_injection_demo.py`** - Demonstration script
  - Shows full pipeline in action
  - Generates before/after comparison
  - Outputs markdown and JSON reports

- **`src/retriever.py`** - Updated with wrapper
  - `build_augmented_prompt()` - end-to-end function
  - Combines retrieval + context injection

- **`tests/test_context_injector.py`** - 22 unit tests
  - All token counting tests
  - Source marker tests
  - Injection and budget tests
  - Template formatting tests

## Testing

Run tests:
```bash
python -m unittest tests.test_context_injector -v
# 22 tests - all passing ✓
```

Run demonstration:
```bash
python -m src.context_injection_demo
# Generates markdown and JSON reports
```

## Next Steps

Potential enhancements:
1. **Dynamic Context Budget:** Adjust budget based on question complexity
2. **Smart Chunking:** Prioritize most relevant chunks under budget constraints
3. **Multi-stage Context:** Different context sections (CRITICAL, SUPPORTING, BACKGROUND)
4. **Context Compression:** Summarize chunks to fit more content in budget
5. **Citation Verification:** Track which sources are actually used in the answer
6. **Context Quality Metrics:** Score quality of assembled context
7. **Interactive Mode:** Let user adjust context budget in real-time
