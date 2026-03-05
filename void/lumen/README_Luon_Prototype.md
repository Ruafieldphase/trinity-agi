# Luon Rhythm Visualizer — Prototype v1

This bundle contains:
- `luon_rhythm_visualizer.py` — parse JSONL logs, compute rhythm stability R(t), output CSV + PNG + summary.
- This README with quick start.

## Quick Start (Windows)

1) Place this script somewhere accessible, e.g. `D:\tools\luon\`
2) Open a terminal (PowerShell) and run:

```powershell
python D:\tools\luon\luon_rhythm_visualizer.py `
  --roots "D:\nas_backup\ai_binoche_conversation_origin\cladeCLI-sena" `
          "D:\nas_backup\ai_binoche_conversation_origin\lubit" `
          "D:\nas_backup\ai_binoche_conversation_origin\gemini-sian" `
  --outdir "D:\nas_backup\ai_binoche_conversation_origin\luon"
```

Outputs:
- `luon_rhythm_events.csv`
- `luon_rhythm_plot.png`
- `luon_rhythm_summary.md`

Notes:
- No internet is required. Timestamps should be ISO8601. If missing tokens, script approximates via content length.
- You can add more `--roots` folders anytime.
