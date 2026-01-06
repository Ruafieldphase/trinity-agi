# YouTube Analysis Index

This workspace can generate a compact index of recent YouTube analysis outputs under `outputs/youtube_learner_index.md`.

The index includes:

- **Quick Stats Section**:
  - Total analyses count
  - Markdown generation status (how many have MD files)
  - Average duration (in seconds and minutes)
  - Length distribution (Short <5m, Medium 5-30m, Long >30m)
  - Top 5 keywords across all analyses

- **Analysis List Table**: Title, Video link, Analyzed timestamp, Summary preview (120 chars), Keywords (optional), JSON/MD links

**Summary Column**: Shows the first 120 characters of each video's analysis summary, giving you a quick preview without opening files.

## VS Code tasks

- **YouTube: Build Index (open)**
  - Builds the index from `outputs/youtube_learner/*.json` and opens it.
- **YouTube: Build Index (no open)**
  - Builds the index without opening it.
- **YouTube: Build Index (prompt top)**
  - Prompts for how many latest items to include.
- **YouTube: Build Index (24h, with keywords)**
  - Includes only analyses updated within the last 24 hours and adds a truncated keywords column.
- **YouTube: Build + Open Index (24h, keywords)** ✨
  - Combines build and open into one step for quick access to recent keyword-enriched results.
- **YouTube: Open Index**
  - Opens the index if it exists.

## CLI equivalents

```powershell
# Latest 20 items (with stats)
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_youtube_index.ps1

# Top N (e.g., 5) without opening
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_youtube_index.ps1 -Top 5 -NoOpen

# Last 24 hours, include keywords, top 10
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_youtube_index.ps1 -SinceHours 24 -IncludeKeywords -Top 10

# Grouped by date (recommended for long-term collections)
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_youtube_index.ps1 -GroupByDate -Top 50

# Grouped by date with keywords
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_youtube_index.ps1 -GroupByDate -IncludeKeywords -Top 30
```

### Date Grouping Mode

Use `-GroupByDate` to organize analyses by date (YYYY-MM-DD):

```markdown
### 📅 2025-10-31

| Title | Video | Summary | JSON | MD |
|-------|-------|---------|------|-----|
| 🔵 Short Video | [link] | ... | [json] | [md] |
| 🟡 Medium Video | [link] | ... | [json] | [md] |

### 📅 2025-10-30

| Title | Video | Summary | JSON | MD |
|-------|-------|---------|------|-----|
| 🔴 Long Course | [link] | ... | [json] | [md] |
```

**Benefits**:

- Easy to see which days you were most active
- Review your learning activity chronologically
- Better organization for collections spanning multiple days

## Notes

- **Keywords column** (when enabled) shows up to 5 keywords truncated to 80 characters.
- **Summary column** always shows the first 120 characters of the analysis summary for quick preview.
- **Quick Stats** provide at-a-glance understanding:
  - Completion rate (how many analyses have markdown files)
  - Duration distribution helps identify short tutorials vs long courses
  - Top keywords show trending topics across your analyzed videos
- Use `-Folder` to point at a different analysis folder; `-OutFile` to write the index elsewhere.

## Example Output

```markdown
## 📊 Quick Stats

- **Total Analyses:** 15
- **With Markdown:** 12 / 15
- **Avg Duration:** 1243s (~21m)
- **Length Distribution:** Short (<5m): 3 | Medium (5-30m): 8 | Long (>30m): 4
- **Top Keywords:** python (12), tutorial (8), code (7), learn (6), data (5)
```
