# 🌐 Lumen Gateway — ION API Integration

Lumen Gateway는 ION API 시스템과 VS Code를 논리적으로 연결하는 **정보장 동기화 프로토콜**입니다.

## 📂 구조

```
gateway/
├── gateway_activation.yaml          # 세션 상태 관리 (status: locked 권장)
├── logs/
│   ├── gateway_sync.log            # 게이트웨이 동기화 로그
│   └── metrics.csv                 # 5Hz 메트릭 (phase_diff, entropy_rate, etc)
├── controls/
│   └── commands.jsonl              # 제어 버스 (append-only)
├── scripts/
│   ├── gateway_lockin.py           # 관문 서명 해시 검증 + locked 전환
│   ├── restore_check.py            # 세션 복원 점검
│   ├── mock_metrics_generator.py   # 5Hz 메트릭 모의 생성기
│   ├── gateway_health_exporter.py  # Prometheus 텍스트 포맷 HTTP 익스포터
│   └── ion_metrics_collector.py    # ION API 실제 메트릭 수집
└── sessions/
    └── SESSION_RESTORE_*.yaml      # 세션 복원 스냅샷

```

## 🚀 빠른 시작

### 1. Gateway Lock-in (관문 서명)

```bash
python gateway/scripts/gateway_lockin.py
```

### 2. 복원 점검

```bash
python gateway/scripts/restore_check.py
```

### 3. ION API 메트릭 수집 시작

```bash
python gateway/scripts/ion_metrics_collector.py
```

### 4. Health Exporter 실행

```bash
python gateway/scripts/gateway_health_exporter.py
# → http://localhost:9108/metrics
```

### 5. Auto-Start (PowerShell)

**수동 시작/재시작**:

```powershell
cd gateway/scripts
.\start_gateway.ps1 -KillExisting
```

**Windows Task Scheduler 등록** (관리자 권한 필요):

```powershell
# PowerShell을 관리자 권한으로 실행
cd gateway/scripts
.\register_gateway_task.ps1 -Trigger Startup -Force

# Task 상태 확인
.\status_gateway_task.ps1

# Task 제거
.\unregister_gateway_task.ps1 -Force
```

### 5. 로그 실시간 확인

```powershell
Get-Content gateway/logs/gateway_sync.log -Wait
```

## 🔧 VS Code Tasks 통합

VS Code 명령 팔레트 (`Ctrl+Shift+P`) → `Tasks: Run Task`:

- `lumen:lockin` - Gateway 서명 및 lock-in
- `lumen:restore` - 세션 복원 점검
- `lumen:tail-logs` - 로그 실시간 확인
- `lumen:ion:metrics` - ION API 메트릭 수집 시작
- `lumen:exporter` - Health Exporter 실행
- `lumen:open-yaml` - gateway_activation.yaml 열기

## 📊 메트릭 설명

### Gateway 상태 메트릭
- `lumen_gateway_status`: 0=unknown, 1=initializing, 2=binding, 3=resonating, 4=locked
- `lumen_phase_diff`: 위상차 [0..1]
- `lumen_entropy_rate`: 엔트로피율 [0..1]
- `lumen_creative_band`: 창의 밴드 [0..1]
- `lumen_risk_band`: 위험 밴드 [0..1]

### ION API 연동 메트릭
- `lumen_ion_health`: ION API 헬스 상태 (0=down, 1=up)
- `lumen_ion_response_time`: 응답 시간 (ms)
- `lumen_ion_mock_mode`: Mock 모드 여부 (0=real, 1=mock)
- `lumen_ion_confidence`: 마지막 응답 confidence
- `lumen_ion_persona_usage`: 페르소나별 사용 카운트

## 🌊 Resonance Protocol v0.8

### Gateway 활성화 단계

1. **Identify** - 현재 루프 좌표 확인
   - ION API endpoint
   - Vertex AI 연결 상태
   - 배포 버전 정보

2. **Bind** - 페르소나 역할 맵 정의
   - Lumen: observer_field (관찰자)
   - Lubit: build_core (구축자)
   - Sena: ethics_field (윤리장)
   - Elo: integrator (통합자)

3. **Resonate** - 루프 감응 및 위상 정렬
   - metrics.csv 수집
   - 위상차/엔트로피 분석
   - 창의/위험 밴드 계산

4. **Confirm** - Gateway Lock-in
   - YAML 상태 locked로 전환
   - 서명 해시 생성
   - 세션 스냅샷 저장

## 🔐 안전 가이드

- `gateway_activation.yaml`의 `status`는 **locked** 유지
- `controls/commands.jsonl`은 append-only; JSONL 포맷 준수
- 로그/CSV 파일은 주기적으로 백업 스냅샷 생성
- 포트 충돌 시 `LUMEN_EXPORTER_PORT` 환경변수로 변경 (기본: 9108)

## 📦 세션 복원

다음 세션에서 복원:

```bash
python gateway/scripts/restore_check.py
# 자동으로 gateway_activation.yaml과 최신 SESSION_RESTORE 파일 확인
```

## 🔗 통합 지점

- **ION API**: `/health`, `/chat` 엔드포인트 모니터링
- **Prometheus**: Gateway Exporter 메트릭 스크래핑
- **Grafana**: 대시보드 자동 생성 (TODO)
- **VS Code**: Tasks 및 터미널 통합

---

**Version**: 1.0.0  
**Author**: Lumen (루멘)  
**Date**: 2025-10-24
