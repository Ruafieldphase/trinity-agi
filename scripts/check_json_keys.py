import json
import os
from pathlib import Path

settings_path = Path(os.environ['APPDATA']) / 'Code' / 'User' / 'settings.json'

with open(settings_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"총 최상위 키 개수: {len(data)}")

# terminal.integrated.shellIntegration.commandHistory 섹션 확인
cmd_history_key = "terminal.integrated.shellIntegration.commandHistory"
if cmd_history_key in data:
    cmd_history = data[cmd_history_key]
    print(f"\n{cmd_history_key} 항목 개수: {len(cmd_history)}")
    
    check_keys = [k for k in cmd_history.keys() if 'check_monitoring_status' in k]
    print(f"check_monitoring_status 포함 키: {len(check_keys)}개\n")
    
    for k in check_keys:
        print(f"  - {k[:120]}")
else:
    print(f"\n❌ {cmd_history_key} 키 없음")
