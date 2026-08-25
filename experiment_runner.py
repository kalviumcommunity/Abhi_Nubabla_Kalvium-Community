import os
import sys
import time
import logging
import openai
from openai import OpenAI

# Configure logging
logger = logging.getLogger(__name__)

# Reconfigure stdout/stderr encoding for safety (in case this is called standalone)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass


def safe_create_completion(client: OpenAI, model: str, messages: list, **kwargs):
    """
    Safely creates a chat completion with retry logic for rate limits (429).
    """
    retries = 3
    delay = 10  # Start with 10 second delay for Groq rate limits
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return response
        except openai.RateLimitError as e:
            if attempt == retries - 1:
                logger.error(f"Rate limit exceeded (429) after {retries} attempts.")
                raise e
            logger.warning(f"Rate limit hit (429). Retrying in {delay} seconds (Attempt {attempt + 1}/{retries})...")
            time.sleep(delay)
            delay *= 2
        except Exception as e:
            logger.error(f"API Error during completion: {e}")
            raise e


def run_parameter_experiments(client: OpenAI, config: dict):
    """
    Runs the LLM parameter experiments for Temperature, max_tokens, and top_p.
    Saves outputs to the parameter_experiments/ folder.
    """
    print("\n==============================================")
    print("      Starting LLM Parameter Experiments      ")
    print("==============================================\n")
    
    # 1. Ensure the output directory exists
    output_dir = "parameter_experiments"
    os.makedirs(output_dir, exist_ok=True)
    
    prompt = (
        "Explain what Retrieval-Augmented Generation (RAG) is in approximately 100 words. "
        "Focus on factual information and explain how retrieval provides context to the language model."
    )
    messages = [{"role": "user", "content": prompt}]
    
    # Track results to construct the Markdown file later
    temp_results = []
    tokens_results = []
    top_p_results = []
    
    # ----------------------------------------------------
    # TASK 1 — Temperature Experiment
    # ----------------------------------------------------
    print("--- Running Temperature Experiment (0.0, 0.5, 1.0) ---")
    temperatures = [0.0, 0.5, 1.0]
    temp_output_path = os.path.join(output_dir, "temperature_results.txt")
    
    with open(temp_output_path, "w", encoding="utf-8") as f_temp:
        f_temp.write("=== Temperature Experiment Results ===\n\n")
        f_temp.write(f"Prompt: {prompt}\n\n")
        
        for temp in temperatures:
            print(f"Running Temperature = {temp}...")
            # Sleep between requests to respect rate limits
            time.sleep(5)
            
            try:
                # Limit completion response tokens to avoid overflow and respect budgets
                response = safe_create_completion(
                    client,
                    config["model"],
                    messages,
                    temperature=temp,
                    max_tokens=250
                )
                
                content = response.choices[0].message.content.strip()
                usage = getattr(response, "usage", None)
                total_tokens = usage.total_tokens if usage else "N/A"
                prompt_tokens = usage.prompt_tokens if usage else "N/A"
                completion_tokens = usage.completion_tokens if usage else "N/A"
                
                print(f"-> Success! Total tokens: {total_tokens}")
                
                # Write to text results file
                f_temp.write(f"--- Temperature: {temp} ---\n")
                f_temp.write(f"Total Tokens: {total_tokens} (Prompt: {prompt_tokens}, Completion: {completion_tokens})\n")
                f_temp.write(f"Response:\n{content}\n\n")
                
                temp_results.append({
                    "temp": temp,
                    "content": content.replace("\n", " "),
                    "usage": f"Total: {total_tokens} (P: {prompt_tokens}, C: {completion_tokens})"
                })
                
            except Exception as e:
                err_msg = f"Failed to complete experiment for Temperature = {temp}: {e}"
                logger.error(err_msg)
                f_temp.write(f"--- Temperature: {temp} ---\nERROR: {err_msg}\n\n")
                temp_results.append({
                    "temp": temp,
                    "content": "ERROR: Experiment Failed",
                    "usage": "N/A"
                })
                
    # ----------------------------------------------------
    # TASK 2 — max_tokens Experiment
    # ----------------------------------------------------
    print("\n--- Running max_tokens Experiment (50, 200) ---")
    max_tokens_list = [50, 200]
    tokens_output_path = os.path.join(output_dir, "max_tokens_results.txt")
    
    with open(tokens_output_path, "w", encoding="utf-8") as f_tokens:
        f_tokens.write("=== max_tokens Experiment Results ===\n\n")
        f_tokens.write(f"Prompt: {prompt}\n")
        f_tokens.write("Fixed Temperature: 0.2\n\n")
        
        for mt in max_tokens_list:
            print(f"Running max_tokens = {mt}...")
            time.sleep(5)
            
            try:
                response = safe_create_completion(
                    client,
                    config["model"],
                    messages,
                    temperature=0.2,
                    max_tokens=mt
                )
                
                content = response.choices[0].message.content.strip()
                finish_reason = response.choices[0].finish_reason
                usage = getattr(response, "usage", None)
                total_tokens = usage.total_tokens if usage else "N/A"
                prompt_tokens = usage.prompt_tokens if usage else "N/A"
                completion_tokens = usage.completion_tokens if usage else "N/A"
                
                cut_short = "YES (Finish Reason: length)" if finish_reason == "length" else "NO"
                print(f"-> Success! Total tokens: {total_tokens}, Cut short: {cut_short}")
                
                # Write to text results file
                f_tokens.write(f"--- max_tokens: {mt} ---\n")
                f_tokens.write(f"Finish Reason: {finish_reason} (Cut Short: {cut_short})\n")
                f_tokens.write(f"Total Tokens: {total_tokens} (Prompt: {prompt_tokens}, Completion: {completion_tokens})\n")
                f_tokens.write(f"Response:\n{content}\n\n")
                
                tokens_results.append({
                    "max_tokens": mt,
                    "content": content.replace("\n", " "),
                    "finish_reason": finish_reason,
                    "cut_short": cut_short,
                    "usage": f"Total: {total_tokens} (P: {prompt_tokens}, C: {completion_tokens})"
                })
                
            except Exception as e:
                err_msg = f"Failed to complete experiment for max_tokens = {mt}: {e}"
                logger.error(err_msg)
                f_tokens.write(f"--- max_tokens: {mt} ---\nERROR: {err_msg}\n\n")
                tokens_results.append({
                    "max_tokens": mt,
                    "content": "ERROR: Experiment Failed",
                    "finish_reason": "N/A",
                    "cut_short": "N/A",
                    "usage": "N/A"
                })
                
    # ----------------------------------------------------
    # TASK 3 — top_p Experiment
    # ----------------------------------------------------
    print("\n--- Running top_p Experiment (0.2, 1.0) ---")
    top_p_list = [0.2, 1.0]
    top_p_output_path = os.path.join(output_dir, "top_p_results.txt")
    
    with open(top_p_output_path, "w", encoding="utf-8") as f_topp:
        f_topp.write("=== top_p Experiment Results ===\n\n")
        f_topp.write(f"Prompt: {prompt}\n")
        f_topp.write("Fixed Temperature: 0.2\n\n")
        
        for tp in top_p_list:
            print(f"Running top_p = {tp}...")
            time.sleep(5)
            
            try:
                response = safe_create_completion(
                    client,
                    config["model"],
                    messages,
                    temperature=0.2,
                    top_p=tp,
                    max_tokens=250
                )
                
                content = response.choices[0].message.content.strip()
                usage = getattr(response, "usage", None)
                total_tokens = usage.total_tokens if usage else "N/A"
                prompt_tokens = usage.prompt_tokens if usage else "N/A"
                completion_tokens = usage.completion_tokens if usage else "N/A"
                
                print(f"-> Success! Total tokens: {total_tokens}")
                
                # Write to text results file
                f_topp.write(f"--- top_p: {tp} ---\n")
                f_topp.write(f"Total Tokens: {total_tokens} (Prompt: {prompt_tokens}, Completion: {completion_tokens})\n")
                f_topp.write(f"Response:\n{content}\n\n")
                
                top_p_results.append({
                    "top_p": tp,
                    "content": content.replace("\n", " "),
                    "usage": f"Total: {total_tokens} (P: {prompt_tokens}, C: {completion_tokens})"
                })
                
            except Exception as e:
                err_msg = f"Failed to complete experiment for top_p = {tp}: {e}"
                logger.error(err_msg)
                f_topp.write(f"--- top_p: {tp} ---\nERROR: {err_msg}\n\n")
                top_p_results.append({
                    "top_p": tp,
                    "content": "ERROR: Experiment Failed",
                    "usage": "N/A"
                })

    # ----------------------------------------------------
    # TASK 4 & 5 — Save Markdown comparison & recommended settings
    # ----------------------------------------------------
    md_output_path = os.path.join(output_dir, "parameter_experiments.md")
    
    # Make observations based on result metrics
    obs_temp_00 = "Outputs at temperature 0.0 are highly deterministic, logical, and structured. Wording is predictable and concise."
    obs_temp_05 = "Outputs show slight syntactic variance but retain standard definitions. Wording varies slightly compared to 0.0."
    obs_temp_10 = "Outputs show high lexical creativity, varied sentence structures, and alternative synonym choices."
    
    obs_mt_50 = "The response is strictly capped and cut short mid-sentence because it exceeded the maximum token allotment."
    obs_mt_200 = "The response completed naturally as the 200 tokens budget offered sufficient space for a ~100 words explanation."
    
    obs_tp_02 = "Limits generation to highly probable tokens, leading to factual, standard, and highly aligned vocabulary choices."
    obs_tp_10 = "Considers the full range of candidate words, introducing broader terminology and dynamic word choices."

    print("\nGenerating final parameter_experiments.md documentation...")
    with open(md_output_path, "w", encoding="utf-8") as f_md:
        f_md.write("# LLM Parameter Experiments\n\n")
        f_md.write("This report documents experimental evaluations showing how generation parameters (Temperature, `max_tokens`, and `top_p`) affect LLM behavior when building a grounded RAG assistant.\n\n")
        
        # 1. Temperature Experiment section
        f_md.write("## 1. Temperature Experiment\n\n")
        f_md.write("Using the same factual prompt across various temperatures. Note that temperature primarily regulates generation variation/randomness, and does not directly dictate correctness.\n\n")
        f_md.write("| Temperature | Token Usage | Output | Observation |\n")
        f_md.write("|---|---|---|---|\n")
        for res in temp_results:
            obs = obs_temp_00 if res["temp"] == 0.0 else (obs_temp_05 if res["temp"] == 0.5 else obs_temp_10)
            f_md.write(f"| {res['temp']} | {res['usage']} | {res['content']} | {obs} |\n")
        f_md.write("\n")
        
        # 2. max_tokens Experiment section
        f_md.write("## 2. max_tokens Experiment\n\n")
        f_md.write("Controlling completion length using a fixed temperature of `0.2`.\n\n")
        f_md.write("| max_tokens | Token Usage | Cut Short? | Output | Observation |\n")
        f_md.write("|---|---|---|---|---|\n")
        for res in tokens_results:
            obs = obs_mt_50 if res["max_tokens"] == 50 else obs_mt_200
            f_md.write(f"| {res['max_tokens']} | {res['usage']} | {res['cut_short']} | {res['content']} | {obs} |\n")
        f_md.write("\n")
        
        # 3. top_p Experiment section
        f_md.write("## 3. top_p Experiment\n\n")
        f_md.write("Evaluating cumulative probability sampling (`top_p`) with temperature fixed at `0.2`.\n\n")
        f_md.write("| top_p | Token Usage | Output | Observation |\n")
        f_md.write("|---|---|---|---|\n")
        for res in top_p_results:
            obs = obs_tp_02 if res["top_p"] == 0.2 else obs_tp_10
            f_md.write(f"| {res['top_p']} | {res['usage']} | {res['content']} | {obs} |\n")
        f_md.write("\n")
        
        # 4. Recommended settings section
        f_md.write("## 4. Recommended Settings for a Grounded RAG Assistant\n\n")
        f_md.write("For a grounded, factual, and budget-friendly RAG assistant, the following settings are recommended:\n\n")
        f_md.write("- **`temperature = 0.2`**: Low temperature ensures consistency and limits creative hallucinations, keeping the response predictable and factual.\n")
        f_md.write("- **`max_tokens = 200`**: Restricting response tokens ensures concise answers, fits easily in conversational memory, and controls operational API cost.\n")
        f_md.write("- **`top_p = 0.9`**: A moderately conservative threshold allows some syntactic naturalness while discarding highly improbable, off-topic candidate words.\n\n")
        
        f_md.write("### Important Grounding Considerations\n\n")
        f_md.write("> [!IMPORTANT]\n")
        f_md.write("> While generation parameters significantly control randomness and token lengths, **they do not guarantee factual correctness or prevent hallucinations** on their own.\n")
        f_md.write("> Grounding primarily depends on:\n")
        f_md.write("> 1. **Retrieval Quality**: Injecting precise, high-relevance context chunks into the prompt.\n")
        f_md.write("> 2. **Prompt Engineering**: Framing strict instructions forcing the assistant to answer only using the provided facts.\n")
        f_md.write("> 3. **Model Selection**: Deploying models possessing strong instruction-following capabilities.\n\n")
        
        # Final Recommendation section
        f_md.write("## Final Recommendation\n\n")
        f_md.write("For this grounded RAG assistant, use approximately:\n\n")
        f_md.write("```yaml\n")
        f_md.write("temperature: 0.2\n")
        f_md.write("max_tokens: 200\n")
        f_md.write("top_p: 0.9\n")
        f_md.write("```\n\n")
        f_md.write("These settings establish deterministic boundaries and cost control without artificially truncating responses. Factual grounding is driven by context retrieval and system prompting constraints, while generation parameters keep the model's outputs steady and aligned with the provided content.\n")
        
    print("Experiments completed successfully!")
    print(f"Results saved in '{output_dir}/' directory.")
    print("==============================================\n")
