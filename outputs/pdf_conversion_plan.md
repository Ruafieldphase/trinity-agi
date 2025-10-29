# Briefing PDF Conversion Plan

## Tools Check
- `pandoc` unavailable (command not found).
- `wkhtmltopdf` not verified; requires installation if chosen.
- Python environment available; can use `markdown` + `weasyprint`/`pdfkit` if dependencies installed.

## Recommended Approach
1. **Option A — Install Pandoc**
   - Download Pandoc for Windows.
   - Command: `pandoc agi_research_onepager.md -o agi_research_onepager.pdf --from markdown`.
   - Repeat for Ion briefs (ensure UTF-8 output handles Korean).

2. **Option B — Python + WeasyPrint**
   - Install packages: `pip install markdown weasyprint`.
   - Convert MD → HTML → PDF via small script.

3. **Option C — Manual (Word Processor)**
   - Open Markdown in VS Code/Typora → Export PDF.
   - Use for quick turnaround if CLI install not possible.

## Action Items
- Decide preferred tool.
- Script conversion for both EN/KR versions once tool installed.
- Update `research_package_manifest.csv` when PDFs generated.
