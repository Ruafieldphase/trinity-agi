#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Client for ChatOps intent classification.

Primary target: Google AI Studio (Gemini API)
 - Controlled via environment variables:
   - CHATOPS_USE_LLM=1 (enable in chatops_intent)
   - LLM_PROVIDER=google-ai-studio (default) | vertex
   - GOOGLE_API_KEY or GEMINI_API_KEY (required for google-ai-studio)
   - VERTEXAI_PROJECT, VERTEXAI_LOCATION (for vertex provider)
   - GEMINI_INTENT_MODEL (default: gemini-2.0-flash)

Safe-by-default:
 - Strict allowed intents; returns None (fallback to rules) if unavailable.
 - JSON-only response enforced by prompt; parser validates and sanitizes.
 - Emoji filtering applied to all LLM outputs.
"""
from __future__ import annotations

import json
import os
import sys
import warnings
from pathlib import Path
from typing import Optional

# Import emoji filter
sys.path.insert(0, str(Path(__file__).parent.parent / "fdo_agi_repo"))
from utils.emoji_filter import remove_emojis


ALLOWED_PREFIXES = {"switch_scene:"}
ALLOWED_INTENTS = {
    "preflight",
    "preflight_interactive",
    "start_stream",
    "stop_stream",
    "quick_status",
    "obs_status",
    "install_obs_deps",
    "bot_start",
    "bot_stop",
    "bot_dryrun",
    "onboarding",
    "install_secret",
    "conversation_summary",
    "unknown",
}


<<<<<<< HEAD
def _load_dotenv_value(name: str) -> str | None:
    """
    Process env에 값이 없으면 워크스페이스 .env에서 읽어온다.
    - 값 출력 금지(키/토큰 보호)
    - 기존 env를 덮어쓰지 않음
    """
    try:
        root = Path(__file__).resolve().parents[1]  # C:\workspace\agi
        for env_path in (root / ".env_credentials", root / ".env"):
            if not env_path.exists():
                continue
            for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
                s = line.strip()
                if not s or s.startswith("#") or "=" not in s:
                    continue
                k, v = s.split("=", 1)
                if k.strip() != name:
                    continue
                val = v.strip().strip('"').strip("'")
                return val or None
    except Exception:
        return None
    return None


=======
>>>>>>> origin/main
def _is_allowed(intent: str) -> bool:
    if intent in ALLOWED_INTENTS:
        return True
    return any(intent.startswith(p) for p in ALLOWED_PREFIXES)


SYSTEM_PROMPT = (
    """
    You are a ChatOps intent classifier. Classify the user's request into ONE intent token.
    Output STRICT JSON with a single field: {"intent": "..."}. No extra text.
    Allowed intents:
      - preflight
      - preflight_interactive
      - start_stream
      - stop_stream
      - quick_status
      - obs_status
      - switch_scene:<scene_name>
      - bot_start
      - bot_stop
      - bot_dryrun
      - onboarding
      - install_secret
      - conversation_summary
      - unknown

    Rules:
      - If the user's request is ambiguous or unsafe, return unknown.
      - For scene switching, return switch_scene:<name> with a short readable name.
      - Respond with JSON only. Do not include markdown or code fences.
    """
    .strip()
)


def _google_ai_studio_classify(utter: str) -> Optional[str]:
    """Use Google AI Studio (google-generativeai) to classify intent."""
<<<<<<< HEAD
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or _load_dotenv_value("GOOGLE_API_KEY") or _load_dotenv_value("GEMINI_API_KEY")
=======
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
>>>>>>> origin/main
    if not api_key:
        print("DEBUG: No GOOGLE_API_KEY or GEMINI_API_KEY found", file=sys.stderr)
        return None
    
    model_name = os.getenv("GEMINI_INTENT_MODEL", "gemini-2.0-flash")
    
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        prompt = f"System:\n{SYSTEM_PROMPT}\n\nUser:\n{utter}\n\nAnswer with JSON only."
        
        resp = model.generate_content(prompt)
        if not resp or not resp.text:
            return None
        
        text = remove_emojis(resp.text).strip()
        # Remove markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
        
        data = json.loads(text)
        intent = data.get("intent", "unknown")
        
        if _is_allowed(intent):
            return intent
        return "unknown"
    
    except Exception as e:
        print(f"DEBUG google-ai-studio failed: {e}", file=sys.stderr)
        return None


def _vertex_classify(utter: str) -> Optional[str]:
    """Use Vertex AI to classify intent (fallback option)."""
    # Fallback priority: VERTEXAI_PROJECT > GCP_PROJECT
    project = os.getenv("VERTEXAI_PROJECT") or os.getenv("GCP_PROJECT")
    location = os.getenv("VERTEXAI_LOCATION") or os.getenv("GCP_LOCATION", "us-central1")
<<<<<<< HEAD
    # Prefer newer flash models; allow override via env.
    model_name = os.getenv("VERTEXAI_INTENT_MODEL") or os.getenv("VERTEX_MODEL_GEMINI", "gemini-2.0-flash-001")
=======
    # Use gemini-1.5-flash-002 as verified in .env
    model_name = os.getenv("VERTEXAI_INTENT_MODEL") or os.getenv("VERTEX_MODEL_GEMINI", "gemini-1.5-flash-002")
>>>>>>> origin/main
    if not project:
        return None
    try:
        import vertexai  # type: ignore
        # Suppress deprecation warnings for SDK version compatibility
        warnings.filterwarnings("ignore", category=UserWarning, module="vertexai")
        
        # Try new GenerativeModel API first
        try:
            from vertexai.generative_models import GenerativeModel  # type: ignore

            vertexai.init(project=project, location=location)
            model = GenerativeModel(model_name)
            prompt = f"System:\n{SYSTEM_PROMPT}\n\nUser:\n{utter}\n\nAnswer with JSON only."
            resp = model.generate_content(prompt, generation_config={"temperature": 0})
            # Extract text from response
            if hasattr(resp, "text") and resp.text:
                text = remove_emojis(resp.text)
            elif hasattr(resp, "candidates") and resp.candidates:
                # Try to extract from candidates list
                parts = []
                for candidate in resp.candidates:
                    if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                        for part in candidate.content.parts:
                            if hasattr(part, "text"):
                                parts.append(remove_emojis(part.text))
                text = "".join(parts) if parts else None
            else:
                text = None
        except Exception as e:
            # Fallback to legacy TextGenerationModel if available
            import sys, traceback
            print(f"DEBUG GenerativeModel failed: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            from vertexai.language_models import TextGenerationModel  # type: ignore

            vertexai.init(project=project, location=location)
            # Known legacy text model; allow override via env if needed
            legacy_model = os.getenv("VERTEXAI_LEGACY_TEXT_MODEL", "text-bison@001")
            model = TextGenerationModel.from_pretrained(legacy_model)
            prompt = (
                SYSTEM_PROMPT
                + "\n\nUser: "
                + utter
                + "\n\nAnswer with JSON only."
            )
            pred = model.predict(prompt=prompt, temperature=0)
            text = remove_emojis(getattr(pred, "text", "")) if hasattr(pred, "text") else None
        if not text:
            return None
        # Extract first JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        data = json.loads(text[start : end + 1])
        intent = str(data.get("intent", "unknown")).strip()
        if not _is_allowed(intent):
            return None
        return intent
    except Exception:
        # Silently fail and fallback to rules
        return None


def classify_intent(utter: str) -> Optional[str]:
    """
    Classify user utterance into ChatOps intent token.
    
    Priority order:
      1. Google AI Studio (if GOOGLE_API_KEY or GEMINI_API_KEY set)
      2. Vertex AI (if VERTEXAI_PROJECT or GCP_PROJECT set)
      3. None (fallback to rules-based)
    """
    provider = os.getenv("LLM_PROVIDER", "google-ai-studio").lower()
    
    # Try Google AI Studio first (primary method)
    if provider in {"google-ai-studio", "gemini", "google"}:
        result = _google_ai_studio_classify(utter)
        if result:
            return result
    
    # Fallback to Vertex AI if configured
    if provider in {"vertex", "vertexai", "gcp"}:
        result = _vertex_classify(utter)
        if result:
            return result
    
    # Auto-detect: try Google AI Studio first, then Vertex
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        result = _google_ai_studio_classify(utter)
        if result:
            return result
    
    project = os.getenv("VERTEXAI_PROJECT") or os.getenv("GCP_PROJECT")
    if project:
        result = _vertex_classify(utter)
        if result:
            return result
    
    # No provider configured or all failed
    return None

