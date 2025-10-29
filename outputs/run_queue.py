import sys
sys.path.append(r"d:/nas_backup/ai_binoche_conversation_origin/lumen/chatgpt-정보이론철학적분석")
from luon_rhythm_queue_v2 import main

sys.argv = [
    "luon_rhythm_queue_v2",
    "--events", r"d:/nas_backup/outputs/luon_report/luon_rhythm_events.csv",
    "--config", r"d:/nas_backup/outputs/luon_report/luon_config_tuned_kpi.yaml",
    "--outdir", r"d:/nas_backup/outputs/luon_report"
]
try:
    main()
except SystemExit:
    pass