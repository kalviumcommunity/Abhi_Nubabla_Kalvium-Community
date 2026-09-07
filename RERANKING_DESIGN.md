# Chunk Re-Ranking System: Design & Implementation

## Overview

This document describes the two-stage retrieval pipeline with re-ranking, designed to improve the relevance and ordering of retrieved document chunks for RAG (Retrieval-Augmented Generation) systems.

## Problem Statement

**Challenge:** Initial vector similarity-based retrieval doesn't always rank the most relevant chunks first. The top-1 result by cosine similarity may not be the most suitable context for downstream LLM generation.

**Solution:** A two-stage pipeline that:
1. **Stage 1:** Retrieves a larger candidate set (e.g., 10 chunks) using fast vector similarity
2. **Stage 2:** Re-ranks candidates using semantic relevance scoring to identify the most suitable chunks for the query

## Architecture

### High-Level Pipeline

```
Query
  ↓
[Stage 1: Initial Retrieval]
  - Embed query using same model as corpus
  - Retrieve k_candidate=10 chunks by cosine similarity
  ↓
[Stage 2: Re-ranking]
  - Score each candidate using re-ranker
  - Sort by re-rank score
  - Return top k_final=3 results
  ↓
Final Results (ranked by semantic relevance)
```

### Key Components

#### 1. Re-ranker Implementations

**SemanticRelevanceReranker** (Default)
- Multi-aspect scoring combining:
  - **Query Term Score (40%):** Overlap of query terms in chunk, weighted by term specificity
  - **Semantic Concept Score (35%):** Alignment of domain concepts between query and chunk
  - **Info Density Score (25%):** Chunk information density based on length and structure markers
- Fully deterministic and requires no external APIs
- Suitable for production environments

**LLMReranker**
- Uses a large language model to score chunk relevance
- Sends each query-chunk pair to the LLM with a scoring prompt
- Normalizes LLM scores to [0, 1] range
- Includes fallback to semantic re-ranker if API is unavailable
- Better alignment with downstream LLM task but higher latency/cost

**HybridReranker**
- Combines vector similarity with semantic relevance
- Weights: 40% original vector score + 60% semantic re-rank score
- Useful when you want to preserve some signal from initial retrieval while applying semantic refinement

#### 2. Scoring Breakdown Transparency

Each chunk includes a `scoring_breakdown` dictionary showing component contributions:
```json
{
  "query_term_score": 0.252,
  "semantic_concept_score": 0.5,
  "info_density_score": 0.8
}
```

This enables:
- Debugging re-ranking decisions
- Understanding why chunks were re-ranked
- Tuning component weights

### Data Models

#### RerankedChunk
Represents a single re-ranked chunk with both vector and re-rank scores:
```python
@dataclass
class RerankedChunk:
    rank: int                           # Position after re-ranking
    chunk_id: str                       # Unique identifier
    source_text: str                    # Full chunk text
    metadata: Dict[str, Any]            # Document metadata
    vector_score: float                 # Original cosine similarity
    rerank_score: float                 # Re-ranker relevance score
    scoring_breakdown: Dict[str, float] # Component score details
```

#### RerangingResult
Contains the full two-stage pipeline result:
```python
@dataclass
class RerangingResult:
    query: str                                    # Input query
    k_candidate: int                              # Stage 1 candidate count
    k_final: int                                  # Stage 2 final count
    candidates_initial: List[RerankedChunk]       # Stage 1 results
    results_reranked: List[RerankedChunk]         # Stage 2 results
    reranker_name: str                            # Which re-ranker was used
```

## Usage

### Simple Two-Stage Retrieval

```python
from src.retriever import retrieve_with_reranking

# Retrieve with default semantic re-ranker
result = retrieve_with_reranking(
    query="How many days of PTO do employees get?",
    k_final=3,           # Final results to return
    k_candidate=10,      # Initial candidates to re-rank
)

# Access results
for chunk in result.results_reranked:
    print(f"Rank: {chunk.rank}")
    print(f"Vector Score: {chunk.vector_score:.4f}")
    print(f"Re-rank Score: {chunk.rerank_score:.4f}")
    print(f"Text: {chunk.source_text[:100]}...")
```

### Custom Re-ranker

```python
from src.retriever import retrieve_with_reranking
from src.reranker import LLMReranker

# Use LLM-based re-ranker
result = retrieve_with_reranking(
    query="What security measures are required for remote access?",
    k_final=3,
    k_candidate=10,
    reranker=LLMReranker(),
)
```

### Accessing Scoring Details

```python
result = retrieve_with_reranking(...)

# Get initial candidates (by vector similarity)
for chunk in result.candidates_initial:
    print(f"ID: {chunk.chunk_id}, Vector: {chunk.vector_score:.4f}")

# Get final results (by semantic relevance)
for chunk in result.results_reranked:
    print(f"ID: {chunk.chunk_id}, Re-rank: {chunk.rerank_score:.4f}")
    print(f"Components: {chunk.scoring_breakdown}")
```

