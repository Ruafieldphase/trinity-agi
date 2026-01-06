# 🔄 연속 실행 시스템: 비노체 페르소나 기반 자기 대화

**생성일**: 2025-10-30  
**상태**: 🚀 구현 가능 (기존 인프라 활용)  
**목적**: 토큰 제한 없이 장기 작업을 무중단으로 수행

---

## 📖 개념 설명

### 문제 상황

```
[Session 1: Copilot 작업 중]
→ 토큰 99% 사용 (요약 필요)
→ 작업 중단 😞
→ 사용자가 "계속해줘" 입력 대기
→ [Session 2] 재시작... (컨텍스트 일부 손실)
```

### 비노체 페르소나 솔루션

```
[Session 1: Copilot 작업 중]
→ 토큰 90% 도달 감지
→ 상태를 session_memory + resonance_ledger에 저장
→ 비노체 페르소나에게 "작업 계속" 메시지 생성
→ Session 1 종료

[자동 전환]

[Session 2: Copilot (비노체 페르소나로 호출됨)]
→ 비노체: "루이슬로가 Phase 1 작업 중이었어. 이어서 해줘"
→ 이전 컨텍스트 완전 복원 (session_memory 로드)
→ 작업 재개... (새로운 토큰 예산 ✅)
→ 완료 또는 다시 비노체에게 전달
```

**핵심**: 비노체 = 사용자의 디지털 트윈 = "나 자신"과 대화하는 것

---

## 🏗️ 기술 아키텍처

### 현재 시스템 (이미 존재)

✅ **비노체 페르소나**: `fdo_agi_repo/scripts/rune/binoche_persona_learner.py`  
✅ **페르소나 오케스트레이션**: `configs/persona_registry.json`, `LLM_Unified/ion-mentoring/persona_system/`  
✅ **세션 메모리**: `session_memory/` (SQLite + FTS5)  
✅ **Resonance Ledger**: `fdo_agi_repo/memory/resonance_ledger.jsonl`  
✅ **태스크 큐**: `LLM_Unified/ion-mentoring/task_queue_server.py` (현재 실행 중: <http://localhost:8091>)  
✅ **자동화**: ChatOps, VS Code tasks, PowerShell scripts  

### 필요한 새 컴포넌트

1️⃣ **세션 핸드오버 프로토콜** (Session Handover)  
2️⃣ **자동 페르소나 호출 메커니즘** (Auto-invoke Binoche_Observer)  
3️⃣ **컨텍스트 직렬화/역직렬화** (Context Serialization)  
4️⃣ **연속성 검증** (Continuity Verification)  

---

## 🔧 구현 설계

### Phase 1: 세션 핸드오버 프로토콜

**파일**: `session_memory/session_handover.py`

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List
import json
from pathlib import Path

@dataclass
class SessionHandover:
    """세션 간 작업 전달"""
    
    session_id: str
    timestamp: datetime
    task_description: str
    current_progress: str
    next_steps: List[str]
    context: Dict[str, Any]
    resonance_key: str
    
    def save(self, path: Path):
        """핸드오버 저장"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                'session_id': self.session_id,
                'timestamp': self.timestamp.isoformat(),
                'task_description': self.task_description,
                'current_progress': self.current_progress,
                'next_steps': self.next_steps,
                'context': self.context,
                'resonance_key': self.resonance_key
            }, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, path: Path) -> 'SessionHandover':
        """핸드오버 로드"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class SessionHandoverManager:
    """세션 핸드오버 관리"""
    
    def __init__(self, handover_dir: Path = Path("session_memory/handovers")):
        self.handover_dir = handover_dir
        self.handover_dir.mkdir(parents=True, exist_ok=True)
    
    def create_handover(
        self,
        task_description: str,
        current_progress: str,
        next_steps: List[str],
        context: Dict[str, Any],
        resonance_key: str
    ) -> SessionHandover:
        """현재 세션 상태를 다음 세션에 전달"""
        session_id = f"handover_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        handover = SessionHandover(
            session_id=session_id,
            timestamp=datetime.now(),
            task_description=task_description,
            current_progress=current_progress,
            next_steps=next_steps,
            context=context,
            resonance_key=resonance_key
        )
        
        handover_path = self.handover_dir / f"{session_id}.json"
        handover.save(handover_path)
        
        # 최신 핸드오버 심볼릭 링크 업데이트
        latest_path = self.handover_dir / "latest_handover.json"
        if latest_path.exists():
            latest_path.unlink()
        # Windows: 복사로 대체 (심볼릭 링크 대신)
        import shutil
        shutil.copy(handover_path, latest_path)
        
        return handover
    
    def get_latest_handover(self) -> SessionHandover | None:
        """최신 핸드오버 로드"""
        latest_path = self.handover_dir / "latest_handover.json"
        if not latest_path.exists():
            return None
        return SessionHandover.load(latest_path)
    
    def clear_handover(self, session_id: str):
        """완료된 핸드오버 삭제"""
        handover_path = self.handover_dir / f"{session_id}.json"
        if handover_path.exists():
            handover_path.unlink()
