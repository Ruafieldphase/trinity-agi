#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test script for LLM-backed ChatOps intent classification.

Usage:
  python scripts/test_llm_intent.py "OBS가 켜져있나요?"
  python scripts/test_llm_intent.py "스트림 상태 보여줘"
"""
from __future__ import annotations
import os
import sys

# Load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.llm_client import classify_intent


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_llm_intent.py '<utterance>'", file=sys.stderr)
        return 2
    
    utter = " ".join(sys.argv[1:])
    print(f"Input: {utter}")
    
    # Check environment - prefer Google AI Studio
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    project = os.getenv("VERTEXAI_PROJECT") or os.getenv("GCP_PROJECT")
    location = os.getenv("VERTEXAI_LOCATION") or os.getenv("GCP_LOCATION")
    model = os.getenv("GEMINI_INTENT_MODEL", "gemini-2.0-flash")
    
    if api_key:
        masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"Provider: Google AI Studio")
        print(f"API Key: {masked}")
        print(f"Model: {model}")
    elif project:
        print(f"Provider: Vertex AI")
        print(f"Project: {project}")
        print(f"Location: {location}")
        print(f"Model: {model}")
    else:
        print("ERROR: No GOOGLE_API_KEY/GEMINI_API_KEY or GCP_PROJECT set.", file=sys.stderr)
        return 2
    
    result = classify_intent(utter)
    print(f"Result: {result}")
    
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
