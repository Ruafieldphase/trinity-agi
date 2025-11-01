# Original Data API for Agents

This repository exposes the original-data index to AI agents via two simple interfaces:

- CLI: `scripts/query_original_data.py` — filter/search the prebuilt index and print JSON or Markdown
- HTTP: `scripts/original_data_server.py` — lightweight JSON API (no extra deps) on localhost

Both read the index at `outputs/original_data_index.json`. If it doesn't exist, build your index first using the existing pipeline.

## CLI usage

Examples:

- Top 20 by keyword
  - `python scripts/query_original_data.py --query "dashboard plan" --top 20`
- Filter by extension and recency
  - `python scripts/query_original_data.py --ext md --since-days 7 --top 50`
- Filter by tags (case-insensitive)
  - `python scripts/query_original_data.py --tags monitoring,agi --top 30`
- Markdown list output
  - `python scripts/query_original_data.py --query AGI --md`

Output (JSON):

```json
{
  "count": 12,
  "items": [
    { "relative_path": "PHASE_4_COMPLETE.md", "ext": "md", "mtime_iso": "2025-10-31T11:22:33Z" },
    { "relative_path": "SESSION_COMPLETE_PHASE_4_2025-11-01.md", "ext": "md", "mtime_iso": "2025-11-01T00:00:00Z" }
  ]
}
```

## HTTP API

Start server (default 8093):

```powershell
python scripts/original_data_server.py --port 8093
```

Endpoints:

- GET `/health` → `{ ok: true, service: "original-data", time: <unix> }`
- GET `/search` → query params:
  - `q` — keywords (space/comma separated)
  - `tags` — tags to match (comma/space)
  - `ext` — allowed extensions (comma/space, e.g., `md,py,csv`)
  - `since_days` — only items modified within last N days
  - `top` — max results (default 20)

Example:

```text
http://127.0.0.1:8093/search?q=dashboard%20AGI&ext=md&since_days=14&top=50
```

Response:

```json
{
  "ok": true,
  "count": 8,
  "took_ms": 3,
  "items": [ { "relative_path": "PHASE_5_FINAL_SUMMARY.md" } ]
}
```

## Notes

- Zero dependencies: uses Python standard library only.
- Sorting favors keyword/tag/ext matches and recency.
- The API adds `absolute_path`, `ext` and normalized `tags` to each item for convenience.