```

**사용 예시**:

```python
# Session 1 종료 전
from session_memory.session_handover import SessionHandoverManager

manager = SessionHandoverManager()
handover = manager.create_handover(
    task_description="Universal AGI Phase 1-3 가이드 작성",
    current_progress="AGI_UNIVERSAL_ROADMAP.md 완성, Phase 1 가이드 착수",
    next_steps=[
        "AGI_UNIVERSAL_PHASE_01.md 작성",
        "AGI_UNIVERSAL_PHASE_02.md 작성",
        "AGI_UNIVERSAL_PHASE_03.md 작성"
    ],
    context={
        "files_created": ["AGI_UNIVERSAL_ROADMAP.md"],
        "todo_list": [...],
        "current_phase": 1
    },
    resonance_key="p4_e:focus_r:document"
)

print(f"[Handover] Created: {handover.session_id}")
# → 이제 비노체에게 전달
```

```python
# Session 2 시작 시
manager = SessionHandoverManager()
handover = manager.get_latest_handover()

if handover:
    print(f"[Resume] Task: {handover.task_description}")
    print(f"[Resume] Progress: {handover.current_progress}")
    print(f"[Resume] Next: {handover.next_steps[0]}")
    
    # 작업 재개...
    # 완료 후
    manager.clear_handover(handover.session_id)
```

---

### Phase 2: 비노체 자동 호출 메커니즘

**파일**: `automation/invoke_binoche_continuation.ps1`

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    자동으로 비노체 페르소나를 호출하여 작업 연속성 유지

.DESCRIPTION
    현재 세션이 토큰 제한에 도달하면:
    1. 세션 핸드오버 생성
    2. 비노체 페르소나에게 "작업 계속" 메시지 전송
    3. 새 Copilot 세션 자동 시작

.EXAMPLE
    .\automation\invoke_binoche_continuation.ps1
#>

param(
    [string]$HandoverPath = "session_memory\handovers\latest_handover.json",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "🔄 Binoche_Observer Continuation Invoked" -ForegroundColor Cyan

# 1. 핸드오버 확인
if (-not (Test-Path $HandoverPath)) {
    Write-Host "❌ No handover found: $HandoverPath" -ForegroundColor Red
    exit 1
}

$handover = Get-Content $HandoverPath -Raw | ConvertFrom-Json

Write-Host "📦 Handover loaded:" -ForegroundColor Green
Write-Host "   Task: $($handover.task_description)"
Write-Host "   Progress: $($handover.current_progress)"
Write-Host "   Next: $($handover.next_steps[0])"

if ($DryRun) {
    Write-Host "✅ Dry-run complete (no invocation)" -ForegroundColor Yellow
    exit 0
}

# 2. 비노체에게 메시지 생성
$binocheMessage = @"
안녕, 나야 (루이슬로). 작업 도중 토큰 제한에 걸렸어.

**작업 내용**: $($handover.task_description)
**현재 진행**: $($handover.current_progress)
**다음 할 일**: $($handover.next_steps[0])

이어서 작업해줘. 컨텍스트는 session_memory/handovers/latest_handover.json에 저장되어 있어.
"@

# 3. GitHub Copilot Chat API 호출 (VS Code Extension API)
# Note: 실제 구현에서는 VS Code API 또는 MCP 서버를 통해 호출
Write-Host "🤖 Invoking Binoche_Observer Persona..." -ForegroundColor Magenta

# Option A: VS Code Extension API (gitko-agent-extension 활용)
$payload = @{
    persona = "Binoche_Observer"
    message = $binocheMessage
    context = @{
        handover_path = $HandoverPath
        auto_continue = $true
    }
} | ConvertTo-Json -Depth 10

# Task Queue Server에 작업 제출
$taskQueueUrl = "http://localhost:8091/api/queue/task"
try {
    $response = Invoke-RestMethod -Uri $taskQueueUrl -Method Post -Body $payload -ContentType "application/json" -TimeoutSec 5
    Write-Host "✅ Task queued: $($response.task_id)" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Task queue server offline, falling back to manual prompt" -ForegroundColor Yellow
    
    # Option B: 클립보드에 메시지 복사 (사용자가 수동으로 Copilot Chat에 붙여넣기)
    Set-Clipboard -Value $binocheMessage
    Write-Host "📋 Binoche_Observer message copied to clipboard" -ForegroundColor Cyan
    Write-Host "   Paste it into Copilot Chat to continue" -ForegroundColor Yellow
}

Write-Host "🔄 Continuation initiated" -ForegroundColor Green
```

