#!/usr/bin/env python3
"""
Gemini CLI wrapper using Google Generative AI SDK.
Reads prompt from stdin and outputs Gemini response to stdout.
Requires GOOGLE_API_KEY environment variable.
"""

import sys
import os
import argparse
from typing import Optional

try:
    import google.generativeai as genai
except ImportError:
    print("Error: google-generativeai package not installed", file=sys.stderr)
    print("Install with: pip install google-generativeai", file=sys.stderr)
    sys.exit(1)

from fdo_agi_repo.utils.emoji_filter import remove_emojis

# Ensure UTF-8 output to avoid cp949 encoding issues on Windows terminals.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass


DEFAULT_MODEL = "models/gemini-2.0-flash"


def chat_with_gemini(
    prompt: str,
    model_name: str = DEFAULT_MODEL,
    max_output_tokens: int = 2048,
    temperature: float = 0.7,
) -> str:
    """
    Send a prompt to Gemini and return the response.

    Args:
        prompt: The input prompt
        model_name: Gemini model name
        max_output_tokens: Maximum tokens in response
        temperature: Sampling temperature

    Returns:
        Generated text response (safe for Windows pipelines)
    """
    # Get API key from environment
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable not set. "
            "Get your API key from https://makersuite.google.com/app/apikey"
        )

    # Configure API
    genai.configure(api_key=api_key)

    # Create model instance
    model = genai.GenerativeModel(model_name)

    # Configure generation
    generation_config = genai.types.GenerationConfig(
        max_output_tokens=max_output_tokens,
        temperature=temperature,
    )

    # Configure safety settings to be less restrictive for research use
    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_ONLY_HIGH",
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_ONLY_HIGH",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_ONLY_HIGH",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_ONLY_HIGH",
        },
    ]

    # Generate response
    response = model.generate_content(
        prompt,
        generation_config=generation_config,
        safety_settings=safety_settings,
    )

    # Handle blocked or empty responses gracefully
    if not response.candidates:
        return "[Response blocked by safety filters]"

    # Try to get text, handle blocked content
    try:
        text = response.text
    except ValueError as e:
        # Response might be blocked or have no valid parts
        if response.candidates:
            candidate = response.candidates[0]
            finish_reason = candidate.finish_reason
            # finish_reason enum: FINISH_REASON_UNSPECIFIED=0, STOP=1, MAX_TOKENS=2,
            # SAFETY=3, RECITATION=4, OTHER=5
            # Note: finish_reason=2 can mean safety block in some API versions
            if finish_reason in (2, 3):
                # Try to get partial content if available
                if candidate.content and candidate.content.parts:
                    try:
                        partial_text = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
                        if partial_text:
                            return partial_text
                    except:
                        pass
                return "[Response blocked or incomplete - please rephrase your prompt]"
            elif finish_reason == 4:
                return "[Response blocked - potential copyright issue]"
        return f"[Unable to generate response: {e}]"

    if not text:
        return "[Empty response from API]"

    # Sanitize output for Windows pipeline compatibility:
    # 1. Remove emojis
    # 2. Remove surrogate pairs (unpaired UTF-16 surrogates)
    # 3. Replace problematic characters with safe alternatives
    text = remove_emojis(text)
    
    sanitized = []
    for ch in text:
        code_point = ord(ch)
        # Skip surrogate range (0xD800-0xDFFF)
        if 0xD800 <= code_point <= 0xDFFF:
            continue
        # Replace with ASCII-safe alternatives for very rare control chars
        if code_point < 32 and ch not in '\n\r\t':
            continue
        sanitized.append(ch)

    return "".join(sanitized)


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Chat with Gemini via Google AI API"
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Gemini model name (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=2048,
        help="Maximum output tokens (default: 2048)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (default: 0.7)"
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read prompt from stdin"
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Prompt text (or use --stdin)"
    )
    
    args = parser.parse_args()
    
    # Ensure stdin uses UTF-8 encoding and handles surrogates
    try:
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

    # Get prompt from stdin or argument
    if args.stdin or not sys.stdin.isatty():
        prompt_text = sys.stdin.read().strip()
    elif args.prompt:
        prompt_text = args.prompt
    else:
        parser.error("Provide prompt as argument or via --stdin")

    # Sanitize input prompt to remove any surrogate characters
    sanitized_prompt = []
    for ch in prompt_text:
        code_point = ord(ch)
        if 0xD800 <= code_point <= 0xDFFF:
            continue  # Skip surrogates
        sanitized_prompt.append(ch)
    prompt_text = "".join(sanitized_prompt)
    
    if not prompt_text:
        print("Error: Empty prompt", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Generate response
        response = chat_with_gemini(
            prompt=prompt_text,
            model_name=args.model,
            max_output_tokens=args.max_tokens,
            temperature=args.temperature,
        )

        # Output response - simple UTF-8 output with replace error handling
        # The chat_with_gemini function already sanitized the text
        print(response)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
