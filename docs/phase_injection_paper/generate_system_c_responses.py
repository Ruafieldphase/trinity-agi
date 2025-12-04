#!/usr/bin/env python3
"""
Generate System C responses using a prompt spec and context bundle.

Example:
    python generate_system_c_responses.py \
        --bundle inputs/input_bundle.jsonl \
        --prompt inputs/prompt_spec_v8.md \
        --model solar:10.7b \
        --output outputs/system_c_prompt_fix_output.jsonl
"""
import argparse
import json
import re
from pathlib import Path
from typing import Dict, Any, List

import requests


def parse_markdown_prompts(path: Path) -> Dict[str, str]:
    text = path.read_text(encoding="utf-8")
    prompts: Dict[str, str] = {}

    # match sections like ## Title ... ``` ... ```
    for match in re.finditer(r"##\s+(.*?)\n+```(.*?)```", text, re.S):
        title = match.group(1).strip().lower()
        body = match.group(2).strip()
        prompts[title] = body
    return prompts


def format_facts(facts: List[str]) -> str:
    if not facts:
        return "(none)"
    return "\n".join(f"- {fact}" for fact in facts)


def format_quotes(quotes: List[str]) -> str:
    if not quotes:
        return "(none)"
    return "\n".join(f"- {quote}" for quote in quotes)


def format_metadata(metadata: Dict[str, Any]) -> str:
    formatted = []
    for key, value in metadata.items():
        formatted.append(f"{key}: {value}")
    return "\n".join(formatted) if formatted else "(none)"


def build_prompt(system_prompt: str, user_template: str, entry: Dict[str, Any]) -> str:
    user_prompt = (
        user_template.replace("{{context_summary}}", entry.get("context_summary", ""))
        .replace("{{facts}}", format_facts(entry.get("facts", [])))
        .replace("{{quotes}}", format_quotes(entry.get("quotes", [])))
        .replace("{{metadata}}", format_metadata(entry.get("metadata", {})))
    )
    return f"{system_prompt}\n\n{user_prompt}"


def generate_response(model: str, prompt: str, base_url: str) -> str:
    payload = {"model": model, "prompt": prompt, "stream": False}
    resp = requests.post(f"{base_url}/api/generate", json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", "").strip()


def main():
    ap = argparse.ArgumentParser(description="Generate System C outputs via Ollama.")
    ap.add_argument("--bundle", required=True, help="Path to input_bundle.jsonl")
    ap.add_argument("--prompt", required=True, help="Path to prompt_spec markdown")
    ap.add_argument("--model", default="solar:10.7b", help="Ollama model name")
    ap.add_argument("--output", required=True, help="Destination JSONL for generated outputs")
    ap.add_argument("--base-url", default="http://localhost:11434", help="Ollama base URL")
    args = ap.parse_args()

    bundle_path = Path(args.bundle)
    prompt_path = Path(args.prompt)
    output_path = Path(args.output)

    prompts = parse_markdown_prompts(prompt_path)
    system_prompt = prompts.get("system prompt")
    user_prompt_template = prompts.get("user prompt")
    if not system_prompt or not user_prompt_template:
        raise ValueError("System prompt or user prompt not found in prompt_spec.")

    entries = []
    for line in bundle_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entries.append(json.loads(line))

    output_lines = []
    for idx, entry in enumerate(entries):
        prompt = build_prompt(system_prompt, user_prompt_template, entry)
        print(f"[INFO] Generating sample #{idx} with model {args.model}...")
        response = generate_response(args.model, prompt, args.base_url)
        output_lines.append(json.dumps({"sample_id": idx, "prompt": prompt, "response": response}))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(output_lines), encoding="utf-8")
    print(f"[INFO] Wrote {len(output_lines)} responses to {output_path}")


if __name__ == "__main__":
    main()
