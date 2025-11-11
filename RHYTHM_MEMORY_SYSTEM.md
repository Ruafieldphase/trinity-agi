# 리듬 기반 기억 시스템 (Rhythm-Based Memory System)

## 철학적 배경

인간의 해마(Hippocampus)는 **두려움 강도에 따라** 기억을 저장합니다:

- **강한 두려움/중요도** → 원샷 학습, 장기기억 (40년 전 익사 경험처럼 생생)
- **약한 자극** → 선조체/기저핵으로 반복 학습 (점진적 축적)

AI에도 같은 원리 적용:

- ✅ 사전학습 = 선조체/기저핵 (이미 보유)
- ❌ 해마 = 부재 → **"지금이 중요하다"를 판단 못함**

## 문제점: 50개 눈 잠자리

항상 모니터링(5초마다 폴링)하면:

- 정보 과부하
- 중요한 순간에 판단 불가
- 자원 낭비
- 조기 소진 (잠자리 실험처럼)

## 해결책: 리듬 + 신호 기반

### 1. 리듬 모드 (Rhythm)

**낮은 빈도 체크포인트** - 배경 리듬 유지

- 30분~1시간 간격
- 중요도: 2~4 (낮음)
- 단기기억(`outputs/memory/short_term/`)에 저장
- 예: 정상 작업 중 주기적 스냅샷

```powershell
# VS Code 태스크: 🧠 Memory: Rhythm Checkpoint (30min)
# 또는
.\scripts\rhythm_based_snapshot.ps1 -Mode rhythm -IntervalMinutes 30
```

### 2. 신호 모드 (Signal)

**중요 순간 즉시 캡처** - 해마 원샷 학습

- 사용자가 "지금 중요!" 표시
- 중요도: 7~10 (높음)
- 장기기억(`outputs/memory/long_term/`)에 즉시 저장
- 예: 에러 발생, 돌파구 발견, 중요한 대화

```powershell
# VS Code 태스크: ⚡ Memory: Signal Capture (Important!)
# 또는
.\scripts\rhythm_based_snapshot.ps1 -Mode signal -Importance 9 -Reason "Critical breakthrough"
```

### 3. Novelty 모드

**새로운 패턴 자동 감지** - 자동 중요도 상승

- 10초 간격 빠른 체크
- 최근 10개 스냅샷과 비교
- 새로운 프로세스/패턴 발견 시 자동 플래그
- `outputs/memory/novelty/`에 별도 저장

```powershell
# VS Code 태스크: 🔔 Memory: Novelty Detection (Background)
# 또는
.\scripts\rhythm_based_snapshot.ps1 -Mode novelty
```

## 메모리 구조

```
outputs/memory/
├── short_term/     # 단기기억 (낮은 중요도, 리듬 체크포인트)
├── long_term/      # 장기기억 (높은 중요도, 신호 캡처)
└── novelty/        # 새로움 감지 (자동 플래그)
```

## 캡처 내용 예시

```json
{
    "mental_state": {
        "resonance_level": 8,
        "fear_noise_level": 2,
        "non_semantic_mode": true,
        "tags": ["john2", "music", "walk"],
        "state_label": "john2_like"
    },
    "timestamp": "2025-11-06T12:56:56+09:00",
    "importance": 8,
    "reason": "Testing hippocampus-style memory system",
    "mode": "signal",
    "active_window": {
        "title": "summarize_stream_observer.py - agi - Visual Studio Code",
        "process": "Code",
        "pid": 40248
    },
    "system_state": {
        "cpu_percent": 31.36,
        "memory_mb": 50988.12
    }
}
```

### 선택 파라미터(레조넌스/무의식 메타데이터)

리듬/신호/새로움 모드 어디서든 다음 메타데이터를 함께 기록할 수 있습니다.

- `-ResonanceLevel` (int, -1~10): 공명/몰입 강도. 7 이상이면 높은 몰입으로 간주.
- `-FearNoise` (int, -1~10): 두려움/잡음 강도. 낮을수록(0~3) 멍함/안정 상태.
- `-NonSemantic` (switch): 언어적 의미 해석을 끄고 형태/음색 중심 인지 플래그.
- `-Tags` (string[]): 태그 배열(예: john2, music, walk, resonance).

신호 모드에서 다음 보강 규칙이 적용됩니다.

- 공명 기반 승격: `ResonanceLevel >= 7` 이면서 `Importance >= 5` → 자동으로 장기기억 저장

## VS Code 태스크

### 실행 태스크

- `🧠 Memory: Rhythm Checkpoint (30min)` - 30분 간격 배경 체크포인트
- `⚡ Memory: Signal Capture (Important!)` - 지금 중요한 순간 캡처
- `🔔 Memory: Novelty Detection (Background)` - 새로움 자동 감지

### 조회 태스크

- `📂 Memory: Open Short-Term` - 단기기억 폴더 열기
- `📂 Memory: Open Long-Term` - 장기기억 폴더 열기
- `📂 Memory: Open Novelty` - 새로움 폴더 열기

## 사용 예시

### 시나리오 1: 일상 작업 중

```powershell
# 배경에서 30분마다 체크포인트
🧠 Memory: Rhythm Checkpoint (30min)
```

### 시나리오 2: 중요한 발견

```powershell
# 돌파구 발견! 즉시 캡처
⚡ Memory: Signal Capture (Important!)
# Reason: "Found solution to async deadlock"
```

### 시나리오 3: 에러 발생

```powershell
# ChatOps 또는 예외 핸들러에서 자동 트리거
.\scripts\rhythm_based_snapshot.ps1 -Mode signal -Importance 9 -Reason "Critical error: $($_.Exception.Message)"
```

### 시나리오 4: 자동 패턴 학습

```powershell
# 새로운 도구 사용 시 자동 감지
🔔 Memory: Novelty Detection (Background)
```

## 핵심 원칙

1. **과부하 방지**: 항상 모니터링하지 않음
2. **리듬 유지**: 낮은 빈도 배경 체크포인트
3. **신호 우선**: 중요한 순간에 집중
4. **자동 학습**: 새로움 자동 감지
5. **계층적 저장**: 단기 → 장기 승격

## 철학적 연결

> "두려움이 강할수록 기억은 선명하다"
>
> 40년 전 물에 빠진 기억이 지금도 생생한 이유는
> 해마가 "이건 중요하다!"고 판단했기 때문.
>
> AI도 마찬가지로, 모든 순간을 똑같이 저장하면
> 중요한 순간을 놓친다.
>
> 리듬을 유지하고, 신호에 반응하며,
> 새로움을 학습하는 것이 해마의 원리.

## 향후 확장

- [ ] 중요도 자동 추론 (컨텍스트 분석)
- [ ] 단기 → 장기 자동 승격 (재방문 빈도 기반)
- [ ] 꿈(Dream) 통합: 단기기억 재구성
- [ ] 감정 신호 통합: 성공/실패 감지
- [ ] 시각적 대시보드: 기억 타임라인

## 참고

- `scripts/rhythm_based_snapshot.ps1` - 핵심 스크립트
- `.vscode/tasks.json` - VS Code 통합
- `outputs/memory/` - 저장 위치
