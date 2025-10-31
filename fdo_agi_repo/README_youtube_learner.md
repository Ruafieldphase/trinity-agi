# YouTube Learner (Phase 2.5)

Lightweight YouTube analysis pipeline with optional OCR and robust fallbacks.

## Features

- Subtitles via youtube-transcript-api (graceful skip if unavailable)
- Frames via OpenCV; video fetched by pytubefix or yt-dlp (fallback)
- Optional OCR via EasyOCR on first N frames (CPU by default)
- Keyword extraction + short summary
- Results saved to `outputs/youtube_learner/` and events to resonance ledger

## Quick start

- Ensure repo venv is active on Windows PowerShell:

```powershell
& C:\workspace\agi\.venv\Scripts\Activate.ps1
```

- Run a smoke E2E (OCR enabled, small footprint):

```powershell
# From workspace root
$env:PYTHONPATH='C:\workspace\agi\fdo_agi_repo'
python fdo_agi_repo\scripts\smoke_e2e_ocr.py
```

Or use the VS Code task: "RPA: Smoke E2E (OCR)" from the command palette.

### Queue mode (recommended for background runs)

Safe, isolated flow using a dedicated queue server on port 8092:

1. Start the server and worker, then enqueue from a URL prompt

- VS Code tasks:
  - "YouTube (8092): Start Task Queue Server" (background)
  - "YouTube (8092): Start Worker (Background)"
  - "YouTube (8092): Enqueue Learn (prompt)"
  - "YouTube (8092): Show Latest Results"

1. One-shot smoke E2E (auto-start server+worker, enqueue, open result)

```powershell
./scripts/run_smoke_e2e_youtube.ps1 -Url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Notes:

- Using 8092 avoids interference with existing RPA workers on 8091.
- The smoke script clips the video (~10s) and samples 3 frames for quick turnaround.

### CLI usage (fast smoke)

You can run the learner directly as a Python module with minimal frames and optional clipping for faster downloads:

```powershell
$env:PYTHONPATH='C:\workspace\agi;C:\workspace\agi\fdo_agi_repo'
py -3 -X utf8 -m rpa.youtube_learner --url "<YouTubeURL>" --max-frames 1 --frame-interval 30.0 --clip-seconds 20
```

Or via helper script:

```powershell
./scripts/run_youtube_learner.ps1 -Url "<YouTubeURL>" -MaxFrames 1 -FrameInterval 30.0 [-EnableOcr]
```

### Orchestrate (Windows Scheduled Task)

- Register a daily run (default 04:10):

```powershell
./scripts/register_youtube_learner_task.ps1 -Register -Time "04:10" -Url "<YouTubeURL>" -MaxFrames 1 -FrameInterval 30.0
```

Note: 일부 환경에서는 Windows 작업 스케줄러 등록에 관리자 권한이 필요합니다. PowerShell을 관리자 권한으로 실행한 뒤 `Register-ScheduledTask` 단계가 포함된 스크립트를 실행하세요.

- Unregister the task:

```powershell
./scripts/register_youtube_learner_task.ps1 -Unregister
```

- Run VS Code tasks:
  - "RPA: YouTube Learner Register (daily)"
  - "RPA: YouTube Learner Unregister"
  - "RPA: YouTube Learner Run (manual)"
  - "RPA: YouTube Learner Index (generate+open)"

## Configuration

`YouTubeLearnerConfig` parameters:

- `enable_ocr` (bool): default false
- `max_ocr_frames` (int): cap OCR frames (default 3)
- `frame_interval` (float): seconds between sampled frames
- `max_frames` (int): maximum total extracted frames
- `sample_clip_seconds` (int): download only the first N seconds via yt-dlp (0 = full)

`E2EConfig` parameters:

- `enable_auto_execution` (bool): default false, keep false for safety
- `ledger_path` (Path): defaults to `memory/resonance_ledger.jsonl`

## Notes

- pytubefix is optional; if missing, the pipeline uses yt-dlp.
- yt-dlp downloads lowest available resolution (mp4 preferred) to speed up tests; `--clip-seconds`/`sample_clip_seconds` can further reduce time, but behavior may vary by stream format.
- EasyOCR will download models on first use; CPU mode is used for compatibility.

### Troubleshooting

- If a task is created but never completes, ensure the YouTube worker is running against the same server/port as the task. Use 8092 flow to avoid contention with other workers.
- If downloads hang, try adding `--clip-seconds 10` (or `-ClipSeconds 10` in the script) and re-run.
- For OCR issues on first run, allow model downloads or pre-warm by running a small OCR job.

## Results viewing (JSON → Markdown)

After a run, artifacts are saved under `outputs/youtube_learner/` as `<videoId>_analysis.json`.
You can generate and open a readable Markdown summary side-by-side via VS Code tasks:

- "YouTube: Open Latest Analysis (ensure MD)" — opens the latest JSON and, if the matching `.md` is missing, auto-generates it and opens as well.
- "YouTube: Open Latest Analysis (MD)" — opens the most recent Markdown summary directly.
- "YouTube: Generate MD (from latest JSON)" — converts the latest JSON to Markdown and opens it.
- "YouTube: Generate MD (latest, no open)" — same as above but doesn’t open the file (CI-friendly).
- "YouTube: Generate MD (from current file)" — converts the JSON currently open in the editor.
- "YouTube: Generate MD (prompt path)" — prompts for a JSON path to convert.

CLI equivalents (optional):

```powershell
# Convert latest JSON to Markdown and open in VS Code
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\generate_youtube_md_from_json.ps1

# Convert without opening (useful in batch pipelines)
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\generate_youtube_md_from_json.ps1 -NoOpen

# Open latest JSON; if MD is missing, generate then open
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\open_latest_youtube_analysis.ps1 -GenerateMdIfMissing

# Open containing folder in Explorer (alongside opening files)
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\open_latest_youtube_analysis.ps1 -OpenFolder
```