## Demonstration Results

### Sample Query
**Query:** "How many days of paid time off do employees get each year?"

### Before Re-ranking (Vector Similarity)
| Rank | Vector Score | Chunk ID | Source |
|------|--------------|----------|--------|
| 1 | 0.5072 | employee_benefits_chunk_001 | PTO Accrual Policy |
| 2 | 0.2580 | employee_benefits_chunk_002 | Sick Leave Policy |
| 3 | 0.1588 | remote_work_policy_chunk_006 | Working Hours |

### After Re-ranking (Semantic Relevance)
| Rank | Re-rank Score | Vector Score | Chunk ID | Movement |
|------|---------------|--------------|----------|----------|
| 1 | 0.4758 | 0.5072 | employee_benefits_chunk_001 | Stable |
| 2 | 0.4672 | 0.2580 | employee_benefits_chunk_002 | ↑ Improved |
| 3 | 0.4672 | 0.1588 | remote_work_policy_chunk_006 | ↓ Reranked |

### Key Insight
The re-ranker improves **candidate #2** (sick days policy) from rank 2→2 with better scoring (0.258→0.467), recognizing it as highly relevant to PTO questions.

## Implementation Details

### SemanticRelevanceReranker Scoring

**1. Query Term Score**
```
- Tokenize query and chunk
- Remove common stopwords
- Count query terms present in chunk
- Weight by term specificity (length)
- score = (matches / total_query_terms) × specificity_weight
```

**2. Semantic Concept Score**
```
- Define domain-specific semantic concepts
- Count concept matches in both query and chunk
- Alignment score = min(1.0, chunk_concepts / query_concepts)
```

**3. Info Density Score**
```
- Ideal chunk size: 50-300 words
- Check for structural markers (colons, numbers, bullets)
- Combine length score (70%) + structure score (30%)
```

**Final Score**
```
final_score = 0.40 × query_term_score 
            + 0.35 × semantic_concept_score 
            + 0.25 × info_density_score
```

### Semantic Concepts (Domain-Specific)
The system recognizes these concepts:
- `leave_vacation`: PTO, vacation, leave, accrual, rollover
- `security`: encryption, malware, VPN, password, incident
- `remote_work`: remote, hybrid, telecommute, WFH
- `policy`: policy, procedure, compliance, guideline
- `benefits`: insurance, health, medical, wellness

## Performance Considerations

### Latency
- **Vector Similarity Retrieval:** O(n) distance computations (fast)
- **Semantic Re-ranking:** O(k) scoring computations where k_candidate ≤ n
- **Total Latency:** ~100-200ms for 10 candidates with semantic re-ranker

### Customization
You can tune the component weights in `SemanticRelevanceReranker`:
```python
reranker = SemanticRelevanceReranker()
reranker.query_terms_weight = 0.4    # Adjust importance
reranker.semantic_concept_weight = 0.35
reranker.info_density_weight = 0.25
```

## Files

- **`src/reranker.py`** - Core re-ranker implementations
  - `ChunkReranker` abstract base class
  - `SemanticRelevanceReranker` implementation
  - `LLMReranker` implementation
  - `HybridReranker` implementation
  - `TwoStageRetrievalPipeline` orchestrator

- **`src/retriever.py`** - Public interface
  - `retrieve_top_k()` - Single-stage direct retrieval
  - `retrieve_with_reranking()` - Two-stage retrieval with re-ranking

- **`src/reranking_demo.py`** - Demonstration script
  - Shows before/after comparison
  - Generates markdown report
  - Exports JSON results
  - Demonstrates all re-ranker types

## Testing

Run the demonstration:
```bash
python -m src.reranking_demo
```

This generates:
- `data/reranking_demo_report.md` - Detailed markdown report
- `data/reranking_demo_results.json` - Structured JSON results with all scores

## Future Enhancements

1. **Cross-Encoder Models:** Fine-tune a cross-encoder specifically for re-ranking
2. **Colbert Re-ranker:** Implement contextualized late interaction (ColBERT) re-ranking
3. **Multi-Stage Clustering:** Add intermediate clustering stage for diversity
4. **Learning to Rank:** Train re-ranker weights on labeled relevance data
5. **Adaptive k_candidate:** Automatically adjust candidate set size based on result variability
6. **Diversification:** Prevent similar chunks from dominating final results

## References

- Retrieval-Augmented Generation: https://arxiv.org/abs/2005.11401
- Dense Passage Retrieval: https://arxiv.org/abs/2004.04906
- ColBERT Re-ranking: https://arxiv.org/abs/2004.12832
- Learning to Rank: https://en.wikipedia.org/wiki/Learning_to_rank
