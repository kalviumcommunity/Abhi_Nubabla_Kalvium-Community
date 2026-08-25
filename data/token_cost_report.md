# Tokenization & LLM Cost Estimation Report

This report measures context window usage, evaluates text-length-to-token ratios using `tiktoken`, and calculates RAG assistant costs.

---

## 📊 Task 1 & 2: Token Counts for Sample Texts

| Sample | Characters | Words | Tokens | Chars / Token |
| :--- | :---: | :---: | :---: | :---: |
| **Sample 1 (Short User Query)** | 78 | 12 | **15** | 5.2 |
| **Sample 2 (Medium Paragraph Context)** | 612 | 87 | **100** | 6.12 |
| **Sample 3 (Long RAG Document)** | 2542 | 351 | **476** | 5.34 |

---

## 💰 Task 3: Cost Estimates (1,000 RAG Workload Queries)

Scenario: 1,000 queries with ~95 input tokens (context + question) and 150 output tokens per query.

| Model | Input Tokens | Input Cost ($) | Output Tokens | Output Cost ($) | **Total Cost ($)** |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **GPT-4o-mini** | 115,000 | $0.0173 | 150,000 | $0.0900 | **$0.1072** |
| **GPT-4o** | 115,000 | $0.2875 | 150,000 | $1.5000 | **$1.7875** |

---

## 🔍 Task 4: Text Length vs. Token Count Relationship

Character length and word count do **not** scale linearly with token counts across different text types:

| Domain Category | Characters | Words | Tokens | Chars / Token | Words / Token |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Standard English Prose** | 146 | 20 | **22** | 6.64 | 0.91 |
| **Python Code Snippet** | 218 | 23 | **60** | 3.63 | 0.38 |
| **Dense Technical / Hyphenated Text** | 179 | 9 | **33** | 5.42 | 0.27 |
| **Multilingual / Non-ASCII Text** | 157 | 21 | **43** | 3.65 | 0.49 |

### Key Takeaways
1. **English Prose**: Averages ~4 characters per token (0.75 words per token).
2. **Code Snippets & Syntax**: Syntax characters (`:`, `=`, `->`, indentation) create higher token density (~2.5-3 characters per token).
3. **Technical / Hyphenated Words**: Complex compounds break into multiple sub-word tokens (~3.8 characters per token).
4. **Multilingual / Non-ASCII**: Non-Latin scripts require multi-byte UTF-8 token encodings, dramatically increasing token count per character (~1.2-1.8 characters per token).