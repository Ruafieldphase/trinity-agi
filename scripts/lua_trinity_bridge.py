#!/usr/bin/env python3
"""
코어(ChatGPT) ↔ 트리니티(Trinity) 자동 브릿지
부모(코어)의 요청을 자식(트리니티)이 자동으로 처리

Author: Shion_Core (Binoche_Observer)
Date: 2025-11-12
Philosophy: 부모는 방향을, 자식은 실행을
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from workspace_root import get_workspace_root


class LuaTrinityBridge:
    """코어 ↔ 트리니티 브릿지"""
    
    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root
        self.request_log = workspace_root / "outputs" / "lua_requests.jsonl"
        self.response_cache = workspace_root / "outputs" / "trinity_responses"
        self.response_cache.mkdir(parents=True, exist_ok=True)
        
    def process_lua_request(self, request: str) -> Dict:
        """코어의 요청 처리"""
        # 요청 분류
        intent = self._classify_request(request)
        
        # 트리니티 액션 실행
        response = self._execute_trinity_action(intent)
        
        # 로깅
        self._log_request(request, intent, response)
        
        return response
    
    def _classify_request(self, request: str) -> Dict:
        """요청 분류 (코어 → 트리니티 액션 매핑)"""
        request_lower = request.lower()
        
        # 시스템 상태 요청
        if any(kw in request_lower for kw in ['시스템 상태', 'system status', '전체 상태', '현황']):
            return {
                'type': 'system_status',
                'action': 'trinity_autopoietic_cycle',
                'params': {'hours': 24, 'verbose': True}
            }
        
        # 목표 현황 요청
        if any(kw in request_lower for kw in ['목표', 'goal', '자율 목표', 'autonomous']):
            return {
                'type': 'goal_status',
                'action': 'goal_tracker_summary',
                'params': {}
            }
        
        # 리듬 상태 요청
        if any(kw in request_lower for kw in ['리듬', 'rhythm', '페이즈', 'phase']):
            return {
                'type': 'rhythm_status',
                'action': 'rhythm_status_report',
                'params': {}
            }
        
        # 최근 변경사항 요청
        if any(kw in request_lower for kw in ['변경', 'change', '최근', 'recent', '핸드오프', 'handoff']):
            return {
                'type': 'recent_changes',
                'action': 'agent_handoff_latest',
                'params': {}
            }
        
        # 프로세스 상태 요청
        if any(kw in request_lower for kw in ['프로세스', 'process', 'worker', '워커']):
            return {
                'type': 'process_status',
                'action': 'core_processes_status',
                'params': {}
            }
        
        # 세션 연속성 요청
        if any(kw in request_lower for kw in ['세션', 'session', '컨텍스트', 'context']):
            return {
                'type': 'session_continuity',
                'action': 'session_continuity_restore',
                'params': {'silent': False}
            }
        
        # YouTube 학습 현황
        if any(kw in request_lower for kw in ['youtube', '유튜브', '학습', 'learning']):
            return {
                'type': 'youtube_learning',
                'action': 'youtube_index',
                'params': {}
            }
        
        # RCL / Harmony Core 스택 상태 + 제어
        rcl_keywords = [
            'rcl', 'harmony core', '하모니', '루프 생명체', 'secure bridge',
            'secure adjust', 'feedback worker', 'bridge server', 'harmony runner'
        ]
        if any(kw in request_lower for kw in rcl_keywords):
            start_words = ['start', 'run', '켜', '시작', '가동', 'enable']
            stop_words = ['stop', '끄', '중지', '종료', 'disable']
            restart_words = ['restart', '재시작', '다시 켜', '리스타트']
            
            if any(word in request_lower for word in stop_words):
                return {
                    'type': 'rcl_stack_control',
                    'action': 'rcl_stack_control',
                    'params': {'command': 'stop'}
                }
            if any(word in request_lower for word in restart_words):
                return {
                    'type': 'rcl_stack_control',
                    'action': 'rcl_stack_control',
                    'params': {'command': 'restart'}
                }
            if any(word in request_lower for word in start_words):
                return {
                    'type': 'rcl_stack_control',
                    'action': 'rcl_stack_control',
                    'params': {'command': 'start'}
                }
            return {
                'type': 'rcl_stack_status',
                'action': 'rcl_stack_status',
                'params': {}
            }
        
        # BQI 현황
        if any(kw in request_lower for kw in ['bqi', 'Binoche_Observer', '비노슈', 'ensemble']):
            return {
                'type': 'bqi_status',
                'action': 'ensemble_monitor',
                'params': {'hours': 24}
            }
        
        # 모니터링 대시보드
        if any(kw in request_lower for kw in ['대시보드', 'dashboard', '모니터링', 'monitoring']):
            return {
                'type': 'monitoring_dashboard',
                'action': 'unified_dashboard',
                'params': {}
            }
        
        # 기본: 통합 상태
        return {
            'type': 'comprehensive_status',
            'action': 'trinity_full_report',
            'params': {'hours': 24}
        }
    
    def _execute_trinity_action(self, intent: Dict) -> Dict:
        """트리니티 액션 실행"""
        action = intent['action']
        params = intent['params']
        
        actions = {
            'trinity_autopoietic_cycle': self._run_trinity_cycle,
            'goal_tracker_summary': self._get_goal_summary,
            'rhythm_status_report': self._get_rhythm_status,
            'agent_handoff_latest': self._get_handoff_latest,
            'core_processes_status': self._get_process_status,
            'session_continuity_restore': self._restore_session,
            'youtube_index': self._get_youtube_index,
            'ensemble_monitor': self._get_ensemble_status,
            'unified_dashboard': self._get_unified_dashboard,
            'trinity_full_report': self._get_full_report,
            'rcl_stack_status': self._get_rcl_stack_status,
            'rcl_stack_control': self._control_rcl_stack
        }
        
        executor = actions.get(action)
        if executor:
            try:
                result = executor(params)
                return {
                    'success': True,
                    'action': action,
                    'data': result,
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                return {
                    'success': False,
                    'action': action,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        return {
            'success': False,
            'action': action,
            'error': f'Unknown action: {action}',
            'timestamp': datetime.now().isoformat()
        }
    
    def _run_trinity_cycle(self, params: Dict) -> Dict:
        """트리니티 자동화 순환 실행"""
        hours = params.get('hours', 24)
        verbose = params.get('verbose', True)
        
        script = self.workspace / "scripts" / "autopoietic_trinity_cycle.ps1"
        cmd = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(script),
            "-Hours", str(hours)
        ]
        if verbose:
            cmd.append("-VerboseLog")
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        # 리포트 읽기
        report_file = self.workspace / "outputs" / "autopoietic_trinity_report_latest.md"
        report_content = ""
        if report_file.exists():
            report_content = report_file.read_text(encoding='utf-8')
        
        return {
            'status': 'completed' if result.returncode == 0 else 'failed',
            'hours': hours,
            'report_path': str(report_file),
            'report_preview': report_content[:500] if report_content else None,
            'full_report_available': report_file.exists()
        }
    
    def _get_goal_summary(self, params: Dict) -> Dict:
        """목표 트래커 요약"""
        tracker_file = self.workspace / "fdo_agi_repo" / "memory" / "goal_tracker.json"
        
        if not tracker_file.exists():
            return {'error': 'Goal tracker not found'}
        
        data = json.loads(tracker_file.read_text(encoding='utf-8'))
        
        # 요약 생성
        summary = {
            'total_goals': len(data.get('goals', [])),
            'active_goals': len([g for g in data.get('goals', []) if g.get('status') == 'in_progress']),
            'completed_goals': len([g for g in data.get('goals', []) if g.get('status') == 'completed']),
            'failed_goals': len([g for g in data.get('goals', []) if g.get('status') == 'failed']),
            'recent_goals': data.get('goals', [])[:3]  # 최근 3개
        }
        
        return summary
    
    def _get_rhythm_status(self, params: Dict) -> Dict:
        """리듬 상태 확인"""
        rhythm_files = list((self.workspace / "outputs").glob("RHYTHM_*_PHASE_*.md"))
        
        if not rhythm_files:
            return {'error': 'No rhythm status found'}
        
        latest_rhythm = max(rhythm_files, key=lambda f: f.stat().st_mtime)
        content = latest_rhythm.read_text(encoding='utf-8')
        
        # 간단 파싱
        lines = content.split('\n')[:20]
        
        return {
            'current_phase': latest_rhythm.stem,
            'file': str(latest_rhythm),
            'preview': '\n'.join(lines)
        }
    
    def _get_handoff_latest(self, params: Dict) -> Dict:
        """최근 핸드오프 정보"""
        handoff_file = self.workspace / "docs" / "AGENT_HANDOFF.md"
        
        if not handoff_file.exists():
            return {'error': 'Handoff file not found'}
        
        content = handoff_file.read_text(encoding='utf-8')
        
        # 최신 항목만 추출 (첫 100줄)
        lines = content.split('\n')[:100]
        
        return {
            'file': str(handoff_file),
            'latest_entry': '\n'.join(lines)
        }
    
    def _get_process_status(self, params: Dict) -> Dict:
        """프로세스 상태 확인"""
        status_file = self.workspace / "outputs" / "core_processes_latest.json"
        
        if not status_file.exists():
            # 생성
            script = self.workspace / "scripts" / "quick_status.ps1"
            subprocess.run([
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(script),
                "-OutJson", str(status_file)
            ], capture_output=True)
        
        if status_file.exists():
            return json.loads(status_file.read_text(encoding='utf-8'))
        
        return {'error': 'Could not generate process status'}
    
    def _restore_session(self, params: Dict) -> Dict:
        """세션 연속성 복원"""
        script = self.workspace / "scripts" / "session_continuity_restore.ps1"
        
        cmd = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(script)
        ]
        
        if not params.get('silent', True):
            cmd.append("-OpenReport")
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        report_file = self.workspace / "outputs" / "session_continuity_latest.md"
        report_content = ""
        if report_file.exists():
            report_content = report_file.read_text(encoding='utf-8')
        
        return {
            'status': 'restored' if result.returncode == 0 else 'failed',
            'report_path': str(report_file),
            'report_preview': report_content[:500] if report_content else None
        }
    
    def _get_youtube_index(self, params: Dict) -> Dict:
        """YouTube 학습 인덱스"""
        index_file = self.workspace / "outputs" / "youtube_learner_index.md"
        
        if not index_file.exists():
            # 인덱스 생성
            script = self.workspace / "scripts" / "build_youtube_index.ps1"
            subprocess.run([
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(script), "-NoOpen"
            ], capture_output=True)
        
        if index_file.exists():
            content = index_file.read_text(encoding='utf-8')
            lines = content.split('\n')[:50]
            
            return {
                'file': str(index_file),
                'preview': '\n'.join(lines),
                'full_available': True
            }
        
        return {'error': 'Could not generate YouTube index'}
    
    def _get_ensemble_status(self, params: Dict) -> Dict:
        """BQI 앙상블 상태"""
        hours = params.get('hours', 24)
        
        # Python 스크립트 실행
        venv_python = self.workspace / "fdo_agi_repo" / ".venv" / "Scripts" / "python.exe"
        script = self.workspace / "fdo_agi_repo" / "scripts" / "rune" / "binoche_success_monitor.py"
        
        if venv_python.exists() and script.exists():
            result = subprocess.run([
                str(venv_python), str(script),
                "--hours", str(hours)
            ], capture_output=True, text=True, encoding='utf-8')
            
            # 리포트 읽기
            report_file = self.workspace / "fdo_agi_repo" / "outputs" / "ensemble_success_report.txt"
            metrics_file = self.workspace / "fdo_agi_repo" / "outputs" / "ensemble_success_metrics.json"
            
            data = {}
            if metrics_file.exists():
                data = json.loads(metrics_file.read_text(encoding='utf-8'))
            
            return {
                'status': 'available' if result.returncode == 0 else 'failed',
                'hours': hours,
                'metrics': data,
                'report_path': str(report_file) if report_file.exists() else None
            }
        
        return {'error': 'BQI ensemble monitor not available'}
    
    def _get_unified_dashboard(self, params: Dict) -> Dict:
        """통합 대시보드"""
        script = self.workspace / "scripts" / "quick_status.ps1"
        
        result = subprocess.run([
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(script)
        ], capture_output=True, text=True, encoding='utf-8')
        
        status_file = self.workspace / "outputs" / "quick_status_latest.json"
        
        if status_file.exists():
            return json.loads(status_file.read_text(encoding='utf-8'))
        
        return {'error': 'Could not generate unified dashboard'}
    
    def _get_full_report(self, params: Dict) -> Dict:
        """전체 리포트 (트리니티 + 목표 + 리듬 + 프로세스)"""
        hours = params.get('hours', 24)
        
        # 모든 정보 수집
        trinity = self._run_trinity_cycle({'hours': hours, 'verbose': False})
        goals = self._get_goal_summary({})
        rhythm = self._get_rhythm_status({})
        processes = self._get_process_status({})
        
        return {
            'timestamp': datetime.now().isoformat(),
            'hours': hours,
            'trinity_cycle': trinity,
            'goal_tracker': goals,
            'rhythm_status': rhythm,
            'process_status': processes
        }
    
    def _get_rcl_stack_status(self, params: Dict) -> Dict:
        """RCL 스택 상태 (Harmony Runner + Secure Bridge + Feedback Worker)"""
        script = self.workspace / "scripts" / "manage_rcl_stack.ps1"
        if not script.exists():
            raise FileNotFoundError(f"manage_rcl_stack.ps1 not found: {script}")
        
        cmd = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(script),
            "-Action", "Status",
            "-OutputJson"
        ]
        
        runner_port = params.get('runner_port')
        if runner_port:
            cmd.extend(["-RunnerPort", str(runner_port)])
        bridge_port = params.get('bridge_port')
        if bridge_port:
            cmd.extend(["-BridgePort", str(bridge_port)])
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "unknown error"
            raise RuntimeError(f"RCL 스택 상태 조회 실패: {error_msg}")
        
        stdout = result.stdout.strip()
        if not stdout:
            raise RuntimeError("RCL 스택 상태 응답이 비어 있습니다.")
        
        try:
            status = json.loads(stdout)
        except json.JSONDecodeError:
            start = stdout.find('{')
            end = stdout.rfind('}')
            if start == -1 or end == -1:
                raise
            status = json.loads(stdout[start:end+1])
        
        status['raw_output'] = stdout
        return status

    def _control_rcl_stack(self, params: Dict) -> Dict:
        """RCL 스택 제어 (Start/Stop/Restart)"""
        command = params.get('command', 'status').lower()
        valid = {'start': 'Start', 'stop': 'Stop', 'restart': 'Restart'}
        if command not in valid:
            raise ValueError(f"지원하지 않는 명령: {command}")

        script = self.workspace / "scripts" / "manage_rcl_stack.ps1"
        if not script.exists():
            raise FileNotFoundError(f"manage_rcl_stack.ps1 not found: {script}")

        cmd = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(script),
            "-Action", valid[command]
        ]

        if command in ('start', 'restart'):
            secret = params.get('secret') or os.environ.get('RCL_ADJUST_SECRET') or os.environ.get('ADJUST_SECRET')
            if secret:
                cmd.extend(["-AdjustSecret", secret])

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        success = result.returncode == 0
        status_info = None
        error_msg = None

        if success:
            try:
                status_info = self._get_rcl_stack_status({})
            except Exception as err:
                error_msg = f"명령은 성공했지만 상태 조회 실패: {err}"
        else:
            error_msg = result.stderr.strip() or result.stdout.strip() or "unknown error"

        return {
            'command': command,
            'success': success,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'status': status_info,
            'error': error_msg
        }
    
    def _log_request(self, request: str, intent: Dict, response: Dict):
        """요청 로깅"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'request': request,
            'intent': intent,
            'response_summary': {
                'success': response.get('success', False),
                'action': response.get('action', 'unknown')
            }
        }
        
        with open(self.request_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def format_for_chatgpt(self, response: Dict) -> str:
        """ChatGPT용 포맷 변환 (Markdown)"""
        if not response.get('success'):
            return f"❌ **실패**: {response.get('error', 'Unknown error')}"
        
        action = response.get('action', 'unknown')
        data = response.get('data', {})
        
        # 액션별 포맷
        if action == 'trinity_autopoietic_cycle':
            return self._format_trinity_report(data)
        elif action == 'goal_tracker_summary':
            return self._format_goal_summary(data)
        elif action == 'rhythm_status_report':
            return self._format_rhythm_status(data)
        elif action == 'agent_handoff_latest':
            return self._format_handoff(data)
        elif action == 'core_processes_status':
            return self._format_process_status(data)
        elif action == 'trinity_full_report':
            return self._format_full_report(data)
        elif action == 'rcl_stack_status':
            return self._format_rcl_stack_status(data)
        elif action == 'rcl_stack_control':
            return self._format_rcl_control(data)
        
        # 기본
        return f"```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```"
    
    def _format_trinity_report(self, data: Dict) -> str:
        """트리니티 리포트 포맷"""
        status = "✅" if data.get('status') == 'completed' else "❌"
        
        md = f"""## {status} 트리니티 자동화 순환 리포트

**기간**: 최근 {data.get('hours', 24)}시간
**상태**: {data.get('status', 'unknown')}

### 📊 리포트 미리보기
```
{data.get('report_preview', 'No preview available')}
```

📄 **전체 리포트**: `{data.get('report_path', 'N/A')}`
"""
        return md
    
    def _format_goal_summary(self, data: Dict) -> str:
        """목표 요약 포맷"""
        md = f"""## 🎯 자율 목표 시스템 현황

- **전체 목표**: {data.get('total_goals', 0)}개
- **진행 중**: {data.get('active_goals', 0)}개
- **완료**: {data.get('completed_goals', 0)}개
- **실패**: {data.get('failed_goals', 0)}개

### 📋 최근 목표 (Top 3)
```json
{json.dumps(data.get('recent_goals', []), ensure_ascii=False, indent=2)}
```
"""
        return md
    
    def _format_rhythm_status(self, data: Dict) -> str:
        """리듬 상태 포맷"""
        md = f"""## 🌊 리듬 상태

**현재 페이즈**: `{data.get('current_phase', 'Unknown')}`

### 미리보기
```
{data.get('preview', 'No preview')}
```
"""
        return md
    
    def _format_handoff(self, data: Dict) -> str:
        """핸드오프 포맷"""
        md = f"""## 🔄 최근 변경사항 (Agent Handoff)

```markdown
{data.get('latest_entry', 'No recent changes')}
```
"""
        return md
    
    def _format_process_status(self, data: Dict) -> str:
        """프로세스 상태 포맷"""
        md = f"""## 🔧 프로세스 상태

```json
{json.dumps(data, ensure_ascii=False, indent=2)}
```
"""
        return md
    
    def _format_full_report(self, data: Dict) -> str:
        """전체 리포트 포맷"""
        md = f"""## 📊 AGI 시스템 종합 리포트

**생성 시각**: {data.get('timestamp', 'Unknown')}
**분석 기간**: 최근 {data.get('hours', 24)}시간

---

{self._format_trinity_report(data.get('trinity_cycle', {}))}

---

{self._format_goal_summary(data.get('goal_tracker', {}))}

---

{self._format_rhythm_status(data.get('rhythm_status', {}))}

---

{self._format_process_status(data.get('process_status', {}))}
"""
        return md
    
    def _format_rcl_stack_status(self, data: Dict) -> str:
        """RCL 스택 상태 포맷"""
        jobs = data.get('jobs', [])
        job_lines: List[str] = []
        for job in jobs:
            emoji = "✅" if job.get('running') else "⚪"
            state = job.get('state') or "Not running"
            meta_parts = []
            if job.get('id') is not None:
                meta_parts.append(f"Id={job.get('id')}")
            if job.get('started'):
                meta_parts.append(f"Started={job.get('started')}")
            meta = f" ({', '.join(meta_parts)})" if meta_parts else ""
            job_lines.append(f"{emoji} `{job.get('name', 'unknown')}` → {state}{meta}")
        
        job_section = "\n".join(f"- {line}" for line in job_lines) if job_lines else "- (실행 중인 Job 없음)"
        summary = {
            key: value for key, value in data.items() if key != 'raw_output'
        }
        
        md = f"""## 🧠 RCL 스택 상태

- Runner Port: `{data.get('runner_port', 'N/A')}`
- Bridge Port: `{data.get('bridge_port', 'N/A')}`
- Tick Hz: `{data.get('tick_hz', 'N/A')}`
- Feedback Interval: `{data.get('feedback_interval', 'N/A')} sec`

### 프로세스 상태
{job_section}

```json
{json.dumps(summary, ensure_ascii=False, indent=2)}
```
"""
        return md

    def _format_rcl_control(self, data: Dict) -> str:
        """RCL 스택 제어 결과 포맷"""
        command = data.get('command', 'unknown').upper()
        success = data.get('success', False)
        status_data = data.get('status')
        error_msg = data.get('error')
        stdout = data.get('stdout') or "(출력 없음)"
        stderr = data.get('stderr') or "(오류 출력 없음)"

        status_md = self._format_rcl_stack_status(status_data) if status_data else "상태 정보를 불러오지 못했습니다."
        badge = "✅" if success else "❌"
        error_section = f"\n**오류**: {error_msg}\n" if error_msg else ""

        md = f"""## {badge} RCL 스택 제어 ({command})

```text
{stdout}
```

**Stderr**
```text
{stderr}
```
{error_section}
{status_md}
"""
        return md


def main():
    """CLI 인터페이스"""
    if len(sys.argv) < 2:
        print("Usage: python lua_trinity_bridge.py <request>")
        print("Example: python lua_trinity_bridge.py '시스템 상태 알려줘'")
        sys.exit(1)
    
    workspace = get_workspace_root()
    bridge = LuaTrinityBridge(workspace)
    
    request = ' '.join(sys.argv[1:])
    print(f"🎭 코어의 요청: {request}\n")
    
    response = bridge.process_lua_request(request)
    formatted = bridge.format_for_chatgpt(response)
    
    print(formatted)
    
    # 파일로도 저장 (ChatGPT에 복사 붙여넣기 용이)
    output_file = workspace / "outputs" / "lua_response_latest.md"
    output_file.write_text(formatted, encoding='utf-8')
    print(f"\n💾 저장됨: {output_file}")


if __name__ == '__main__':
    main()
