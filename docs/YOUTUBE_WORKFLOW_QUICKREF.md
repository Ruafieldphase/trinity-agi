# YouTube Learning Workflow - Quick Reference

**Status**: ✅ Fully Operational (2025-10-31)

This workspace provides a complete automated YouTube learning pipeline with RPA, analysis, and indexing capabilities.

## 🎯 Core Workflow

```text
YouTube URL → RPA Worker → Frame Extraction → LLM Analysis → JSON/MD Output → Index Generation
```

## 📋 Quick Start (3 Steps)

### 1. Start the Infrastructure

```powershell
# Start Task Queue Server (if not running)
# VS Code Task: "Task Queue Server (Fresh)"

# Start RPA Worker
# VS Code Task: "YouTube: Start Worker (Background)"
```

### 2. Enqueue Analysis

```powershell
# VS Code Task: "YouTube: Enqueue Learn (URL, OCR off)"
# Prompts for YouTube URL, analyzes video with frame extraction
```

### 3. View Results

```powershell
# Build and open recent index with keywords
# VS Code Task: "YouTube: Build + Open Index (24h, keywords)"
```

**Expected Output:**

```markdown
# YouTube Analysis Index

## 📊 Quick Stats

- **Total Analyses:** 2
- **With Markdown:** 1 / 2
- **Avg Duration:** 1909s (~32m)
- **Length Distribution:** Short (<5m): 1 | Medium (5-30m): 0 | Long (>30m): 1
- **Top Keywords:** python (2), tutorial (2), learn (1), code (1), data (1)

## 📑 Analysis List

| Title | Video | Summary | Keywords | JSON | MD |
|-------|-------|---------|----------|------|-----|
| Python Tutorial | [link] | Comprehensive Python tutorial covering basics... | python, tutorial, learn | [json] | [md] |
```

## 🛠️ Available VS Code Tasks

### Infrastructure

- **Task Queue Server (Fresh)** - Start the task queue server on port 8091
- **YouTube: Start Worker (Background)** - Start RPA worker to process tasks

### Analysis Queue

- **YouTube: Enqueue Learn (URL, OCR off)** - Enqueue video analysis (faster)
- **YouTube: Enqueue Learn (URL, OCR on)** - Enqueue with OCR text extraction

### Results & Output

- **YouTube: Open Latest Analysis (JSON)** - View raw analysis data
- **YouTube: Open Latest Analysis (MD)** - View markdown report
- **YouTube: Generate MD (from latest JSON)** - Convert latest JSON to Markdown
- **YouTube: Open Latest Folder** - Browse all analysis files

### Index Management

- **YouTube: Build Index (open)** - Generate and open index
- **YouTube: Build Index (24h, with keywords)** - Recent analyses with keywords
- **YouTube: Build Index (grouped by date)** - Organize by analysis date
- **YouTube: Build Index (grouped, with keywords)** - Date groups + keywords
- **YouTube: Build + Open Index (24h, keywords)** ⭐ - **Recommended quick view**
- **YouTube: Open Index** - Open existing index

### Testing & Validation

- **YouTube: E2E Pipeline Test (skip enqueue)** - Test pipeline with existing data
- **YouTube: E2E Pipeline Test (full)** - Complete pipeline test including enqueue

### Analysis & Processing

- **YouTube: Enqueue Learn (URL, OCR off)** - Queue video analysis (recommended)
- **YouTube: Enqueue Learn (URL, OCR on)** - Queue with OCR (slower, more detail)
- **YouTube: Start Worker (Background)** - Start RPA worker process

### Results Access

- **YouTube: Open Latest Analysis (JSON)** - View raw analysis data
- **YouTube: Open Latest Analysis (MD)** - View formatted markdown
- **YouTube: Open Latest Analysis (ensure MD)** - Generate MD if missing, then open
- **YouTube: Open Latest Folder** - Browse all analysis files

### Markdown Generation

- **YouTube: Generate MD (from latest JSON)** - Convert latest JSON to MD and open
- **YouTube: Generate MD (latest, no open)** - Convert without opening
- **YouTube: Generate MD (from current file)** - Convert currently open JSON
- **YouTube: Generate MD (prompt path)** - Convert specific JSON file

### Index & Reporting

- **YouTube: Build Index (open)** - Generate index and open (default: 20 items)
- **YouTube: Build Index (no open)** - Generate index silently
- **YouTube: Build Index (prompt top)** - Choose how many items to include
- **YouTube: Build Index (24h, with keywords)** - Recent analyses with keyword column
- **YouTube: Build + Open Index (24h, keywords)** ⭐ - **Recommended quick view**
- **YouTube: Open Index** - Open existing index

## 💻 CLI Commands

### Quick Analysis

```powershell
# Enqueue single video (no OCR, fast)
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\enqueue_youtube_learn.ps1 `
  -Url "https://www.youtube.com/watch?v=VIDEO_ID" `
  -ClipSeconds 10 -MaxFrames 3 -FrameInterval 30
```

