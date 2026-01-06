# Original Data Index: Usage Guide

This indexer catalogs your knowledge assets under `C:\\workspace\\original_data` and produces:

- `outputs/original_data_index.json` — full machine-readable index
- `outputs/original_data_index.md` — quick, readable table (top 200 by last modified)

## Why

- You already curated a rich set of discussions and structures in `original_data`. This tool makes them discoverable and reusable across agents and scripts.

## Run

- VS Code Tasks:
  - "Original Data: Build Index (open)" — builds the index and opens the MD
  - "Original Data: Build Index (no open)" — builds silently
  - "Original Data: Open Index (MD/JSON)" — open latest outputs

## What it captures

- Path, relative path, name, extension
- Size bytes, created/modified timestamps (UTC)
- Title (from H1 for `.md`, or filename), tags (from simple YAML front matter `tags:`)
- Optional SHA1 (use `-ComputeHash` for small files)

## Command-line (PowerShell)

You can run the script directly:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_original_data_index.ps1 -OpenMd -AllowEmpty
```

Parameters:

- `-Root` — root folder to scan (default `C:\workspace\original_data`)
- `-OutDir` — where to place outputs (default `outputs`)
- `-IncludeExt` — extensions to include
- `-MaxFiles` — safety cap (default 10000)
- `-ComputeHash` `-MaxHashMB` — compute SHA1 for small files
- `-OpenMd` / `-NoOpen` — open MD after build
- `-AllowEmpty` — if root is missing, still write an empty index

## Notes

- Text extraction is intentionally light for speed and safety. The index focuses on metadata + quick titles/tags.
- You can change `-IncludeExt` to narrow/widen coverage.
- The script is side-effect free: it only reads files and writes two outputs.

## Next steps (optional)

- Add a search CLI to filter by title/tags/date and open files.
- Wire this index into your agents (e.g., as a retrieval source for planning or guardrails).
