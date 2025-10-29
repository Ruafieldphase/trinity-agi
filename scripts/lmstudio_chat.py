from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Proxy stdin prompt to an LM Studio HTTP endpoint (OpenAI compatible)."
    )
    parser.add_argument(
        "--endpoint",
        default="http://localhost:1234",
        help="Base URL of the LM Studio server (e.g., http://192.168.0.67:8080).",
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Model name as exposed by LM Studio (check the server UI).",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="Maximum tokens to generate.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature.",
    )
    return parser.parse_args()


def main() -> None:
    # UTF-8 인코딩 강제 설정
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if sys.stdin.encoding != 'utf-8':
        import io
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    
    args = parse_args()

    prompt = sys.stdin.read().strip()
    if not prompt:
        print("[lmstudio_chat] No prompt received on stdin.", file=sys.stderr)
        sys.exit(1)

    url = args.endpoint.rstrip("/") + "/v1/chat/completions"

    payload: Dict[str, Any] = {
        "model": args.model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
        "stream": False,
    }

    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=240,
        )
    except requests.RequestException as exc:
        print(f"[lmstudio_chat] Request failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if response.status_code >= 400:
        print(
            f"[lmstudio_chat] HTTP {response.status_code}: {response.text}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        data = response.json()
    except json.JSONDecodeError as exc:
        print(f"[lmstudio_chat] Invalid JSON response: {exc}", file=sys.stderr)
        sys.exit(1)

    choices = data.get("choices") or []
    if not choices:
        print("[lmstudio_chat] No choices returned.", file=sys.stderr)
        sys.exit(1)

    message = choices[0].get("message", {})
    content = message.get("content")
    if not content:
        print("[lmstudio_chat] Empty content in response.", file=sys.stderr)
        sys.exit(1)

    sys.stdout.write(content)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
