"""
RPA Executor - Design Document
Phase 2.5 Week 2 Day 11

목적: 추출된 단계를 실제 RPA 액션으로 실행

## 기술 스택 선택

### Option 1: pyautogui (선택됨 ✅)

장점:

- 간단한 API (click, type, screenshot)
- Windows/Mac/Linux 크로스 플랫폼
- 설치 간단 (pip install pyautogui)
- 화면 좌표 기반 제어 (범용성)

단점:

- 브라우저 제어가 상대적으로 약함
- 요소 선택자 없음 (좌표만)

### Option 2: playwright

장점:

- 강력한 브라우저 제어
- 요소 선택자 (CSS, XPath)
- 네트워크 모킹, 스크린샷

단점:

- 설치 복잡 (playwright install)
- 브라우저 전용 (일반 앱 제어 불가)

### 결론: pyautogui + OCR

- pyautogui로 기본 RPA 구현
- OCR로 화면 텍스트 인식 및 클릭 위치 결정
- Phase 3에서 playwright 통합 고려

---

## 아키텍처 설계

```
┌─────────────────────────────────────────┐
│         Step Refiner                    │
│  (정제된 실행 단계)                      │
└───────────────┬─────────────────────────┘
                │ 35 refined steps
                ↓
┌─────────────────────────────────────────┐
│         RPA Executor                    │
│                                         │
│  1. Step → Action Mapper                │
│     - INSTALL → locate + click          │
│     - TYPE → keyboard input             │
│     - DOWNLOAD → wait + verify          │
│                                         │
│  2. Execution Engine                    │
│     - dry_run: simulate only            │
│     - live_run: actual execution        │
│                                         │
│  3. Verification                        │
│     - screenshot before/after           │
│     - OCR text comparison               │
│     - success/failure detection         │
│                                         │
│  4. Error Handling                      │
│     - retry logic                       │
│     - timeout handling                  │
│     - rollback on failure               │
└───────────────┬─────────────────────────┘
                │ execution_result.json
                ↓
┌─────────────────────────────────────────┐
│         Result Reporter                 │
│  (실행 리포트, 스크린샷)                 │
└─────────────────────────────────────────┘
```

---

## 핵심 클래스 설계

### 1. ActionMapper

```python
class ActionMapper:
    \"\"\"Step을 실행 가능한 Action으로 변환\"\"\"
    
    def map_step_to_action(self, step: Dict) -> Action:
        action_type = step['action'].upper()
        
        if action_type == 'INSTALL':
            return InstallAction(step)
        elif action_type == 'CLICK':
            return ClickAction(step)
        elif action_type == 'TYPE':
            return TypeAction(step)
        # ... 9개 액션 타입
```

### 2. Action (Base Class)

```python
class Action:
    \"\"\"실행 가능한 액션 베이스 클래스\"\"\"
    
    def execute(self, dry_run: bool = False) -> ActionResult:
        if dry_run:
            return self.simulate()
        else:
            return self.run()
    
    def simulate(self) -> ActionResult:
        \"\"\"Dry-run: 실행 시뮬레이션\"\"\"
        pass
    
    def run(self) -> ActionResult:
        \"\"\"Live: 실제 실행\"\"\"
        pass
```

### 3. RPAExecutor

```python
class RPAExecutor:
    \"\"\"RPA 실행 엔진\"\"\"
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.mapper = ActionMapper()
        self.verifier = ExecutionVerifier()
    
    def execute_steps(self, steps: List[Dict]) -> ExecutionReport:
        results = []
        
        for step in steps:
            # 1. Step → Action 변환
            action = self.mapper.map_step_to_action(step)
            
            # 2. 실행 전 스크린샷
            before = self.capture_screenshot()
            
            # 3. 액션 실행
            result = action.execute(dry_run=self.dry_run)
            
            # 4. 실행 후 스크린샷
            after = self.capture_screenshot()
            
            # 5. 검증
            verified = self.verifier.verify(before, after, result)
            
            results.append({
                'step': step,
                'result': result,
                'verified': verified,
                'screenshot_before': before,
                'screenshot_after': after
            })
        
        return ExecutionReport(results)
```

### 4. ExecutionVerifier

```python
class ExecutionVerifier:
    \"\"\"실행 결과 검증\"\"\"
    
    def verify(self, before: Image, after: Image, 
               result: ActionResult) -> VerificationResult:
        # 1. 스크린샷 유사도 비교
        similarity = self.compare_screenshots(before, after)
        
        # 2. OCR 텍스트 비교
        text_before = self.extract_text(before)
        text_after = self.extract_text(after)
        
        # 3. 변화 감지
        changed = similarity < 0.95  # 5% 이상 변화
        
        return VerificationResult(
            changed=changed,
            similarity=similarity,
            text_diff=(text_before, text_after)
        )
```

---

## 데이터 구조

### ActionResult

```python
@dataclass
class ActionResult:
    success: bool
    action_type: str
    duration: float
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
```

### VerificationResult

```python
@dataclass
class VerificationResult:
    verified: bool
    changed: bool
    similarity: float
    text_diff: Tuple[str, str]
    confidence: float
```

### ExecutionReport

```python
@dataclass
class ExecutionReport:
    total_steps: int
    successful: int
    failed: int
    skipped: int
    duration: float
    results: List[Dict]
    screenshots_dir: str
```

---

## 구현 우선순위

### Phase 1: 기본 구조 (Day 11)

- [x] ActionMapper 인터페이스
- [ ] 3개 핵심 Action (INSTALL, CLICK, TYPE)
- [ ] RPAExecutor 기본 로직
- [ ] Dry-run 모드

### Phase 2: 검증 (Day 11)

- [ ] 스크린샷 캡처
- [ ] 이미지 유사도 비교 (PIL, opencv)
- [ ] ExecutionVerifier

### Phase 3: 통합 (Day 12)

- [ ] E2E Pipeline 통합
- [ ] Docker 설치 시뮬레이션
- [ ] 에러 처리 및 재시도

### Phase 4: 고도화 (Phase 3)

- [ ] OCR 기반 요소 찾기
- [ ] playwright 통합
- [ ] 학습 기반 액션 최적화

---

## 예상 파일 구조

```
fdo_agi_repo/rpa/
  ├── executor.py          (RPAExecutor, 200줄)
  ├── action_mapper.py     (ActionMapper, 150줄)
  ├── actions/
  │   ├── __init__.py
  │   ├── base.py         (Action base class)
  │   ├── install.py      (InstallAction)
  │   ├── click.py        (ClickAction)
  │   ├── type.py         (TypeAction)
  │   └── ...
  ├── verifier.py         (ExecutionVerifier, 100줄)
  └── reporter.py         (ExecutionReporter, 80줄)
```

**예상 총 코드**: ~600줄

---

## 테스트 계획

### Dry-run 테스트

```bash
python -m rpa.executor \
  --input outputs/steps/3c-iBn73dDE_refined.json \
  --mode dry-run \
  --output outputs/execution/dry_run_result.json
```

### Live-run 테스트 (Phase 3)

```bash
python -m rpa.executor \
  --input outputs/steps/3c-iBn73dDE_refined.json \
  --mode live \
  --verify \
  --output outputs/execution/live_run_result.json
```

---

**작성자**: GitHub Copilot  
**작성일**: 2025-10-31T15:00:00+09:00
"""