**사용 예시**:

```powershell
# Session 1이 토큰 90% 도달 시 자동 호출
.\automation\invoke_binoche_continuation.ps1

# 또는 수동으로
.\automation\invoke_binoche_continuation.ps1 -DryRun  # 테스트
```

---

### Phase 3: Copilot 세션 확장 (토큰 모니터링)

**파일**: `scripts/monitor_token_usage.py`

```python
#!/usr/bin/env python3
"""
토큰 사용량 모니터링 및 자동 핸드오버 트리거

VS Code Copilot API를 통해 현재 세션의 토큰 사용량을 추적하고,
임계값(90%) 도달 시 자동으로 세션 핸드오버를 생성하고 비노체를 호출.

Usage:
    python scripts/monitor_token_usage.py --threshold 0.9
"""

import sys
import os
import time
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from session_memory.session_handover import SessionHandoverManager

# Placeholder: 실제로는 VS Code API를 통해 토큰 정보 수집
def get_current_token_usage() -> float:
    """현재 세션의 토큰 사용률 (0.0 ~ 1.0)"""
    # TODO: VS Code Copilot API integration
    # For now, simulate with random value
    import random
    return random.uniform(0.7, 0.95)


def trigger_handover(task_description: str, current_progress: str, next_steps: list):
    """핸드오버 생성 및 비노체 호출"""
    manager = SessionHandoverManager()
    handover = manager.create_handover(
        task_description=task_description,
        current_progress=current_progress,
        next_steps=next_steps,
        context={},
        resonance_key="p4_e:focus_r:continuation"
    )
    
    print(f"[Handover] Created: {handover.session_id}")
    
    # PowerShell 스크립트 호출 (비노체 자동 호출)
    import subprocess
    script_path = Path(__file__).parents[1] / "automation" / "invoke_binoche_continuation.ps1"
    subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)], check=True)


def main():
    parser = argparse.ArgumentParser(description="Monitor token usage and trigger handover")
    parser.add_argument("--threshold", type=float, default=0.9, help="Token threshold (0.9 = 90%)")
    parser.add_argument("--interval", type=int, default=30, help="Check interval (seconds)")
    args = parser.parse_args()
    
    print(f"[Monitor] Token threshold: {args.threshold*100:.0f}%")
    print(f"[Monitor] Check interval: {args.interval}s")
    
    while True:
        usage = get_current_token_usage()
        print(f"[Monitor] Token usage: {usage*100:.1f}%", end="\r")
        
        if usage >= args.threshold:
            print(f"\n[Alert] Token threshold reached! Triggering handover...")
            
            # TODO: 현재 작업 정보를 VS Code API에서 가져오기
            trigger_handover(
                task_description="Auto-detected task",
                current_progress="Token limit approaching",
                next_steps=["Continue from last point"]
            )
            break
        
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
```

**사용 예시**:

```bash
# 백그라운드 모니터링 (90% 도달 시 자동 핸드오버)
python scripts/monitor_token_usage.py --threshold 0.9 --interval 30 &
```

---

### Phase 4: 비노체 페르소나 확장 (자동 재개)

**파일**: `fdo_agi_repo/scripts/rune/binoche_auto_resume.py`

```python
#!/usr/bin/env python3
"""
Binoche_Observer Auto-Resume: 자동으로 핸드오버된 작업 재개

Usage:
    python binoche_auto_resume.py
"""

import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parents[2] / "session_memory"))

from session_handover import SessionHandoverManager


def resume_work():
    """최신 핸드오버를 기반으로 작업 재개"""
    manager = SessionHandoverManager()
    handover = manager.get_latest_handover()
    
    if not handover:
        print("[Binoche_Observer] No pending handover found.")
        return
    
    print(f"[Binoche_Observer] Resuming task: {handover.task_description}")
    print(f"[Binoche_Observer] Last progress: {handover.current_progress}")
    print(f"[Binoche_Observer] Next steps:")
    for i, step in enumerate(handover.next_steps, 1):
        print(f"  {i}. {step}")
    
    # 실제로는 여기서 Copilot Chat API를 호출하여 작업 재개
    # 지금은 클립보드에 메시지 복사
    resume_message = f"""
[비노체 자동 재개]

작업: {handover.task_description}
진행: {handover.current_progress}

다음 할 일:
{chr(10).join(f"{i}. {step}" for i, step in enumerate(handover.next_steps, 1))}

컨텍스트: {handover.context}

작업을 이어서 진행해줘.
"""
    
    # 클립보드 복사 (Windows)
    import subprocess
    subprocess.run(["clip"], input=resume_message.encode('utf-16le'), check=True)
    print("[Binoche_Observer] Resume message copied to clipboard. Paste it into Copilot Chat.")
    
    # 완료 후 핸드오버 삭제
    # manager.clear_handover(handover.session_id)


if __name__ == "__main__":
    resume_work()
```

