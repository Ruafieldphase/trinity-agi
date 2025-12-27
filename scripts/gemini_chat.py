#!/usr/bin/env python3
"""
Gemini CLI wrapper using Vertex AI SDK.
Reads prompt from stdin and outputs Gemini response to stdout.
"""

import sys
import os
import argparse
from typing import Optional
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig


def chat_with_gemini(
    prompt: str,
    project_id: str = "naeda-genesis",
    location: str = "us-central1",
    model_name: str = "gemini-2.5-flash",
    max_output_tokens: int = 2048,
    temperature: float = 0.7,
) -> str:
    """
    Send a prompt to Gemini and return the response.
    
    Args:
        prompt: The input prompt
        project_id: GCP project ID
        location: GCP region
        model_name: Gemini model name
        max_output_tokens: Maximum tokens in response
        temperature: Sampling temperature
        
    Returns:
        Generated text response
    """
    # Initialize Vertex AI (prefer env vars when provided)
    # Priority: explicit args > environment > defaults
    env_project = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
    env_location = os.getenv("GCP_LOCATION") or os.getenv("GOOGLE_CLOUD_REGION") or os.getenv("VERTEX_LOCATION")
    env_model = os.getenv("VERTEX_MODEL_GEMINI") or os.getenv("GEMINI_MODEL")
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

    use_project = project_id or env_project or "naeda-genesis"
    use_location = location or env_location or "us-central1"
    use_model = model_name or env_model or "gemini-2.5-flash"

    # Pass api_key to init if present; otherwise rely on ADC
    if api_key:
        vertexai.init(project=use_project, location=use_location, api_key=api_key)
    else:
        vertexai.init(project=use_project, location=use_location)
    
    # Configure generation parameters
    generation_config = GenerationConfig(
        max_output_tokens=max_output_tokens,
        temperature=temperature,
    )
    
    # Create model instance (fallback list for environments where some models are not enabled)
    candidates = [use_model, "gemini-2.0-flash-001", "gemini-1.5-flash-002"]
    last_err: Optional[Exception] = None
    model = None
    for cand in candidates:
        try:
            model = GenerativeModel(cand)
            use_model = cand
            break
        except Exception as e:
            last_err = e
            continue
    if model is None:
        raise RuntimeError(f"Failed to initialize Gemini model (tried: {', '.join(candidates)}): {last_err}")
    
    # Generate response
    response = model.generate_content(
        prompt,
        generation_config=generation_config,
        stream=False,
    )
    
    return response.text


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Chat with Gemini via Vertex AI"
    )
    parser.add_argument(
        "--project",
        default=os.getenv("GCP_PROJECT", "naeda-genesis"),
        help="GCP project ID (env: GCP_PROJECT)"
    )
    parser.add_argument(
        "--location",
        default=os.getenv("GCP_LOCATION", os.getenv("GOOGLE_CLOUD_REGION", "us-central1")),
        help="GCP region (env: GCP_LOCATION)"
    )
    parser.add_argument(
        "--model",
        default=os.getenv("VERTEX_MODEL_GEMINI", os.getenv("GEMINI_MODEL", "gemini-1.5-flash-002")),
        help="Gemini model name (env: VERTEX_MODEL_GEMINI)"
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
    
    # Get prompt from stdin or argument
    if args.stdin or not sys.stdin.isatty():
        prompt_text = sys.stdin.read().strip()
    elif args.prompt:
        prompt_text = args.prompt
    else:
        parser.error("Provide prompt as argument or via --stdin")
    
    if not prompt_text:
        print("Error: Empty prompt", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Generate response
        response = chat_with_gemini(
            prompt=prompt_text,
            project_id=args.project,
            location=args.location,
            model_name=args.model,
            max_output_tokens=args.max_tokens,
            temperature=args.temperature,
        )
        
        # Output response
        print(response)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