### Index Generation

```powershell
# Latest 20 with stats
.\scripts\build_youtube_index.ps1

# Custom filters
.\scripts\build_youtube_index.ps1 -SinceHours 24 -IncludeKeywords -Top 10 -NoOpen

# Last 7 days, top 50
.\scripts\build_youtube_index.ps1 -SinceHours 168 -Top 50
```

### MD File Generation

```powershell
# From specific JSON
.\scripts\generate_youtube_md_from_json.ps1 -JsonPath "path\to\analysis.json"

# Latest JSON, no open
.\scripts\generate_youtube_md_from_json.ps1 -NoOpen
```

## 📊 Index Features

The generated index (`outputs/youtube_learner_index.md`) includes:

- **Summary Statistics**
  - Total analyses count
  - Average video duration
  - Top 5 most frequent keywords across all analyses

- **Filterable Table**
  - Video title with YouTube link
  - Analysis timestamp
  - Keywords (optional, top 5 per video)
  - Direct links to JSON and MD files

## 🔧 Configuration

### Default Paths

- **Analysis Output**: `outputs/youtube_learner/`
- **Index Output**: `outputs/youtube_learner_index.md`
- **Task Queue Server**: `http://127.0.0.1:8091`

### Analysis Parameters

- **ClipSeconds**: Video clip length (default: 10s)
- **MaxFrames**: Maximum frames to extract (default: 3)
- **FrameInterval**: Seconds between frames (default: 30s)
- **EnableOcr**: OCR text extraction (default: false)

## 🎓 Common Use Cases

### Daily Review Workflow

```powershell
# Morning: Queue interesting videos
# VS Code Task: "YouTube: Enqueue Learn (URL, OCR off)"
# (Repeat for each video)

# Afternoon: Review results
# VS Code Task: "YouTube: Build + Open Index (24h, keywords)"
```

### Deep Analysis

```powershell
# Queue with OCR for detailed extraction
# VS Code Task: "YouTube: Enqueue Learn (URL, OCR on)"

# Generate detailed markdown
# VS Code Task: "YouTube: Generate MD (from latest JSON)"
```

### Batch Processing

```powershell
# Create custom script to enqueue multiple URLs
$urls = @(
    "https://www.youtube.com/watch?v=VIDEO1",
    "https://www.youtube.com/watch?v=VIDEO2"
)

foreach ($url in $urls) {
    .\scripts\enqueue_youtube_learn.ps1 -Url $url -ClipSeconds 10 -MaxFrames 3 -FrameInterval 30
    Start-Sleep -Seconds 2  # Rate limiting
}
```

## 📝 Output Format

### JSON Structure

```json
{
  "video_id": "dQw4w9WgXcQ",
  "title": "Video Title",
  "duration": 213,
  "analyzed_at": "2025-10-31T04:35:38.461167",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "frames": [...],
  "transcript": "...",
  "summary": "..."
}
```

### Markdown Sections

- Video metadata (title, duration, link)
- Summary
- Key points
- Transcript
- Frame analysis (if available)
- Keywords

## 🚨 Troubleshooting

### Worker Not Processing

```powershell
# Check server status
Invoke-RestMethod -Uri 'http://127.0.0.1:8091/api/health'

# Restart worker
# VS Code Task: "YouTube: Start Worker (Background)"
```

### Missing Markdown Files

```powershell
# Generate from existing JSON
# VS Code Task: "YouTube: Generate MD (from latest JSON)"
```

### Empty Index

```powershell
# Check if analyses exist
Get-ChildItem outputs/youtube_learner/*.json

# Adjust time filter
.\scripts\build_youtube_index.ps1 -SinceHours 720  # Last 30 days
```

## 📚 Documentation

- **Index Guide**: `docs/YOUTUBE_ANALYSIS_INDEX.md`
- **RPA Setup**: `PHASE_2_5_RPA_YOUTUBE_LEARNING_PLAN.md`
- **Detailed README**: `README_youtube_learner.md`

## ⚡ Performance Tips

1. **Use OCR sparingly** - Significantly slower, use only when text extraction is critical
2. **Adjust frame extraction** - Lower MaxFrames for faster processing
3. **Filter indexes by time** - Use `-SinceHours` for faster index generation on large datasets
4. **Monitor worker health** - Single worker recommended to avoid rate limiting

## 🎉 Success Metrics

- ✅ **Analysis Speed**: ~30-60 seconds per video (no OCR)
- ✅ **Index Generation**: <2 seconds for 100 items
- ✅ **Markdown Quality**: Structured, readable, with all key information
- ✅ **Automation Level**: Fully automated from URL to formatted output

---

**Last Updated**: 2025-10-31  
**Maintained By**: AGI Workspace Team  
**Status**: Production Ready ✨