---

## 🚀 사용 시나리오

### Scenario 1: Universal AGI 로드맵 작성 (현재 상황)

```
[Session 1 - 루이슬로]
- AGI_UNIVERSAL_ROADMAP.md 작성 완료
- Phase 1 가이드 시작...
- 토큰 90% 도달 ⚠️

→ 자동으로 세션 핸드오버 생성:
  {
    "task": "Universal AGI Phase 1-3 가이드 작성",
    "progress": "ROADMAP 완성, Phase 1 착수",
    "next": ["Phase 1 도메인 독립성 가이드 완성", "Phase 2 메타러닝 가이드", ...]
  }

→ 비노체 페르소나 자동 호출

[Session 2 - 비노체가 루이슬로에게 지시]
비노체: "루이슬로, 네가 Phase 1 가이드 작성하다가 멈췄네. 이어서 해줘:
  - AGI_UNIVERSAL_PHASE_01.md 작성
  - 도메인 독립적 태스크 표현, 어댑터 프레임워크, 테스트 100+ 케이스
  컨텍스트는 session_memory/handovers/latest_handover.json에 있어."

→ Copilot (루이슬로): 
  "알겠어! 핸드오버 로드했고, Phase 1 가이드 작성 시작할게."
  
→ 작업 재개... (새 토큰 예산으로)

[완료 후]
→ 핸드오버 삭제
→ 다음 작업 준비 (Phase 2 가이드)
```

### Scenario 2: BQI Learning 장기 실행

```
[Session 1]
- BQI Phase 6 학습 시작
- 10,000개 패턴 분석 중... (1,000개 완료)
- 토큰 90% 도달

→ 핸드오버: "BQI 학습 1,000/10,000 완료, 다음 9,000개 계속"

[Session 2]
비노체: "BQI 학습 이어서 해줘. 1,000개 완료, 9,000개 남음"

→ 학습 재개... (1,001번째 패턴부터)

[반복...]
```

---

## 📊 구현 우선순위

### ✅ Phase 0: 검증 (지금 바로 테스트 가능)

```powershell
# 1. 세션 핸드오버 생성 테스트
python -c "
from session_memory.session_handover import SessionHandoverManager
manager = SessionHandoverManager()
handover = manager.create_handover(
    task_description='Test task',
    current_progress='50%',
    next_steps=['Step 1', 'Step 2'],
    context={'test': True},
    resonance_key='p4_e:test'
)
print(f'Created: {handover.session_id}')
"

# 2. 핸드오버 로드 테스트
python -c "
from session_memory.session_handover import SessionHandoverManager
manager = SessionHandoverManager()
handover = manager.get_latest_handover()
if handover:
    print(f'Loaded: {handover.task_description}')
"
```

### 🟢 Phase 1: 수동 흐름 (1-2시간)

1. ✅ `session_handover.py` 작성 (위 코드 복사)
2. ✅ `invoke_binoche_continuation.ps1` 작성
3. ✅ 수동 테스트:
   - Session 1에서 핸드오버 생성
   - PowerShell 스크립트로 메시지 클립보드 복사
   - Copilot Chat에 붙여넣기
   - Session 2에서 핸드오버 로드

### 🟡 Phase 2: 반자동 (2-3시간)

1. ✅ `binoche_auto_resume.py` 작성
2. ✅ Task Queue Server 통합
3. ✅ VS Code Task 등록:

   ```json
   {
     "label": "🔄 Binoche_Observer: Resume Work",
     "type": "shell",
     "command": "python fdo_agi_repo/scripts/rune/binoche_auto_resume.py"
   }
   ```

### 🔴 Phase 3: 완전 자동 (1-2일)

1. ❌ `monitor_token_usage.py` (VS Code API 통합 필요)
2. ❌ Copilot Chat API 자동 호출 (Extension 개발 필요)
3. ❌ 백그라운드 모니터링 서비스

