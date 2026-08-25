import logging
import tiktoken

logger = logging.getLogger(__name__)


def count_tokens(messages: list, model: str) -> int:
    """
    Calculates the total token count of a list of messages.
    
    If the model is supported by tiktoken, uses the exact tokenizer.
    Otherwise, falls back to using the 'cl100k_base' encoding as a safe approximation,
    and logs a warning.
    """
    try:
        # Check if model is supported directly
        try:
            encoding = tiktoken.encoding_for_model(model)
            # Log exact tokenizer usage (not needed for every call, but we can do it at debug level)
        except KeyError:
            # Fallback to cl100k_base for Groq and xAI models
            encoding = tiktoken.get_encoding("cl100k_base")
            logger.debug(
                f"Model '{model}' not directly supported by tiktoken; "
                f"using 'cl100k_base' encoding as an approximation."
            )
    except Exception as e:
        # Safe character-based fallback if tiktoken errors or is unavailable
        total_chars = sum(len(m.get("content", "")) + len(m.get("role", "")) for m in messages)
        # Add basic overhead of 4 tokens per message plus 2 tokens for response priming
        estimated_tokens = int(total_chars / 4) + len(messages) * 4 + 2
        logger.warning(
            f"Error loading tiktoken encoding ({e}). "
            f"Using approximate character-based estimation: {estimated_tokens} tokens."
        )
        return estimated_tokens

    # Standard OpenAI token counting implementation
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # Every message follows <im_start>{role/name}\n{content}<im_end>\n
        for key, value in message.items():
            num_tokens += len(encoding.encode(str(value)))
    num_tokens += 2  # Every reply is primed with <im_start>assistant
    return num_tokens


def trim_history(messages: list, max_tokens: int, threshold: float, model: str) -> tuple:
    """
    Trims the conversation history if it meets or exceeds the threshold of the token budget.
    
    Preserves:
      - The system message at index 0.
      - The most recent messages (specifically the user prompt at the end).
    
    Removes:
      - User/Assistant pairs (oldest first).
      
    Returns:
      (trimmed_messages, final_token_count, trimming_occurred)
    """
    limit = int(max_tokens * threshold)
    tokens = count_tokens(messages, model)
    
    if tokens < limit:
        return messages, tokens, False
        
    logger.info(f"History token count: {tokens} / {max_tokens} (Threshold: {limit})")
    logger.info("History reached/exceeded threshold. Starting trimming...")
    
    trimmed = list(messages)
    trimmed_any = False
    
    # We must have at least [system, user, assistant, current_user] (length 4)
    # to pop the oldest user-assistant turn (index 1 and 2).
    while len(trimmed) >= 4 and count_tokens(trimmed, model) >= limit:
        if trimmed[1]["role"] == "user" and trimmed[2]["role"] == "assistant":
            removed_user = trimmed.pop(1)
            removed_assistant = trimmed.pop(1)
            trimmed_any = True
            logger.info(
                f"Removed turn: USER ({removed_user['content'][:30]}...) "
                f"+ ASSISTANT ({removed_assistant['content'][:30]}...)"
            )
        else:
            # Prevent infinite loop if roles are out of order
            logger.warning("Roles in conversation history are out of expected sequence (user, assistant). Aborting trim.")
            break
            
    final_tokens = count_tokens(trimmed, model)
    logger.info(f"Token count after trimming: {final_tokens} / {max_tokens}")
    
    return trimmed, final_tokens, trimmed_any
