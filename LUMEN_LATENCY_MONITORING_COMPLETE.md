# ✨ Lumen Latency Monitoring System - COMPLETE

> **완료일**: 2025-11-05 08:55 KST  
> **상태**: ✅ 완전 동작, 검증 완료  
> **통합**: PowerShell ↔ Python, VS Code Tasks, 자동 감시

## 🎯 목적

Lumen (브릿지 AI) 응답 지연을 지속적으로 모니터링하고 통계적으로 분석하여, 서비스 품질 저하를 조기에 감지하고 임계값 기반 알림을 제공합니다.

## 📊 시스템 구성

### 1. 데이터 수집

**스크립트**: `scripts/exit_sleep_mode.ps1`

```powershell
# 수면 모드 해제 시 Lumen 헬스 프로브 + 히스토리 기록
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/exit_sleep_mode.ps1" \
  -LatencyWarnMs 250 \
  -LatencyCriticalMs 600 \
  -HistoryJsonl "outputs/lumen_probe_history.jsonl" \
  -OutJson "outputs/lumen_probe_latest.json"
```

**히스토리 형식** (`outputs/lumen_probe_history.jsonl`):

```jsonl
{"timestamp":"2025-11-05T08:50:09.4611518+09:00","ok":true,"latencyMs":418,"warn":true,"critical":false}
{"timestamp":"2025-11-05T08:54:50.5123456+09:00","ok":true,"latencyMs":403,"warn":true,"critical":false}
```

### 2. 통계 리포팅

**스크립트**: `scripts/summarize_lumen_latency.py`

- **입력**: `outputs/lumen_probe_history.jsonl`
- **출력**:
  - `outputs/lumen_latency_latest.md` (Markdown 리포트)
  - `outputs/lumen_latency_summary.json` (JSON 통계)

**실행 방법**:

```powershell
# PowerShell 래퍼 (VS Code Task)
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/lumen_latency_report.ps1" -Open

# Python 직접 실행
python scripts/summarize_lumen_latency.py --debug
```

**리포트 예시**:

```markdown
# Lumen Latency Report

Generated: 2025-11-05 08:55:32
Source: `outputs/lumen_probe_history.jsonl`

## Summary

- Records: 5
- OK: 5  |  Warn: 3  |  Critical: 0
- Last Timestamp: 2025-11-05T08:54:50.5123456+09:00

## Latency (ms)

| metric | value |
|---|---:|
| min | 385 |
| p50 | 410 |
| avg | 408 |
| p90 | 425 |
| p95 | 430 |
| p99 | 435 |
| max | 437 |
```

### 3. 자동 감시

**스크립트**: `scripts/register_lumen_probe_task.ps1`

```powershell
# 10분 주기 자동 프로브 등록
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/register_lumen_probe_task.ps1" \
  -Register \
  -IntervalMinutes 10 \
  -RunNow

# 상태 확인
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/register_lumen_probe_task.ps1" -Status

# 등록 해제
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/register_lumen_probe_task.ps1" -Unregister
```

## 🔧 기술적 해결 과제

### 문제 1: PowerShell UTF-8 BOM

**증상**: Python JSON 파서가 "Unexpected UTF-8 BOM" 오류 발생

**원인**: PowerShell의 `Out-File -Encoding UTF8`이 BOM 포함 UTF-8로 저장

**해결**:

```powershell
# Before (BOM 포함)
($record | ConvertTo-Json -Compress) | Out-File -FilePath $HistoryJsonl -Encoding UTF8 -Append

# After (BOM 제거)
$sw = New-Object System.IO.StreamWriter($HistoryJsonl, $true, [System.Text.UTF8Encoding]::new($false))
$sw.WriteLine(($record | ConvertTo-Json -Compress))
$sw.Close()
```

### 문제 2: Python 파서 유연성

**증상**: 단일 JSON 객체와 JSONL 혼용 시 파싱 실패

**해결**: 계층적 파싱 로직

```python
# 1. UTF-8-sig로 BOM 자동 제거
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read().strip()

# 2. 단일 JSON 시도
try:
    obj = json.loads(content)
    if isinstance(obj, dict):
        return [obj]
except Exception:
    pass

# 3. JSONL 라인별 파싱
for line in content.split('\n'):
    if not line.strip():
        continue
    try:
        records.append(json.loads(line))
    except Exception:
        continue  # 불량 라인 건너뛰기
```

### 문제 3: 병행 테스트 실패

