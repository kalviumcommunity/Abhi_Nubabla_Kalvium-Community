# LLM Parameter Experiments

This report documents experimental evaluations showing how generation parameters (Temperature, `max_tokens`, and `top_p`) affect LLM behavior when building a grounded RAG assistant.

## 1. Temperature Experiment

Using the same factual prompt across various temperatures. Note that temperature primarily regulates generation variation/randomness, and does not directly dictate correctness.

| Temperature | Token Usage | Output | Observation |
|---|---|---|---|
| 0.0 | Total: 296 (P: 46, C: 250) | <think> Here's a thinking process:  1.  **Analyze User Input:**    - **Topic:** Retrieval-Augmented Generation (RAG)    - **Length:** Approximately 100 words    - **Focus:** Factual information    - **Key Requirement:** Explain how retrieval provides context to the language model  2.  **Deconstruct RAG (Key Concepts):**    - What is it? A framework/architecture combining retrieval systems with generative AI (LLMs).    - How does it work?       - User query comes in      - System searches an external knowledge base/database      - Retrieves relevant documents/chunks      - Feeds these retrieved pieces as context to the LLM      - LLM generates a response grounded in that context    - Why? Reduces hallucinations, keeps knowledge up-to-date, improves accuracy/factual grounding.  3.  **Draft - Mental Refinement (aiming for ~100 words):**    Retrieval-Augmented Generation (RAG) is an AI architecture that enhances large language models by integrating external knowledge retrieval. When a user submits a query, the system first searches a designated database or document repository to locate relevant | Outputs at temperature 0.0 are highly deterministic, logical, and structured. Wording is predictable and concise. |
| 0.5 | Total: 296 (P: 46, C: 250) | <think> Here's a thinking process:  1.  **Analyze User Input:**    - **Topic:** Retrieval-Augmented Generation (RAG)    - **Length:** Approximately 100 words    - **Focus:** Factual information    - **Key Requirement:** Explain how retrieval provides context to the language model  2.  **Deconstruct RAG:**    - What is it? A technique/framework combining retrieval-based and generative AI methods.    - How does it work? It retrieves relevant external information/documents and feeds them to a language model (LLM) to generate responses.    - Why use it? Reduces hallucinations, keeps knowledge up-to-date, grounds responses in factual data.    - Key mechanism: Retrieval provides context by fetching relevant passages/documents from a knowledge base, which are then appended to the prompt, giving the LLM specific, verified information to base its generation on.  3.  **Draft - Mental Refinement (aiming for ~100 words):**    Retrieval-Augmented Generation (RAG) is an AI architecture that enhances large language models by integrating external knowledge retrieval with text generation. Instead of relying solely on pre-trained parameters, | Outputs show slight syntactic variance but retain standard definitions. Wording varies slightly compared to 0.0. |
| 1.0 | Total: 296 (P: 46, C: 250) | <think> Thinking Process:  1.  **Deconstruct the user's request:**     *   Topic: Retrieval-Augmented Generation (RAG).     *   Length: Approximately 100 words.     *   Focus: Factual information.     *   Key mechanism: Explain how retrieval provides context to the language model.  2.  **Drafting - Attempt 1 (Mental or rough text):**     Retrieval-Augmented Generation (RAG) is an AI architecture that enhances Large Language Models (LLMs) by connecting them to external knowledge sources. When a user asks a question, the system first retrieves relevant information from a database or documents using a search algorithm. This retrieved data is then combined with the user's query to form an enriched prompt, which is fed into the LLM. By providing this specific, up-to-date context, RAG prevents hallucinations, grounds responses in factual data, and allows the model to generate accurate answers based on information beyond its static training set.  3.  **Review and Refine (Word Count and Content Check):**     *   *Text:* Retrieval-Augmented Generation (RAG) is an AI architecture that enhances Large Language Models (LL | Outputs show high lexical creativity, varied sentence structures, and alternative synonym choices. |

## 2. max_tokens Experiment

Controlling completion length using a fixed temperature of `0.2`.

| max_tokens | Token Usage | Cut Short? | Output | Observation |
|---|---|---|---|---|
| 50 | Total: 96 (P: 46, C: 50) | YES (Finish Reason: length) | <think> Here's a thinking process:  1.  **Analyze User Input:**    - **Topic:** Retrieval-Augmented Generation (RAG)    - **Length:** Approximately 100 words    - **Focus:** F | The response is strictly capped and cut short mid-sentence because it exceeded the maximum token allotment. |
| 200 | Total: 246 (P: 46, C: 200) | YES (Finish Reason: length) | <think> Here's a thinking process:  1.  **Analyze User Input:**    - **Topic:** Retrieval-Augmented Generation (RAG)    - **Length:** Approximately 100 words    - **Focus:** Factual information    - **Key Requirement:** Explain how retrieval provides context to the language model  2.  **Deconstruct RAG (Core Concepts):**    - What is it? A technique/framework combining retrieval systems with generative AI (LLMs).    - How does it work?       - User query comes in.      - System searches an external knowledge base/database for relevant information.      - Retrieved documents/chunks are combined with the query.      - This combined input is fed to the LLM.      - LLM generates a response grounded in the retrieved context.    - Why? Reduces hallucinations, provides up-to-date/accurate information, leverages external knowledge without retraining. | The response completed naturally as the 200 tokens budget offered sufficient space for a ~100 words explanation. |

## 3. top_p Experiment

Evaluating cumulative probability sampling (`top_p`) with temperature fixed at `0.2`.

| top_p | Token Usage | Output | Observation |
|---|---|---|---|
| 0.2 | Total: 296 (P: 46, C: 250) | <think> Here's a thinking process:  1.  **Analyze User Input:**    - **Topic:** Retrieval-Augmented Generation (RAG)    - **Length:** Approximately 100 words    - **Focus:** Factual information    - **Key Requirement:** Explain how retrieval provides context to the language model  2.  **Deconstruct RAG (Key Concepts):**    - What is it? A framework/architecture combining retrieval systems with generative AI (LLMs).    - How does it work?       - User query comes in      - System searches an external knowledge base/database      - Retrieves relevant documents/chunks      - Feeds these retrieved pieces as context to the LLM      - LLM generates a response grounded in that context    - Why? Reduces hallucinations, keeps knowledge up-to-date, improves accuracy/factual grounding.  3.  **Draft - Mental Refinement (aiming for ~100 words):**    Retrieval-Augmented Generation (RAG) is an AI architecture that enhances large language models by integrating external knowledge retrieval. When a user submits a query, the system first searches a designated database or document repository to locate relevant | Limits generation to highly probable tokens, leading to factual, standard, and highly aligned vocabulary choices. |
| 1.0 | Total: 296 (P: 46, C: 250) | <think> Here's a thinking process:  1.  **Analyze User Input:**    - **Topic:** Retrieval-Augmented Generation (RAG)    - **Length:** Approximately 100 words    - **Focus:** Factual information    - **Key Requirement:** Explain how retrieval provides context to the language model  2.  **Deconstruct RAG (Key Concepts):**    - What is it? A framework/architecture combining retrieval and generation.    - How does it work? Retrieves relevant external information/documents, then feeds that to an LLM to generate a response.    - Why? Reduces hallucinations, grounds responses in factual/up-to-date data, leverages external knowledge bases.    - How does retrieval provide context? The retrieved documents/chunks are appended to the prompt, giving the LLM specific, relevant facts to reference during generation.  3.  **Draft - Mental Refinement (aiming for ~100 words):**    Retrieval-Augmented Generation (RAG) is an AI architecture that enhances large language models by integrating external knowledge retrieval with text generation. When a user submits a query, RAG first searches a designated database or document corpus to locate relevant | Considers the full range of candidate words, introducing broader terminology and dynamic word choices. |

## 4. Recommended Settings for a Grounded RAG Assistant

For a grounded, factual, and budget-friendly RAG assistant, the following settings are recommended:

- **`temperature = 0.2`**: Low temperature ensures consistency and limits creative hallucinations, keeping the response predictable and factual.
- **`max_tokens = 200`**: Restricting response tokens ensures concise answers, fits easily in conversational memory, and controls operational API cost.
- **`top_p = 0.9`**: A moderately conservative threshold allows some syntactic naturalness while discarding highly improbable, off-topic candidate words.

### Important Grounding Considerations

> [!IMPORTANT]
> While generation parameters significantly control randomness and token lengths, **they do not guarantee factual correctness or prevent hallucinations** on their own.
> Grounding primarily depends on:
> 1. **Retrieval Quality**: Injecting precise, high-relevance context chunks into the prompt.
> 2. **Prompt Engineering**: Framing strict instructions forcing the assistant to answer only using the provided facts.
> 3. **Model Selection**: Deploying models possessing strong instruction-following capabilities.

## Final Recommendation

For this grounded RAG assistant, use approximately:

```yaml
temperature: 0.2
max_tokens: 200
top_p: 0.9
```

These settings establish deterministic boundaries and cost control without artificially truncating responses. Factual grounding is driven by context retrieval and system prompting constraints, while generation parameters keep the model's outputs steady and aligned with the provided content.
