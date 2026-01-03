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
from workspace_root import get_workspace_root
from typing import Optional

# Import emoji filter
sys.path.insert(0, str(get_workspace_root() / "fdo_agi_repo"))
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


def _load_dotenv_value(name: str) -> str | None:
    """
    Process env에 값이 없으면 워크스페이스 .env에서 읽어온다.
    - 값 출력 금지(키/토큰 보호)
    - 기존 env를 덮어쓰지 않음
    """
    try:
        root = get_workspace_root()
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
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or _load_dotenv_value("GOOGLE_API_KEY") or _load_dotenv_value("GEMINI_API_KEY")
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
        # Avoid noisy logs for missing keys if we have a fallback
        return None


def _vertex_classify(utter: str) -> Optional[str]:
    """Use Vertex AI to classify intent (fallback option)."""
    # Fallback priority: VERTEXAI_PROJECT > GCP_PROJECT
    project = os.getenv("VERTEXAI_PROJECT") or os.getenv("GCP_PROJECT")
    location = os.getenv("VERTEXAI_LOCATION") or os.getenv("GCP_LOCATION", "us-central1")
    # Prefer newer flash models; allow override via env.
    model_name = os.getenv("VERTEXAI_INTENT_MODEL") or os.getenv("VERTEX_MODEL_GEMINI", "gemini-2.0-flash-001")
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
      1. Google AI Studio (Free Tier) - Primary
      2. Vertex AI (Paid Tier) - Fallback/Override
    """
    provider = os.getenv("LLM_PROVIDER", "google-ai-studio").lower()
    
    # 1. Force AI Studio if API Key is present (Safety first)
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or _load_dotenv_value("GOOGLE_API_KEY")
    if api_key:
        result = _google_ai_studio_classify(utter)
        if result:
            return result

    # 2. Vertex AI Fallback (Only if explicitly requested or AI Studio failed)
    project = os.getenv("VERTEXAI_PROJECT") or os.getenv("GCP_PROJECT") or _load_dotenv_value("GOOGLE_CLOUD_PROJECT")
    if project:
        # LOG WARNING: Using paid tier
        if os.getenv("AGI_VERBOSE_COSTS") == "1":
            print(f"⚠️ [COST_WARNING] Falling back to Paid Vertex AI for project: {project}", file=sys.stderr)
            
        result = _vertex_classify(utter)
        if result:
            return result
    
    return None

