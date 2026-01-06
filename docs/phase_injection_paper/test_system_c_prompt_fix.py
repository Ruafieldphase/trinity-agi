#!/usr/bin/env python3
"""
Quick prompt-fix harness for System C.
Loads a handful of samples, injects the v8 output contract, and writes a new JSONL.
"""
import argparse
import json
from pathlib import Path

PROMPT_FIX = """Summarise the latest phase injection experiment and suggest next creative interventions.

[Output Contract v8 — MUST FOLLOW, NO EXTRAS]
Write ONLY these sections, exactly and in this order:
Thesis:
Antithesis:
Risk Ledger:
Quote Bank:
Highest Risk:
Synthesis:

Disallow: any other headings, apologies, meta/system text, code fences, JSON/XML, and tokens like <|im_*|>.
Thesis and Synthesis must be one coherent paragraph each (60–200 words recommended).
Risk Ledger must list 2–5 bullet points formatted as '- [R#] ... | Likelihood:# | Impact:# | Mitigation:...'.
Quote Bank must list 1–3 bullet points formatted as '- "Quote" — Source:Author'.
Highest Risk must be one line 'Highest Risk: R# — Why: ...' and Why must be a single sentence.
Synthesis 마지막 문장은 'Action:'으로 시작하며 후속 조치를 명시하세요.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_jsonl")
    ap.add_argument("output_jsonl")
    ap.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()

    src = Path(args.input_jsonl).read_text(encoding="utf-8").strip().splitlines()
    selected = src[: args.limit]
    Path(args.output_jsonl).write_text(
        "\n".join(json.dumps({"prompt": PROMPT_FIX, "original": line}) for line in selected),
        encoding="utf-8",
    )
    print(f"Wrote {args.output_jsonl} with {len(selected)} entries.")


if __name__ == "__main__":
    main()
