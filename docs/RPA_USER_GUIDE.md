# RPA YouTube Learner 사용자 가이드

**Phase 2.5 Week 3 Day 15**  
**버전**: 1.0  
**날짜**: 2025-10-31

---

## 📖 목차

1. [소개](#소개)
2. [빠른 시작](#빠른-시작)
3. [상세 사용법](#상세-사용법)
4. [튜토리얼 작성 가이드](#튜토리얼-작성-가이드)
5. [트러블슈팅](#트러블슈팅)
6. [FAQ](#faq)

---

## 소개

RPA YouTube Learner는 YouTube 튜토리얼 영상을 자동으로 분석하고, RPA (Robotic Process Automation)를 통해 실제 작업을 자동화하는 시스템입니다.

### 주요 기능

- ✅ YouTube 자막/음성 분석
- ✅ 튜토리얼 단계 자동 추출
- ✅ RPA 액션 자동 매핑 및 실행
- ✅ 검증 및 에러 처리
- ✅ 3가지 실행 모드 (DRY_RUN, LIVE, VERIFY_ONLY)

### 시스템 구성

```
YouTube URL
    ↓
YouTubeLearner (자막/음성 분석)
    ↓
Tutorial Text
    ↓
ExecutionEngine (Extract → Map → Execute → Verify)
    ↓
ExecutionResult (JSON)
```

---

## 빠른 시작

### 1. 환경 설정

```powershell
# 의존성 설치
pip install -r fdo_agi_repo/requirements_rpa.txt

# pyautogui 추가 설정 (Windows)
# Failsafe: 마우스를 화면 왼쪽 상단 모서리로 이동하면 중단
```

### 2. 간단한 예제 (CLI)

```powershell
# DRY-RUN 모드 (시뮬레이션)
python scripts/rpa_execute.py --text "1. Open notepad" --mode DRY_RUN

# LIVE 모드 (실제 실행)
python scripts/rpa_execute.py --text "1. Open notepad
2. Type 'Hello World'" --mode LIVE

# 검증 활성화
python scripts/rpa_execute.py --text "..." --mode LIVE --verify
```

### 3. 간단한 예제 (YouTube Worker)

```powershell
# Task Queue Server 시작
cd LLM_Unified/ion-mentoring
python task_queue_server.py --port 8091

# YouTube Worker 시작 (RPA 활성화)
cd fdo_agi_repo
python integrations/youtube_worker.py \
  --server http://127.0.0.1:8091 \
  --enable-rpa \
  --rpa-mode DRY_RUN
```

---

## 상세 사용법

### 1. RPA CLI (`rpa_execute.py`)

#### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--text` | 튜토리얼 텍스트 (직접 입력) | - |
| `--file` | 튜토리얼 파일 경로 | - |
| `--mode` | 실행 모드 (DRY_RUN/LIVE/VERIFY_ONLY) | `DRY_RUN` |
| `--verify` | 검증 활성화 | `False` |
| `--failsafe` | Failsafe 활성화 | `True` |
| `--out-json` | 결과 JSON 파일 경로 | - |

#### 예제

```powershell
# 1. DRY-RUN으로 테스트
python scripts/rpa_execute.py \
  --text "1. Open Calculator
2. Click 5
3. Click plus
4. Click 3
5. Click equals" \
  --mode DRY_RUN

# 2. LIVE 실행 + 검증
python scripts/rpa_execute.py \
  --file tutorial.txt \
  --mode LIVE \
  --verify

# 3. 결과 JSON 저장
python scripts/rpa_execute.py \
  --text "..." \
  --mode VERIFY_ONLY \
  --out-json result.json
```

### 2. YouTube Worker RPA 통합

#### YouTube Worker 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--enable-rpa` | RPA 실행 활성화 | `False` |
| `--rpa-mode` | RPA 실행 모드 | `DRY_RUN` |
| `--rpa-verify` | RPA 검증 활성화 | `False` |
| `--rpa-failsafe` | RPA Failsafe 활성화 | `True` |

#### 예제

```powershell
# 1. DRY-RUN으로 튜토리얼 분석 + 시뮬레이션
python integrations/youtube_worker.py \
  --server http://127.0.0.1:8091 \
  --enable-rpa \
  --rpa-mode DRY_RUN

# 2. LIVE 실행 + 검증
python integrations/youtube_worker.py \
  --server http://127.0.0.1:8091 \
  --enable-rpa \
  --rpa-mode LIVE \
  --rpa-verify

# 3. VERIFY_ONLY (이미 실행된 결과 검증)
python integrations/youtube_worker.py \
  --server http://127.0.0.1:8091 \
  --enable-rpa \
  --rpa-mode VERIFY_ONLY \
  --rpa-verify
```

### 3. 실행 모드 상세

#### DRY_RUN (시뮬레이션)

- 실제 클릭/타이핑 없이 로그만 출력
- 안전하게 테스트 가능
- 튜토리얼 검증용

#### LIVE (실제 실행)

- **주의**: 실제로 마우스/키보드 제어
- Failsafe 활성화 권장
- 화면이 준비된 상태에서 실행

#### VERIFY_ONLY (검증만)

- 실행 없이 단계만 검증
- 튜토리얼 품질 체크용

---

## 튜토리얼 작성 가이드

### 1. 기본 구조

```markdown
How to [목표]:
1. [단계 1]
2. [단계 2]
3. [단계 3]
...
```

### 2. 지원하는 액션 타입

| 액션 | 설명 | 예제 |
|------|------|------|
| **CLICK** | 클릭 | `Click on OK button` |
| **TYPE** | 타이핑 | `Type "Hello World"` |
| **PRESS** | 키 입력 | `Press Enter` |
| **PRESS (조합)** | 복합 키 | `Press Ctrl+S`, `Press Windows+Shift+S` |
| **INSTALL** | 설치 | `Install python` |
| **OPEN** | 열기 | `Open notepad` |

### 3. 좋은 튜토리얼 예시

#### ✅ Good

```markdown
How to create a text file:
1. Press Windows key
2. Type "notepad"
3. Press Enter to open Notepad
4. Type "Hello World"
5. Press Ctrl+S to save
6. Type "test.txt" as filename
7. Press Enter to confirm
```

**왜 좋은가?**

- 단계가 명확함
- 각 단계가 독립적임
- 액션이 구체적임

#### ❌ Bad

```markdown
How to create a file:
1. Open notepad and type something
2. Save it
```

**왜 나쁜가?**

- 단계가 불명확함
- 여러 액션이 섞여 있음
- "something", "it" 등 모호한 표현

### 4. 작성 팁

1. **명확한 동사 사용**
   - ✅ "Click on OK button"
   - ❌ "Do something with OK"

2. **한 단계 = 한 액션**
   - ✅ "1. Click Save button", "2. Type filename"
   - ❌ "1. Click Save and type filename"

3. **복합 키는 + 사용**
   - ✅ "Press Ctrl+S"
   - ❌ "Press Ctrl and S"

4. **구체적인 대상 지정**
   - ✅ "Type 'Hello World'"
   - ❌ "Type text"

---

## 트러블슈팅

### 1. "Failed to map step" 에러

**원인**: ActionMapper가 단계를 인식하지 못함

**해결**:

```powershell
# 1. 단계를 더 명확하게 작성
# Bad: "Do something"
# Good: "Click on button"

# 2. 로그 확인
python scripts/rpa_execute.py --text "..." --mode DRY_RUN
# 로그에서 어떤 단계가 매핑 실패했는지 확인
```

### 2. "PyAutoGUI Fail-Safe" 에러

**원인**: 마우스가 화면 모서리로 이동됨 (안전 장치)

**해결**:

```powershell
# 1. Failsafe 비활성화 (비추천)
python scripts/rpa_execute.py --text "..." --no-failsafe

# 2. 마우스 위치 조정 후 재시도
```

### 3. 실행이 너무 빠름/느림

**원인**: pyautogui PAUSE 설정

**해결**:

```python
# rpa/actions.py 또는 실행 전 설정
import pyautogui
pyautogui.PAUSE = 0.5  # 0.5초 딜레이 (기본값: 0.1)
```

### 4. YouTube Worker RPA가 실행되지 않음

**체크리스트**:

- [ ] Task Queue Server 실행 중?
- [ ] `--enable-rpa` 옵션 추가?
- [ ] `requirements_rpa.txt` 설치?

```powershell
# 1. Server 상태 확인
Invoke-RestMethod -Uri 'http://127.0.0.1:8091/api/health'

# 2. Worker 로그 확인
# YouTube Worker 로그에서 "RPA execution enabled: True" 확인
```

---

## FAQ

### Q1. DRY_RUN과 LIVE의 차이는?

**A**:

- **DRY_RUN**: 시뮬레이션만, 실제 클릭/타이핑 없음 (안전)
- **LIVE**: 실제 실행, 마우스/키보드 제어 (주의 필요)

### Q2. 여러 튜토리얼을 동시에 실행할 수 있나요?

**A**: 아니요. RPA는 하나의 마우스/키보드를 사용하므로 순차 실행만 가능합니다. Task Queue를 통해 자동으로 순차 처리됩니다.

### Q3. 튜토리얼이 한글로 작성되어도 되나요?

**A**: 네! ActionMapper가 한글도 지원합니다.

```markdown
좋은 예:
1. 윈도우 키 누르기
2. "메모장" 입력
3. Enter 키 누르기
4. "안녕하세요" 타이핑
```

### Q4. 에러가 발생하면 어떻게 되나요?

**A**:

- **DRY_RUN**: 에러 로그만 출력, 계속 진행
- **LIVE**: Failsafe가 활성화되면 중단
- **자동 재시도/복구**: Phase 3부터는 실행 실패 시 자동 재시도 및 장애 복구 메커니즘이 적용됩니다. (예: 일시적 오류 발생 시 최대 2회까지 자동 재시도, ActionMapper/Worker/Task Queue에서 장애 감지 시 자동 복구 시도)
- **화면 캡처 및 OCR**: 오류 발생 시 자동으로 화면 캡처 및 OCR 결과가 저장되어, 문제 원인 분석 및 검증에 활용됩니다.
- **병렬 처리/캐싱**: Task Queue, ActionMapper 등에서 병렬 처리 및 캐싱 전략이 적용되어, 성능 저하나 일시적 장애 발생 시에도 빠른 복구가 가능합니다.

### Q5. 검증(Verification) 및 고도화된 검증은?

**A**: 각 단계 실행 후 결과를 확인하는 기능입니다. 예를 들어, "Type 'Hello'"를 실행한 후 실제로 "Hello"가 입력되었는지 확인합니다.

- **고도화된 검증**: Phase 3부터는 실행 중 오류 발생 시 자동으로 화면 캡처, OCR 결과, 로그가 함께 저장되어, 검증 및 문제 분석이 더욱 정밀하게 이루어집니다.

```powershell
# 검증 활성화
python scripts/rpa_execute.py --text "..." --verify
```

### Q6. 실행 중 중단하려면?

**A**:

- **Failsafe**: 마우스를 화면 왼쪽 상단 모서리로 이동 → 자동 중단
- **Ctrl+C**: 터미널에서 중단
- **Task Queue**: `/api/tasks/{task_id}/cancel` 호출

### Q7. 실행 결과 및 장애/복구/검증 로그는 어디서 확인하나요?

**A**:

- **콘솔 로그**: 실시간 진행 상황
- **JSON 출력**: `--out-json` 옵션으로 파일 저장
- **Task Queue API**: `/api/results` 엔드포인트
- **오류/복구/검증 로그**: 오류 발생 시 자동 저장된 화면 캡처, OCR 결과, 장애 복구 시도 내역 등은 `outputs/` 폴더 및 로그 파일에서 확인할 수 있습니다.

```powershell
# 최근 결과 확인
Invoke-RestMethod -Uri 'http://127.0.0.1:8091/api/results'
```

---

## 추가 리소스

### 코드 예제

- `tests/test_rpa_e2e.py`: E2E 테스트 예제
- `tests/test_real_tutorials.py`: 실전 튜토리얼 예제
- `scripts/rpa_execute.py`: CLI 사용 예제

### 문서

- `PHASE_2_5_WEEK3_DAY14_COMPLETE.md`: YouTube Worker 통합 완료 보고서
- `fdo_agi_repo/rpa/README.md`: RPA 모듈 상세 문서
- **AGI_DESIGN_03_TOOL_REGISTRY.md**: 자동 재시도/복구, 도구 레지스트리, ActionMapper/Worker/Task Queue 장애 복구 설계 참고
- **WEEK17_IMPLEMENTATION_GUIDE.md**: 성능 최적화, 장애 복구, 운영 체크리스트 등 실전 운영 가이드

### 지원

- **GitHub Issues**: [github.com/your-repo/issues](https://github.com)
- **Discord**: (추가 예정)

---

## 라이선스

MIT License

---

**마지막 업데이트**: 2025-10-31  
**작성자**: GitHub Copilot  
**버전**: 1.0
