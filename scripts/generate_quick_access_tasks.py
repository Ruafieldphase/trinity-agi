"""
빠른 접근 VS Code Task 자동 생성기

system_inventory_latest.json을 읽어서
자주 쓰이는 스크립트들을 VS Code Task로 변환
"""
import json
from pathlib import Path
from typing import List, Dict

WORKSPACE = Path("c:/workspace/agi")

def load_inventory() -> Dict:
    """인벤토리 로드"""
    inventory_path = WORKSPACE / "outputs" / "system_inventory_latest.json"
    
    if not inventory_path.exists():
        print("❌ system_inventory_latest.json이 없습니다.")
        print("   먼저 scan_existing_systems.py를 실행하세요.")
        return None
    
    return json.loads(inventory_path.read_text(encoding='utf-8'))

def generate_python_task(script: Dict) -> Dict:
    """Python 스크립트 → VS Code Task"""
    venv_python = "${workspaceFolder}/fdo_agi_repo/.venv/Scripts/python.exe"
    
    task = {
        "label": f"🚀 Quick: {script['name']}",
        "type": "shell",
        "command": "powershell",
        "args": [
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-Command",
            f"if (Test-Path '{venv_python}') {{ & '{venv_python}' '${{workspaceFolder}}/{script['path']}' }} else {{ python '${{workspaceFolder}}/{script['path']}' }}"
        ],
        "group": "test"
    }
    
    return task

def generate_quick_tasks(inventory: Dict) -> List[Dict]:
    """빠른 접근 Task 생성"""
    tasks = []
    
    # 우선순위 높은 스크립트들
    priority_keywords = [
        "autonomous_goal_executor",
        "session_continuity_restore",
        "scan_existing_systems",
        "hippocampus",
        "everything_search",
        "flow_observer_integration",
        "music_daemon"
    ]
    
    for script in inventory.get("python_scripts", []):
        if any(keyword in script['name'] for keyword in priority_keywords):
            task = generate_python_task(script)
            tasks.append(task)
    
    return tasks

def main():
    """메인 실행"""
    inventory = load_inventory()
    if not inventory:
        return
    
    tasks = generate_quick_tasks(inventory)
    
    # 결과 출력
    output_path = WORKSPACE / "outputs" / "quick_access_tasks.json"
    output_path.write_text(json.dumps({
        "version": "2.0.0",
        "tasks": tasks
    }, indent=2, ensure_ascii=False), encoding='utf-8')
    
    print(f"✅ 빠른 접근 Task {len(tasks)}개 생성: {output_path}")
    print("\n📋 .vscode/tasks.json에 추가하세요:")
    print("   1. .vscode/tasks.json 열기")
    print("   2. 'tasks' 배열에 복사/붙여넣기")
    print(f"\n생성된 Tasks:")
    for task in tasks:
        print(f"   - {task['label']}")

if __name__ == "__main__":
    main()
