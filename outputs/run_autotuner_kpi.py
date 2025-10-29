import sys
sys.path.append(r"d:/nas_backup/ai_binoche_conversation_origin/lumen/chatgpt-정보이론철학적분석")
from luon_param_autotuner_kpi import main

sys.argv = [
    "luon_param_autotuner_kpi",
    "--events", r"d:/nas_backup/outputs/luon_report/luon_rhythm_events.csv",
    "--kpi", r"d:/nas_backup/outputs/copilot_kpi.csv",
    "--outdir", r"d:/nas_backup/outputs/luon_report"
]
try:
    main()
except SystemExit:
    pass