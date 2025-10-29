import argparse
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_GLOB = [
    ROOT / "README.md",
    ROOT / "RELEASE_NOTES.md",
    ROOT / "CHANGELOG.md",
    ROOT / "docs" / "INDEX.md",
    ROOT / "docs" / "PHASE3_EXECUTIVE_SUMMARY.md",
    ROOT / "docs" / "PHASE3_EXECUTIVE_SUMMARY_KO.md",
]

# Default excludes when scanning all markdown files under ROOT
EXCLUDE_DIRS = {
    ".git",
    ".github",  # workflows and meta files
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "outputs",  # generated artifacts (usually no .md)
    "logs",
}

LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _strip_code_blocks(text: str) -> str:
    """Remove fenced (``` ... ```) and inline (`...`) code blocks to avoid false-positive link checks.

    This prevents patterns like [persona_name](persona_name) inside code from being treated as markdown links.
    """
    # Remove fenced code blocks (including language specifiers)
    text = re.sub(r"```[\s\S]*?```", "", text)
    # Remove inline code spans
    text = re.sub(r"`[^`]*`", "", text)
    return text


def is_external_link(href: str) -> bool:
    return href.startswith("http://") or href.startswith("https://")


def normalize_path(base: Path, href: str) -> Path:
    # strip anchors and queries
    href = href.split("#", 1)[0].split("?", 1)[0]
    return (base.parent / href).resolve()


def check_file(md_path: Path):
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    text = _strip_code_blocks(text)
    broken = []
    for match in LINK_PATTERN.finditer(text):
        href = match.group(1).strip()
        if not href or is_external_link(href) or href.startswith("mailto:"):
            continue
        # ignore in-page anchors
        if href.startswith("#"):
            continue
        target = normalize_path(md_path, href)
        if not target.exists():
            broken.append((href, str(target)))
    return broken


def iter_markdown_files_all():
    for root, dirs, files in os.walk(ROOT):
        # prune excluded dirs
        pruned = []
        for d in list(dirs):
            if d in EXCLUDE_DIRS:
                pruned.append(d)
        for d in pruned:
            dirs.remove(d)
        for f in files:
            if f.lower().endswith(".md"):
                yield Path(root) / f


def main():
    parser = argparse.ArgumentParser(description="Internal Markdown link checker")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scan all Markdown files under the project root (ion-mentoring)",
    )
    args = parser.parse_args()

    any_broken = False
    scanned_count = 0
    targets = list(iter_markdown_files_all()) if args.all else DOCS_GLOB
    for md_path in targets:
        if not md_path.exists():
            print(f"[SKIP] {md_path} (not found)")
            continue
        scanned_count += 1
        broken = check_file(md_path)
        if broken:
            any_broken = True
            print(f"[BROKEN] {md_path}")
            for href, abs_path in broken:
                print(f"  - {href} -> {abs_path} [MISSING]")
        else:
            print(f"[OK] {md_path}")
    print(f"Scanned {scanned_count} Markdown files.")
    if any_broken:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
