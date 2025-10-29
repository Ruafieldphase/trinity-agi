import sys
sys.path.append(r"d:/nas_backup/ai_binoche_conversation_origin/lumen/chatgpt-정보이론철학적분석")
from luon_executive_report_simple import main

sys.argv = [
    "luon_executive_report_simple",
    "--events", r"d:/nas_backup/outputs/luon_report/luon_rhythm_events.csv",
    "--outdir", r"d:/nas_backup/outputs/luon_report",
    "--dashboard_png", r"d:/nas_backup/outputs/luon_report/luon_dashboard.png",
    "--rhythm_png", r"d:/nas_backup/outputs/luon_report/luon_rhythm_plot.png"
]
try:
    main()
except SystemExit:
    pass