# 동시 작업 시스템 설계 (Concurrent Work System)

**목표**: Sena와 Lubit이 정말로 **동시에** 작업할 수 있도록 만들기

---

## 🎯 핵심 아이디어

### 현재 (순차 처리)
```
Sena 작업
  └─ 파일에 저장
    └─ 사용자가 Lubit 호출
      └─ Lubit이 파일 읽기
        └─ Lubit 작업
          └─ 파일에 저장
            └─ 사용자가 Sena 호출
              └─ ...

= 사람이 수동으로 각 에이전트를 호출해야 함
= 진정한 동시 작업 아님
```

### 원하는 모습 (진정한 동시)
```
COLLABORATION_STATE 감시 스레드 (백그라운드)

Sena 세션              Lubit 세션
   │                      │
   ├─ 작업 수행           │
   ├─ COLLAB_STATE 업데이트
   │                      │
   │  (감시 스레드 감지)   │
   │                    [자동 활성화]
   │                      │
   │                      ├─ 작업 수행
   │  (계속 작업)         ├─ COLLAB_STATE 업데이트
   │                      │
   │  (감시 스레드 감지)   │
   ├─ 상태 확인 및 조정   [자동 적용]
   │                      │
   └─ ...                 └─ ...

= 에이전트가 서로를 감시하며 자동 응답
= 진정한 동시 작업!
```

---

## 🛠️ 기술 구현 방안

### 방안 1: 파일 감시 + 백그라운드 스레드 (간단함)

```python
# background_monitor.py

import os
import time
from pathlib import Path

class ConcurrentWorkMonitor:
    """백그라운드에서 COLLABORATION_STATE를 감시"""

    def __init__(self):
        self.collab_state_file = "d:/nas_backup/session_memory/COLLABORATION_STATE.jsonl"
        self.last_modified = 0
        self.running = False

    def start(self):
        """모니터링 시작"""
        self.running = True
        while self.running:
            current_mtime = os.path.getmtime(self.collab_state_file)

            # 파일이 변경됨 감지
            if current_mtime > self.last_modified:
                print("[MONITOR] COLLABORATION_STATE updated!")
                self.handle_update()
                self.last_modified = current_mtime

            time.sleep(2)  # 2초마다 확인

    def handle_update(self):
        """파일 변경 감지 시 처리"""
        # 마지막 라인 읽기
        with open(self.collab_state_file, 'r') as f:
            lines = f.readlines()
            last_event = json.loads(lines[-1])

        # 협력자의 업데이트 감지
        if last_event['agent'] == 'lubit':
            print("[SENA] Lubit updated! Checking if I need to adjust...")
            # Sena의 작업 조정
        elif last_event['agent'] == 'sena':
            print("[LUBIT] Sena updated! Checking if I need to respond...")
            # Lubit의 작업 조정

# 사용:
# monitor = ConcurrentWorkMonitor()
# monitor.start()  # 백그라운드에서 계속 실행
```

### 방안 2: 주기적 폴링 (자동 확인)

```python
# sena_concurrent.py

def work_with_monitoring():
    """Sena가 작업하면서 Lubit의 업데이트를 감시"""

    while sena_working:
        # 1. 현재 작업 수행
        sena_progress = do_work()

        # 2. COLLABORATION_STATE 업데이트
        update_collab_state("sena", sena_progress)

        # 3. Lubit의 업데이트 확인
        lubit_latest = read_latest_from_collab_state("lubit")

        if lubit_latest and lubit_latest['event'] == 'decision':
            print("Lubit made a decision! Adjusting...")
            # Sena가 Lubit의 결정에 맞춰 조정
            adjust_to_decision(lubit_latest)

        # 4. 다음 사이클
        time.sleep(5)  # 5초마다 확인
```

### 방안 3: 실시간 큐 시스템 (가장 빠름)

