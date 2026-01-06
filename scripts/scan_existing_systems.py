"""
AGI 시스템 인벤토리 스캐너

이미 만들어진 기능들을 자동으로 발견하고 문서화합니다.
- Python 스크립트 분석
- VS Code Task 분석
- PowerShell 스크립트 분석
- 빠른 접근 치트시트 생성
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import re

WORKSPACE = Path("c:/workspace/agi")

class SystemInventory:
    """기존 시스템 인벤토리"""
    
    def __init__(self):
        self.python_scripts: List[Dict] = []
        self.ps_scripts: List[Dict] = []
        self.vscode_tasks: List[Dict] = []
        self.utilities: List[Dict] = []
        
    def scan_all(self):
        """모든 시스템 스캔"""
        print("🔍 AGI 시스템 인벤토리 스캔 시작...")
        
        self.scan_python_scripts()
        self.scan_powershell_scripts()
        self.scan_vscode_tasks()
        self.scan_utilities()
        
        return self
    
    def scan_python_scripts(self):
        """Python 스크립트 스캔"""
        scripts_dir = WORKSPACE / "scripts"
        fdo_scripts = WORKSPACE / "fdo_agi_repo" / "scripts"
        
        for base_dir in [scripts_dir, fdo_scripts]:
            if not base_dir.exists():
                continue
                
            for py_file in base_dir.rglob("*.py"):
                # __pycache__, .venv 제외
                if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                    continue
                
                info = self._analyze_python_file(py_file)
                if info:
                    self.python_scripts.append(info)
        
        print(f"  ✅ Python 스크립트: {len(self.python_scripts)}개")
    
    def scan_powershell_scripts(self):
        """PowerShell 스크립트 스캔"""
        scripts_dir = WORKSPACE / "scripts"
        
        if scripts_dir.exists():
            for ps_file in scripts_dir.rglob("*.ps1"):
                info = self._analyze_ps_file(ps_file)
                if info:
                    self.ps_scripts.append(info)
        
        print(f"  ✅ PowerShell 스크립트: {len(self.ps_scripts)}개")
    
    def scan_vscode_tasks(self):
        """VS Code Task 스캔"""
        tasks_file = WORKSPACE / ".vscode" / "tasks.json"
        
        if tasks_file.exists():
            try:
                # JSON with Comments 파싱
                content = tasks_file.read_text(encoding='utf-8')
                # 간단한 주석 제거
                content = re.sub(r'//.*', '', content)
                content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
                
                tasks_data = json.loads(content)
                
                for task in tasks_data.get("tasks", []):
                    self.vscode_tasks.append({
                        "label": task.get("label", ""),
                        "type": task.get("type", ""),
                        "command": task.get("command", ""),
                        "group": task.get("group", ""),
                        "is_background": task.get("isBackground", False)
                    })
                
                print(f"  ✅ VS Code Tasks: {len(self.vscode_tasks)}개")
            except Exception as e:
                print(f"  ⚠️ tasks.json 파싱 실패: {e}")
    
    def scan_utilities(self):
        """유틸리티 모듈 스캔"""
        utils_dir = WORKSPACE / "fdo_agi_repo" / "utils"
        
        if utils_dir.exists():
            for py_file in utils_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                
                info = self._analyze_python_file(py_file, is_util=True)
                if info:
                    self.utilities.append(info)
        
        print(f"  ✅ 유틸리티 모듈: {len(self.utilities)}개")
    
    def _analyze_python_file(self, path: Path, is_util=False) -> Dict[str, Any]:
        """Python 파일 분석"""
        try:
            content = path.read_text(encoding='utf-8')
            
            # Docstring 추출
            docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
            docstring = docstring_match.group(1).strip() if docstring_match else ""
            
            # 주요 함수/클래스 추출
            functions = re.findall(r'^def\s+(\w+)\s*\(', content, re.MULTILINE)
            classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
            
            # argparse 사용 여부
            has_cli = "--" in content or "argparse" in content
            
            return {
                "name": path.stem,
                "path": str(path.relative_to(WORKSPACE)),
                "docstring": docstring[:200] if docstring else "",
                "functions": functions[:5],  # 처음 5개만
                "classes": classes,
                "has_cli": has_cli,
                "is_utility": is_util,
                "size": path.stat().st_size,
                "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat()
            }
        except Exception as e:
            return None
    
    def _analyze_ps_file(self, path: Path) -> Dict[str, Any]:
        """PowerShell 파일 분석"""
        try:
            content = path.read_text(encoding='utf-8')
            
            # Comment-based help 추출
            help_match = re.search(r'<#(.*?)#>', content, re.DOTALL)
            help_text = help_match.group(1).strip() if help_match else ""
            
            # 함수 추출
            functions = re.findall(r'function\s+(\w+[-\w]*)', content)
            
            # 파라미터 추출
            params = re.findall(r'\[Parameter.*?\]\s*\$(\w+)', content)
            
            return {
                "name": path.stem,
                "path": str(path.relative_to(WORKSPACE)),
                "help": help_text[:200] if help_text else "",
                "functions": functions,
                "params": params[:5],
                "size": path.stat().st_size,
                "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat()
            }
        except Exception as e:
            return None
    
    def generate_cheatsheet(self) -> str:
        """빠른 접근 치트시트 생성"""
        md = ["# AGI 시스템 빠른 접근 가이드\n"]
        md.append(f"*생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
        
        # 카테고리별 정리
        categories = {
            "🎯 자율 목표": ["autonomous", "goal", "execute"],
            "🔄 세션 관리": ["session", "continuity", "restore"],
            "🎵 음악/리듬": ["music", "rhythm", "daemon"],
            "🌊 Flow/ADHD": ["flow", "adhd", "observer"],
            "📊 모니터링": ["monitor", "dashboard", "health"],
            "🎓 학습": ["learn", "youtube", "bqi"],
            "💬 ChatOps": ["chatops", "bot"],
            "🔍 검색": ["search", "everything", "hippocampus"],
        }
        
        for category, keywords in categories.items():
            md.append(f"\n## {category}\n")
            
            # Python 스크립트
            matches = [s for s in self.python_scripts 
                      if any(k in s['name'].lower() for k in keywords)]
            if matches:
                md.append("### Python 스크립트\n")
                for script in matches[:3]:  # 상위 3개
                    md.append(f"- **{script['name']}**")
                    if script['docstring']:
                        md.append(f"  - {script['docstring'].split(chr(10))[0]}")
                    if script['has_cli']:
                        md.append(f"  - CLI: `python {script['path']}`")
                    md.append("")
            
            # VS Code Tasks
            task_matches = [t for t in self.vscode_tasks
                           if any(k in t['label'].lower() for k in keywords)]
            if task_matches:
                md.append("### VS Code Tasks\n")
                for task in task_matches[:3]:
                    md.append(f"- **{task['label']}**")
                    if task['is_background']:
                        md.append("  - 🔄 Background")
                    md.append("")
        
        # 유틸리티 섹션
        if self.utilities:
            md.append("\n## 🛠️ 유틸리티 모듈\n")
            for util in self.utilities:
                md.append(f"### {util['name']}\n")
                if util['docstring']:
                    md.append(f"{util['docstring']}\n")
                if util['classes']:
                    md.append(f"**클래스**: {', '.join(util['classes'])}\n")
                if util['functions']:
                    md.append(f"**함수**: {', '.join(util['functions'][:3])}...\n")
                md.append(f"```python")
                md.append(f"from fdo_agi_repo.utils.{util['name']} import ...")
                md.append(f"```\n")
        
        return "\n".join(md)
    
    def generate_json_report(self) -> Dict:
        """JSON 리포트 생성"""
        return {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "python_scripts": len(self.python_scripts),
                "powershell_scripts": len(self.ps_scripts),
                "vscode_tasks": len(self.vscode_tasks),
                "utilities": len(self.utilities)
            },
            "python_scripts": self.python_scripts,
            "powershell_scripts": self.ps_scripts,
            "vscode_tasks": self.vscode_tasks,
            "utilities": self.utilities
        }


def main():
    """메인 실행"""
    inventory = SystemInventory()
    inventory.scan_all()
    
    # 치트시트 생성
    cheatsheet = inventory.generate_cheatsheet()
    cheatsheet_path = WORKSPACE / "outputs" / "system_inventory_cheatsheet.md"
    cheatsheet_path.parent.mkdir(exist_ok=True)
    cheatsheet_path.write_text(cheatsheet, encoding='utf-8')
    print(f"\n✅ 치트시트 생성: {cheatsheet_path}")
    
    # JSON 리포트
    report = inventory.generate_json_report()
    report_path = WORKSPACE / "outputs" / "system_inventory_latest.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"✅ JSON 리포트: {report_path}")
    
    print(f"\n🎉 스캔 완료!")
    print(f"   - Python: {len(inventory.python_scripts)}")
    print(f"   - PowerShell: {len(inventory.ps_scripts)}")
    print(f"   - Tasks: {len(inventory.vscode_tasks)}")
    print(f"   - Utils: {len(inventory.utilities)}")


if __name__ == "__main__":
    main()