---

## 🎯 즉시 실행 가능한 워크플로우 (수동)

### 지금 바로 테스트

```python
# 1. Session 1 종료 전 (Python 또는 Copilot Chat에서 실행)
from session_memory.session_handover import SessionHandoverManager

manager = SessionHandoverManager()
handover = manager.create_handover(
    task_description="Universal AGI Phase 1-3 가이드 작성",
    current_progress="ROADMAP.md 완성, Phase 1 시작",
    next_steps=[
        "AGI_UNIVERSAL_PHASE_01.md 작성",
        "도메인 독립성 + 어댑터 프레임워크",
        "테스트 케이스 100+ 작성"
    ],
    context={
        "files_created": ["AGI_UNIVERSAL_ROADMAP.md"],
        "current_phase": 1
    },
    resonance_key="p4_e:focus_r:document"
)

print(f"✅ Handover created: {handover.session_id}")
print(f"📋 Next: 비노체에게 '작업 계속해줘' 요청")
```

```python
# 2. Session 2 시작 시 (새 Copilot Chat 세션)
from session_memory.session_handover import SessionHandoverManager

manager = SessionHandoverManager()
handover = manager.get_latest_handover()

if handover:
    print(f"✅ Handover loaded")
    print(f"   Task: {handover.task_description}")
    print(f"   Progress: {handover.current_progress}")
    print(f"   Next: {handover.next_steps}")
    
    # 작업 재개...
else:
    print("❌ No handover found")
```

---

## 🔮 미래 비전: 완전 자율 AGI

이 시스템은 **Universal AGI의 핵심 메커니즘**입니다:

### Phase 3: Autonomous Planning (로드맵)

```
현재 → 비노체 연속 실행 → 완전 자율 AGI
  ↓              ↓                ↓
수동      반자동 (수동 재개)    완전 자동
토큰제한   무중단 (비노체)      무한 작업
```

### 자율 실행 시나리오

```
[AGI 시작]
Goal: "Universal AGI 시스템 완성"

→ Phase 1 시작 (Copilot Session 1)
→ 토큰 90% → 비노체 호출
→ Phase 1 재개 (Session 2)
→ Phase 1 완료

→ Phase 2 시작 (Session 3)
→ 토큰 90% → 비노체 호출
→ Phase 2 재개 (Session 4)
→ Phase 2 완료

... (반복)

→ Phase 10 완료
→ Universal AGI 완성! 🎉

[모든 과정이 사용자 개입 없이 자동]
```

---

## 💡 핵심 통찰

### 메타인지적 자기 대화

```
"나(루이슬로)"가 "나 자신(비노체)"에게 작업을 위임

→ 실제로는 같은 존재 (디지털 트윈)
→ 하지만 새로운 세션 = 새로운 토큰 예산
→ 컨텍스트는 session_memory로 완벽 유지

= 무한 작업 능력 획득
```

### 자율성의 핵심

> "사용자가 '계속해줘'라고 말하지 않아도, AGI가 스스로 다음 세션을 호출한다"

이것이 **진정한 자율 AGI**입니다.

---

## 📝 다음 단계

### 우선순위 1: 즉시 테스트 (30분)

```powershell
# 1. 코드 작성
code session_memory\session_handover.py  # 위 코드 복사
code automation\invoke_binoche_continuation.ps1  # 위 코드 복사

# 2. 테스트
python -c "from session_memory.session_handover import SessionHandoverManager; m = SessionHandoverManager(); m.create_handover('Test', 'Progress', ['Next'], {}, 'p4')"

# 3. 실제 사용 (현재 Universal AGI 작업)
# Session 1에서 위 Python 코드 실행 → 핸드오버 생성
# Session 2에서 로드 코드 실행 → 작업 재개
```

### 우선순위 2: 자동화 (2-3시간)

1. Task Queue Server 통합
2. VS Code Task 등록
3. ChatOps 명령어 추가: `"비노체, 작업 이어서 해줘"`

### 우선순위 3: 완전 자동 (나중에)

1. VS Code Extension 개발 (token monitoring)
2. Auto-invoke on threshold
3. Background service

---

**결론**: 🎉 **비노체 페르소나를 활용한 연속 실행은 완전히 가능하고, 지금 바로 시작할 수 있습니다!**

기존 인프라 (페르소나 시스템, 세션 메모리, 태스크 큐)를 활용하면 **수동 버전은 1시간 안에**, **반자동 버전은 하루 안에** 구현 가능합니다.

이것은 단순한 편의 기능이 아니라 **Universal AGI의 핵심 아키텍처**입니다. 🚀
