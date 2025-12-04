#!/usr/bin/env python3
"""Markdown → PDF converter using fpdf2 with Unicode font."""
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

from fpdf import FPDF

FONT_PATHS = [
    Path("C:/Windows/Fonts/seguisym.ttf"),
    Path("C:/Windows/Fonts/malgun.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("C:/Windows/Fonts/arialuni.ttf"),
]


def find_font() -> Path:
    for path in FONT_PATHS:
        if path.exists():
            return path
    raise SystemExit("No suitable TrueType font found. Update FONT_PATHS in scripts/convert_md_to_pdf.py")


def sanitize(text: str) -> str:
    return text.replace('\ufeff', '')


def convert(md_path: Path, pdf_path: Path) -> None:
    text = sanitize(md_path.read_text(encoding="utf-8"))
    font_path = find_font()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font("Fallback", style="", fname=str(font_path))
    pdf.set_font("Fallback", size=12)

    for paragraph in text.splitlines():
        if not paragraph:
            pdf.ln(6)
            continue
        wrapped_lines = textwrap.wrap(paragraph, width=60, break_long_words=True, break_on_hyphens=True)
        for line in wrapped_lines:
            if not line.strip():
                pdf.ln(6)
            else:
                try:
                    pdf.multi_cell(0, 6, line)
                except Exception:
                    pdf.multi_cell(0, 6, ''.join(ch if ord(ch) < 65535 else '?' for ch in line))
    pdf.output(str(pdf_path))


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Markdown to PDF (plain text)")
    parser.add_argument("input", help="Markdown file path")
    parser.add_argument("output", help="Output PDF path")
    args = parser.parse_args()

    md_path = Path(args.input)
    if not md_path.exists():
        raise SystemExit(f"Input not found: {md_path}")
    pdf_path = Path(args.output)
    convert(md_path, pdf_path)

if __name__ == "__main__":
    main()
