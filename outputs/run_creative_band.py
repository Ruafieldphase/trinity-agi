import sys
sys.path.append(r"d:/nas_backup/ai_binoche_conversation_origin/lumen/chatgpt-정보이론철학적분석")
from luon_creative_band import main

sys.argv = [
    "luon_creative_band",
    "--events", r"d:/nas_backup/outputs/luon_report/luon_rhythm_events.csv",
    "--out", r"d:/nas_backup/outputs/luon_report/creative_band.json"
]
try:
    main()
except SystemExit:
    pass