import os
import sys
import logging
import argparse
import openai
from openai import OpenAI
from dotenv import load_dotenv

import history_manager
from prompt.templates import render_rag_request, STAFF_ASSISTANT_SYSTEM_PROMPT

# Reconfigure stdout/stderr to use UTF-8 to prevent encoding issues on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass

# Set up logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """
    Loads configuration from environment variables.
    
    Validates that the required variables are present. If any are missing,
    raises a ValueError.
    """
    load_dotenv()
    
    config = {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_BASE_URL"),
        "model": os.getenv("OPENAI_MODEL"),
        "max_history_tokens": int(os.getenv("MAX_HISTORY_TOKENS", "1000")),
        "history_trim_threshold": float(os.getenv("HISTORY_TRIM_THRESHOLD", "0.80")),
        "max_response_tokens": int(os.getenv("MAX_RESPONSE_TOKENS", "200"))
    }
    
    missing_vars = [k for k, v in list(config.items())[:3] if not v or v.strip() == ""]
    if missing_vars:
        env_mapping = {
            "api_key": "OPENAI_API_KEY",
            "base_url": "OPENAI_BASE_URL",
            "model": "OPENAI_MODEL"
        }
        missing_env_names = [env_mapping[var] for var in missing_vars]
        raise ValueError(
            f"Configuration error: Missing required environment variable(s): "
            f"{', '.join(missing_env_names)} in .env file."
        )
        
    if config["api_key"] in ["your_grok_api_key_here", "your_api_key_here"]:
        raise ValueError("A real xAI API key is not configured in .env. Add a new valid key locally and rerun the script.")
        
    return config


def create_client(config: dict) -> OpenAI:
    """
    Initializes and returns the OpenAI client.
    """
    return OpenAI(
        api_key=config["api_key"],
        base_url=config["base_url"]
    )


def log_response(response) -> None:
    """
    Logs the response metadata and token usage (if available).
    """
    try:
        if hasattr(response, "model_dump"):
            logger.info(f"Response payload: {response.model_dump()}")
        else:
            logger.info(f"Response payload: {str(response)}")
    except Exception as e:
        logger.warning(f"Could not serialize response payload: {e}")

    try:
        usage = getattr(response, "usage", None)
        if usage:
            prompt_tokens = getattr(usage, "prompt_tokens", None)
            completion_tokens = getattr(usage, "completion_tokens", None)
            total_tokens = getattr(usage, "total_tokens", None)
            
            if prompt_tokens is not None or completion_tokens is not None or total_tokens is not None:
                logger.info(
                    f"API token usage: Prompt/Input: {prompt_tokens}, "
                    f"Completion/Output: {completion_tokens}, "
                    f"Total: {total_tokens}"
                )
            else:
                logger.info("API token usage: Not available")
        else:
            logger.info("API token usage: Not available")
    except Exception as e:
        logger.warning(f"Error reading token usage from API: {e}")


def execute_turn(client: OpenAI, config: dict, history: list, user_content: str, turn_num: int) -> tuple:
    """
    Executes a single turn in the chat.
    Appends the user message, calculates token count, performs trimming if threshold is met,
    makes the API call, logs usage, and updates the history.
    """
    logger.info(f"--- Turn {turn_num} ---")
    
    # 1. Add current user message to temp history to check total tokens
    history.append({"role": "user", "content": user_content})
    
    # 2. Count tokens before management
    tokens_before = history_manager.count_tokens(history, config["model"])
    logger.info(f"History tokens before management: {tokens_before}")
    logger.info(f"History budget: {config['max_history_tokens']} (Threshold: {int(config['max_history_tokens'] * config['history_trim_threshold'])})")
    
    # 3. Trim history if necessary
    trimmed_history, tokens_after, trimmed_occurred = history_manager.trim_history(
        history,
        config["max_history_tokens"],
        config["history_trim_threshold"],
        config["model"]
    )
    
    if trimmed_occurred:
        # Update our active history to the trimmed version
        history = trimmed_history
    else:
        logger.info("No trimming required.")
        
    # 4. Make the API request
    logger.info("Sending chat completion request...")
    logger.info(f"Request messages: {history}")
    
    response = client.chat.completions.create(
        model=config["model"],
        messages=history,
        max_tokens=config["max_response_tokens"]
    )
    
    logger.info("Response received successfully.")
    log_response(response)
    
    assistant_content = response.choices[0].message.content
    print(f"Assistant: {assistant_content}")
    
    # 5. Append assistant reply to history
    history.append({"role": "assistant", "content": assistant_content})
    
    return history


def run_demo(client: OpenAI, config: dict):
    """
    Runs a deterministic demonstration to trigger history trimming.
    """
    import time
    print("\n=== History Management Demo ===\n")
    print(f"Configured history budget: {config['max_history_tokens']} tokens")
    print(f"Trim threshold: {int(config['history_trim_threshold'] * 100)}% ({int(config['max_history_tokens'] * config['history_trim_threshold'])} tokens)\n")
    
    # Predefined turns with long prompts to force budget overflow
    demo_turns = [
        "Explain what Retrieval-Augmented Generation (RAG) is in detail. Please write a long paragraph of at least 120 words covering search query translation, vector retrieval, and contextual generation.",
        "Explain why document chunking is critical in RAG pipelines. Provide a comprehensive bulleted list detailing semantic chunk boundaries, overlap ratio, token limits, and retrieve efficiency.",
        "Compare sparse text retrieval algorithms (like BM25 keyword search) with dense vector retrieval embeddings. Elaborate on hybrid search strategies, re-ranking models, and semantic density.",
        "Describe the typical challenges associated with parsing complex PDF documents in real-world RAG systems, such as handling structured tables, inline images, and multi-column document layouts.",
        "Explain evaluation frameworks for RAG systems (like Ragas or TruLens). Detail metrics such as faithfulness, answer relevance, context recall, and semantic similarity."
    ]
    
    history = [{"role": "system", "content": STAFF_ASSISTANT_SYSTEM_PROMPT}]
    
    for i, prompt in enumerate(demo_turns, 1):
        try:
            if i > 1:
                logger.info("Sleeping for 15 seconds to respect API rate limits...")
                time.sleep(15)
            history = execute_turn(
                client, config, history, render_rag_request("", prompt), i
            )
            print()
        except Exception as e:
            logger.error(f"Error in Demo Turn {i}: {e}")
            raise e
            
    # Final sanity check on system message preservation
    system_preserved = len(history) > 0 and history[0]["role"] == "system"
    final_tokens = history_manager.count_tokens(history, config["model"])
    
    print("\n=== Demo Completed Successfully ===")
    print(f"System message preserved: {'YES' if system_preserved else 'NO'}")
    print(f"Final managed history tokens: {final_tokens} / {config['max_history_tokens']}")
    print("===================================\n")


def run_interactive(client: OpenAI, config: dict):
    """
    Runs an interactive chat loop in the console.
    """
    print("\nRAG Chat — type 'exit' or 'quit' to quit\n")
    
    history = [{"role": "system", "content": STAFF_ASSISTANT_SYSTEM_PROMPT}]
    
    turn_num = 1
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
                
            history = execute_turn(
                client, config, history, render_rag_request("", user_input), turn_num
            )
            turn_num += 1
            print()
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except openai.AuthenticationError:
            logger.error(
                "Authentication failed (401). Check that your API key is valid "
                "and correctly configured in .env."
            )
            sys.exit(1)
        except openai.RateLimitError:
            logger.error("Rate limit exceeded (429). Please wait and try again later.")
            sys.exit(1)
        except openai.APIConnectionError as e:
            logger.error(f"Connection error: Could not connect to the API server. Details: {e}")
            sys.exit(1)
        except openai.APITimeoutError as e:
            logger.error(f"Timeout error: The request to the API server timed out. Details: {e}")
            sys.exit(1)
        except openai.APIStatusError as e:
            if e.status_code == 401:
                logger.error(
                    "Authentication failed (401). Check that your API key is valid "
                    "and correctly configured in .env."
                )
            elif e.status_code == 400:
                try:
                    err_data = e.response.json()
                    if isinstance(err_data, dict):
                        err_val = err_data.get("error")
                        if isinstance(err_val, dict):
                            err_msg = err_val.get("message") or str(err_val)
                        else:
                            err_msg = str(err_val) if err_val else str(err_data)
                    else:
                        err_msg = str(err_data)
                except Exception:
                    err_msg = str(e)
                logger.error(f"API request failed (400): {err_msg}")
            elif e.status_code == 429:
                logger.error("Rate limit exceeded (429). Please wait and try again later.")
            else:
                logger.error(f"API status error ({e.status_code}): {e.message}")
            sys.exit(1)
        except openai.APIError as e:
            logger.error(f"API error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Multi-turn conversation history RAG chat client.")
    parser.add_argument("--demo", action="store_true", help="Run the overflow demonstration mode.")
    parser.add_argument("--parameters", action="store_true", help="Run the parameter experiments.")
    args = parser.parse_args()
    
    try:
        config = load_config()
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
        
    client = create_client(config)
    
    try:
        if args.parameters:
            import experiment_runner
            experiment_runner.run_parameter_experiments(client, config)
        elif args.demo:
            run_demo(client, config)
        else:
            run_interactive(client, config)
    except openai.AuthenticationError:
        logger.error(
            "Authentication failed (401). Check that your API key is valid "
            "and correctly configured in .env."
        )
        sys.exit(1)
    except openai.RateLimitError:
        logger.error("Rate limit exceeded (429). Please wait and try again later.")
        sys.exit(1)
    except openai.APIConnectionError as e:
        logger.error(f"Connection error: Could not connect to the API server. Details: {e}")
        sys.exit(1)
    except openai.APITimeoutError as e:
        logger.error(f"Timeout error: The request to the API server timed out. Details: {e}")
        sys.exit(1)
    except openai.APIStatusError as e:
        if e.status_code == 401:
            logger.error(
                "Authentication failed (401). Check that your API key is valid "
                "and correctly configured in .env."
            )
        elif e.status_code == 400:
            try:
                err_data = e.response.json()
                if isinstance(err_data, dict):
                    err_val = err_data.get("error")
                    if isinstance(err_val, dict):
                        err_msg = err_val.get("message") or str(err_val)
                    else:
                        err_msg = str(err_val) if err_val else str(err_data)
                else:
                    err_msg = str(err_data)
            except Exception:
                err_msg = str(e)
            logger.error(f"API request failed (400): {err_msg}")
        elif e.status_code == 429:
            logger.error("Rate limit exceeded (429). Please wait and try again later.")
        else:
            logger.error(f"API status error ({e.status_code}): {e.message}")
        sys.exit(1)
    except openai.APIError as e:
        logger.error(f"API error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
