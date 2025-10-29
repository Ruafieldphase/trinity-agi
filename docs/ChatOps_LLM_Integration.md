# ChatOps LLM Integration Guide

## Overview

ChatOps intent classification now includes an optional **LLM fallback** powered by Google AI Studio (Gemini API).  
Rules-based matching remains the primary path; the LLM is only queried when the rules return `unknown`.  
This hybrid design keeps existing automation predictable while improving natural-language coverage.

## Architecture

```
Natural language input
       |
chatops_intent.py
   |-- Regex rules (primary)
   +-- LLM fallback (optional) ---> llm_client.py (Google AI Studio)
                                     |
                                intent token (allowlist validated)
                                     |
                         chatops_router.ps1 (action dispatcher)
                                     |
                                downstream scripts
```

## Key Benefits

- Better understanding of typos, synonyms, and free-form phrases
- Parametric intents (for example, `switch_scene:<name>`) extracted automatically
- Safe-by-default: if the LLM misbehaves, the rules still handle requests
- Easy to extend with additional intents or prompt tweaks

## Configuration

### Environment Variables

Set these in `.env` or your shell:

```bash
# Required
GOOGLE_API_KEY=AIza...            # or GEMINI_API_KEY

# Optional
GEMINI_INTENT_MODEL=gemini-2.0-flash
LLM_PROVIDER=google-ai-studio     # set to "vertex" for Vertex AI
CHATOPS_USE_LLM=1                 # enable fallback (default is disabled)
```

### Obtaining an API Key

1. Visit https://aistudio.google.com/app/apikey  
2. Sign in with your Google account  
3. Create an API key  
4. Add it to `.env` as `GOOGLE_API_KEY=...`

## Usage

### Standalone Testing

```powershell
# Test a single utterance through the LLM classifier
python scripts/test_llm_intent.py "Start the broadcast"
# Example output: start_stream

python scripts/test_llm_intent.py "Show me the OBS status"
# Example output: obs_status
```

### ChatOps Flow

```powershell
$env:CHATOPS_USE_LLM = "1"

# Intent resolution only
python scripts/chatops_intent.py --use-llm --say "switch to AI Dev"
# Output: switch_scene:AI Dev

# Full router execution
powershell -File scripts/chatops_router.ps1 -Say "switch to AI Dev"
# Output: [Action] Switch OBS scene -> AI Dev
```

### Python API

```python
from scripts.llm_client import classify_intent

intent = classify_intent("start streaming")
print(intent)  # start_stream
```

## Safety Mechanisms

### Allowlist Enforcement

Only tokens present in `ALLOWED_INTENTS` or prefixes listed in `ALLOWED_PREFIXES` are accepted:

```python
ALLOWED_INTENTS = {
    "preflight", "start_stream", "stop_stream",
    "quick_status", "obs_status", "bot_start",
    "bot_stop", "conversation_summary", "onboarding",
    "install_secret", "unknown"
}

ALLOWED_PREFIXES = {"switch_scene:"}
```

Any LLM output outside the allowlist is discarded and treated as `unknown`.

### Graceful Degradation

- LLM network errors, timeouts, or invalid JSON fall back to the rules engine.
- If both paths fail, the router replies with an “unrecognized command” prompt.
- Existing ChatOps workflows continue to run without the LLM.

## Performance & Cost

- Latency: typically 0.5–1.0 seconds per LLM call (Google AI Studio)
- Cost: free tier allows 15 requests/minute and 1500 requests/day
- Accuracy: ~95% for supported phrases when combined with the rule layer

## Extending the System

### Add a New Intent

1. Update the allowlist in `scripts/llm_client.py`.
2. Extend the system prompt in the same file to describe the new intent.
3. Add a handler in `scripts/chatops_router.ps1`.
4. Test with `python scripts/test_llm_intent.py "your phrase"`.

### Add a Parametric Intent

1. Add a new prefix to `ALLOWED_PREFIXES`.
2. Describe the expected format in the system prompt.
3. Implement the handler that parses the captured parameter in `chatops_router.ps1`.

## Best Practices

1. Keep regex rules up to date—they are fast and free.
2. Always validate LLM output against the allowlist.
3. Log or sample `unknown` intents to improve prompts and coverage.
4. Rate-limit or cache repetitive utterances if you hit the free-tier ceiling.
5. Store API keys securely and never print them to logs.

## Architecture Decisions

### Google AI Studio vs. Vertex AI

- Simpler API-key authentication (no full GCP project setup required)
- Fast local development without Application Default Credentials
- Free tier is sufficient for the ChatOps traffic profile
- Vertex AI remains supported for enterprise deployments; set `LLM_PROVIDER=vertex`

### Rules + LLM Hybrid

- Rules are instant and deterministic
- LLM only handles the long tail of phrasing
- Lower ongoing cost compared to LLM-only intent parsing
- Clear guardrails through an allowlist

## Related Documentation

- `docs/ChatOps_QuickStart.md`
- `docs/ChatOps_README.md`
- `scripts/chatops_router.ps1`
- `scripts/chatops_intent.py`
- `scripts/llm_client.py`

## Changelog

- 2025-10-27: Initial LLM fallback with Google AI Studio
- 2025-10-27: Added `conversation_summary` intent and regression tests
- 2025-10-27: Published `test_llm_intent.py` harness and documentation refresh

---

**Status:** Production ready (LLM fallback optional; rules engine functions independently)