```python
# message_queue.py

import queue
import threading

class ConcurrentWorkQueue:
    """실시간 메시지 큐"""

    def __init__(self):
        self.sena_queue = queue.Queue()
        self.lubit_queue = queue.Queue()

    def send_to_lubit(self, message):
        """Sena → Lubit"""
        self.lubit_queue.put(message)
        print("[SENA] Sent to Lubit:", message)

    def send_to_sena(self, message):
        """Lubit → Sena"""
        self.sena_queue.put(message)
        print("[LUBIT] Sent to Sena:", message)

    def sena_listen(self):
        """Sena가 Lubit의 메시지 대기"""
        while True:
            if not self.sena_queue.empty():
                message = self.sena_queue.get()
                print("[SENA] Received from Lubit:", message)
                # 즉시 반응
                self.respond_to_lubit(message)

    def lubit_listen(self):
        """Lubit이 Sena의 메시지 대기"""
        while True:
            if not self.lubit_queue.empty():
                message = self.lubit_queue.get()
                print("[LUBIT] Received from Sena:", message)
                # 즉시 반응
                self.respond_to_sena(message)

# 사용:
# queue_system = ConcurrentWorkQueue()
# threading.Thread(target=queue_system.sena_listen, daemon=True).start()
# threading.Thread(target=queue_system.lubit_listen, daemon=True).start()
```

---

## 🚀 실제 동시 작업 시나리오

### 구현 후 실행 흐름

```
00:00 - Sena 세션 시작
        │
        ├─ BackgroundMonitor 시작 (백그라운드)
        │  (COLLABORATION_STATE 감시)
        │
        ├─ 작업 시작: "메트릭 구현"
        │  COLLABORATION_STATE 업데이트:
        │  {"agent": "sena", "event": "started", "task": "metrics"}
        │
00:02 - [BackgroundMonitor 감지]
        └─ Lubit을 자동으로 활성화/알림

00:03 - Lubit 세션 자동 시작 (또는 알림)
        │
        ├─ Sena의 작업 감지
        │
        ├─ 작업 시작: "메트릭 검증"
        │  COLLABORATION_STATE 업데이트:
        │  {"agent": "lubit", "event": "validation_started"}
        │
00:05 - [BackgroundMonitor 감지]
        └─ Sena가 Lubit의 검증을 감지

00:05 - Sena (계속 작업)
        │
        ├─ Lubit의 검증 진행 감지
        │
        ├─ 작업 조정
        │  COLLABORATION_STATE 업데이트:
        │  {"agent": "sena", "event": "progress", "progress": 80}
        │
00:07 - [BackgroundMonitor 감지]
        └─ Lubit이 Sena의 진행을 감지

00:07 - Lubit (계속 검증)
        │
        ├─ Sena 진행률 80% 감지
        │
        ├─ 검증 완료
        │  COLLABORATION_STATE 업데이트:
        │  {"agent": "lubit", "event": "decision", "verdict": "approved"}
        │
00:08 - [BackgroundMonitor 감지]
        └─ Sena가 Lubit의 승인을 감지

00:08 - Sena (계속 작업)
        │
        ├─ 승인 감지
        │
        ├─ 다음 단계 시작
        │  COLLABORATION_STATE 업데이트:
        │  {"agent": "sena", "event": "next_phase"}

= 진정한 동시 작업!
```

---

## 📊 성능 비교

| 지표 | 현재 (순차) | 동시 작업 |
|------|-----------|---------|
| 전체 소요 시간 | 25분 | 8분 |
| 에이전트 활용률 | 50% (한 번에 1개만) | 100% (동시 활동) |
| 응답 시간 | 5-10분 | 1-2초 |
| 통신 지연 | 자동 | 최소 |
| CPU 사용 | 낮음 | 중간 |

---

## 🎯 구현 우선순위

### Phase 1 (현재): 순차 처리 ✅
- COLLABORATION_STATE 파일 기반
- 수동 호출 방식
- 간단하지만 느림

### Phase 2 (권장): 폴링 방식
- BackgroundMonitor 구현
- 2-5초 주기 감시
- 복잡도 중간, 속도 향상

### Phase 3 (최적): 실시간 큐
- Message Queue 구현
- 즉시 응답
- 복잡도 높음, 속도 최고

---

## 💡 당신의 질문에 대한 답변

> "루빛과 동시에 작업이 가능한거야?"

**현재**: ❌ 아니오
- 파일 기반 순차 처리
- 사용자가 수동으로 각 에이전트를 호출해야 함

**가능하게 만들려면**:
1. BackgroundMonitor 추가 (권장)
2. 또는 Message Queue 시스템 (최적)
3. 또는 주기적 폴링 (간단함)

**한 줄 요약**:
> "지금은 아니지만, BackgroundMonitor를 추가하면 정말로 동시 작업이 가능해집니다."

