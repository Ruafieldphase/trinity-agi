"""
Emoji Filter Utility
====================

Remove emojis from LLM outputs to ensure clean, professional communication.
Works with Gemini, Claude, OpenAI, and other LLM providers.
"""
import re
import os
from typing import Optional


# Emoji regex pattern covering only emoji ranges (NOT text characters like Korean/Chinese):
# - Emoticons (U+1F600-U+1F64F)
# - Symbols & Pictographs (U+1F300-U+1F5FF)
# - Transport & Map Symbols (U+1F680-U+1F6FF)
# - Supplemental Symbols (U+1F900-U+1F9FF)
# - Flags (U+1F1E0-U+1F1FF)
# - Variation selectors (U+FE0F, U+FE0E)
# - Skin tone modifiers (U+1F3FB-U+1F3FF)
# - Zero-Width Joiner (U+200D) for multi-part emojis
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U00002700-\U000027BF"  # dingbats (narrowed range)
    "\U0001F3FB-\U0001F3FF"  # skin tone modifiers
    "\U0000FE0F"             # variation selector-16 (emoji style)
    "\U0000FE0E"             # variation selector-15 (text style)
    "\U0000200D"             # zero-width joiner
    "]+",
    flags=re.UNICODE
)


def remove_emojis(text: Optional[str], enabled: Optional[bool] = None) -> str:
    """
    Remove all emojis from text.
    
    Args:
        text: Input text (may contain emojis)
        enabled: Override for filtering (defaults to EMOJI_FILTER_ENABLED env var)
    
    Returns:
        Text with emojis removed, or empty string if input was None
        
    Example:
        >>> remove_emojis("Hello 👋 World 🌍!")
        "Hello  World !"
    """
    if text is None:
        return ""
    
    # Check if filtering is enabled
    if enabled is None:
        enabled = os.environ.get("EMOJI_FILTER_ENABLED", "1").lower() in ("1", "true", "yes")
    
    if not enabled:
        return text
    
    return EMOJI_PATTERN.sub("", text)


def filter_llm_response(response: Optional[str]) -> str:
    """
    Filter LLM response to remove emojis.
    Alias for remove_emojis() for clarity in LLM integration contexts.
    """
    return remove_emojis(response)
