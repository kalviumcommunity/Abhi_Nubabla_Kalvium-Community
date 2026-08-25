import os
import sys
import logging
import openai
from openai import OpenAI
from dotenv import load_dotenv

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
        "model": os.getenv("OPENAI_MODEL")
    }
    
    missing_vars = [k for k, v in config.items() if not v or v.strip() == ""]
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


def send_chat_request(client: OpenAI, model: str):
    """
    Sends a chat completion request to the OpenAI-compatible endpoint.
    """
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant. Answer clearly and concisely."},
        {"role": "user", "content": "Explain what Retrieval-Augmented Generation is in two sentences."}
    ]
    
    logger.info("Sending chat completion request...")
    logger.info(f"Request messages: {messages}")
    
    return client.chat.completions.create(
        model=model,
        messages=messages
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
                    f"Token usage: Prompt/Input: {prompt_tokens}, "
                    f"Completion/Output: {completion_tokens}, "
                    f"Total: {total_tokens}"
                )
            else:
                logger.info("Token usage: Not available")
        else:
            logger.info("Token usage: Not available")
    except Exception as e:
        logger.warning(f"Error reading token usage: {e}")


def main():
    try:
        # Load and validate environment variables
        config = load_config()
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
        
    client = create_client(config)
    
    try:
        # Make the API call
        response = send_chat_request(client, config["model"])
        
        # Log payload details and token usage
        logger.info("Response received successfully.")
        log_response(response)
        
        # Print actual chat completion text to terminal
        print(f"Assistant: {response.choices[0].message.content}")
        
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