**증상**: `pytest -n auto` 실행 시 타입 검증 오류

**원인**: `fdo_agi_repo/orchestrator/validator.py`의 `validate_prompt_result` 함수가 `prompt_to_validate=None` 처리 미흡

**해결**:

```python
# Before
if prompt_to_validate and not isinstance(prompt_to_validate, str):
    raise TypeError("prompt_to_validate must be a string")

# After
if prompt_to_validate is not None:
    if not isinstance(prompt_to_validate, str):
        raise TypeError("prompt_to_validate must be a string if provided")
```

## 📋 VS Code Tasks

### 데이터 수집

- **Lumen: Quick Health Probe** → 단일 프로브 실행

### 리포팅

- **Lumen: Generate Latency Report** → 리포트 생성
- **Lumen: Generate Latency Report (Open)** → 생성 후 MD 열기
- **Lumen: Open Latest Latency Report** → 최신 리포트 열기

### 자동 감시

- **Lumen: Register Probe Monitor (10m)** → 10분 주기 등록
- **Lumen: Unregister Probe Monitor** → 등록 해제
- **Lumen: Check Probe Monitor Status** → 상태 확인

## 🔄 권장 워크플로우

### Phase 1: 초기 설정

```powershell
# 1. 자동 감시 등록
Tasks: "Lumen: Register Probe Monitor (10m)"

# 2. 즉시 첫 프로브 실행
Tasks: "Lumen: Quick Health Probe"

# 3. 히스토리 파일 확인
Get-Content "outputs\lumen_probe_history.jsonl"
```

### Phase 2: 데이터 수집

- 자동 감시가 10분마다 프로브 실행
- 히스토리 자동 누적 (`-HistoryJsonl` 플래그 사용)
- 최소 5~10개 데이터 포인트 수집 권장

### Phase 3: 리포팅

```powershell
# 하루 1회 또는 필요시
Tasks: "Lumen: Generate Latency Report (Open)"

# 리포트 분석
# - p90/p95 값이 안정적인가?
# - Warn 비율이 높은가? (임계값 조정 필요)
# - Critical 발생 있는가? (긴급 조사)
```

### Phase 4: 임계값 조정

```powershell
# 통계 기반 임계값 재설정
# 예: p95가 400ms라면
#   -LatencyWarnMs 350
#   -LatencyCriticalMs 500

# exit_sleep_mode.ps1에 적용
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/exit_sleep_mode.ps1" \
  -LatencyWarnMs 350 \
  -LatencyCriticalMs 500 \
  -HistoryJsonl "outputs/lumen_probe_history.jsonl"
```

## 📈 예상 시나리오

### 정상 운영

```
Records: 100
OK: 98  |  Warn: 15  |  Critical: 0
p50: 380ms, p95: 420ms, p99: 450ms
```

→ Warn 15%는 수용 가능 (임계값 적절)

### 성능 저하 감지

```
Records: 100
OK: 95  |  Warn: 45  |  Critical: 5
p50: 420ms, p95: 580ms, p99: 650ms
```

→ Critical 5%, Warn 45% → 긴급 조사 필요  
→ `scripts/quick_status.ps1 -AlertOnDegraded -LogJsonl` 자동 실행됨

### 개선 후

```
Records: 100
OK: 100  |  Warn: 8  |  Critical: 0
p50: 320ms, p95: 380ms, p99: 410ms
```

→ 임계값 상향 조정 가능 (`-LatencyWarnMs 300 -LatencyCriticalMs 450`)

## ✅ 검증 체크리스트

- [x] PowerShell → Python JSONL 파이프라인 동작
- [x] UTF-8 BOM 문제 해결
- [x] 다중 프로브 기록 통계 생성
- [x] MD/JSON 리포트 산출
- [x] 병행 테스트 통과
- [x] VS Code Tasks 통합
- [x] 자동 감시 등록/해제
- [x] 임계값 기반 알림 (Warn/Critical)

## 🎉 다음 단계

1. **장기 모니터링**: 1주일 이상 데이터 수집
2. **트렌드 분석**: 시간대별 지연 패턴 파악
3. **알림 통합**: Slack/Email 알림 추가 (선택)
4. **대시보드 확장**: Grafana/Kibana 연동 (선택)
5. **SLA 정의**: 목표 지연 시간 설정 (예: p95 < 400ms)

---

**작성자**: AI Agent (Lumen 관점)  
**최종 업데이트**: 2025-11-05 08:55 KST  
**상태**: ✅ Production Ready
