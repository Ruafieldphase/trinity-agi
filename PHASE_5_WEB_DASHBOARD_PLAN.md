# Phase 5: 웹 기반 실시간 대시보드 구축

**시작 날짜**: 2025-10-31  
**예상 소요 시간**: 1.5-2시간  
**목표**: 브라우저 기반 실시간 모니터링 대시보드

---

## 🎯 목표

Phase 4에서 구축한 콘솔 기반 모니터링을 **웹 대시보드**로 업그레이드하여:

- 브라우저에서 실시간 차트 확인
- 여러 사용자가 동시에 모니터링
- 히스토리 데이터 시각화 (트렌드 분석)
- 모바일에서도 접근 가능

---

## 📋 구현 계획

### 1단계: 백엔드 API 서버 (30분)

**기술 스택**: FastAPI (Python)

**엔드포인트**:

- `GET /api/metrics/latest` - 최신 메트릭 (JSON)
- `GET /api/metrics/history?minutes=30` - 히스토리 (JSONL → JSON)
- `GET /api/alerts/recent?count=20` - 최근 알림
- `GET /api/system/status` - 시스템 상태 요약
- `WebSocket /ws/metrics` - 실시간 스트리밍

**구현 파일**:

- `fdo_agi_repo/monitoring/web_server.py` (~200줄)

**주요 기능**:

- JSONL 파일 읽기 (메트릭, 알림)
- JSON 변환 및 필터링
- CORS 설정 (브라우저 접근 허용)
- WebSocket 스트리밍 (3초 간격)

---

### 2단계: 프론트엔드 대시보드 (60분)

**기술 스택**: HTML + Vanilla JS + Chart.js

**페이지 구성**:

```
┌─────────────────────────────────────────────────┐
│  🔍 RPA Monitoring Dashboard                    │
│  Last updated: 2025-10-31 20:30:15  [Refresh]  │
├─────────────────────────────────────────────────┤
│                                                  │
│  📊 Current Status                               │
│  ┌───────────────┬───────────────┬─────────────┐│
│  │ Success Rate  │ Active Workers│ Queue Size  ││
│  │   85.7%       │      3        │     5       ││
│  │   🟢          │               │             ││
│  └───────────────┴───────────────┴─────────────┘│
│                                                  │
│  📈 Success Rate Trend (30min)                  │
│  ┌─────────────────────────────────────────────┐│
│  │     Chart.js Line Chart (실시간 업데이트)    ││
│  │     X축: 시간, Y축: 성공률 (%)              ││
│  └─────────────────────────────────────────────┘│
│                                                  │
│  ⏱️ Response Time Distribution                 │
│  ┌─────────────────────────────────────────────┐│
│  │     Chart.js Bar Chart                       ││
│  │     평균 응답 시간 추이                       ││
│  └─────────────────────────────────────────────┘│
│                                                  │
│  🚨 Recent Alerts (Last 10)                     │
│  ┌─────────────────────────────────────────────┐│
│  │ [CRITICAL] 20:25:30 - Error rate high: 25%  ││
│  │ [WARNING]  20:20:15 - Response slow: 850ms  ││
│  │ [INFO]     20:15:00 - Worker added: worker-2││
│  └─────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
```

**구현 파일**:

- `fdo_agi_repo/monitoring/static/index.html` (~150줄)
- `fdo_agi_repo/monitoring/static/app.js` (~200줄)
- `fdo_agi_repo/monitoring/static/style.css` (~100줄)

**주요 기능**:

- 실시간 데이터 페치 (3초 간격)
- Chart.js로 실시간 차트 업데이트
- WebSocket 연결 (선택적)
- 반응형 디자인 (모바일 대응)

---

### 3단계: 통합 및 테스트 (30분)

**테스트 시나리오**:

1. FastAPI 서버 시작
2. 브라우저에서 `http://localhost:8000` 접속
3. Task Queue Server + RPA Worker 실행
4. 작업 추가 → 실시간 차트 업데이트 확인
5. 알림 발생 → 대시보드에 표시 확인

**검증 항목**:

- ✅ 차트 실시간 업데이트 (3초 간격)
- ✅ 성공률, 에러율 정확히 표시
- ✅ 알림 목록 최신순 정렬
- ✅ 모바일 반응형 디자인
- ✅ WebSocket 연결 안정성

---

## 🛠️ 기술 스택

### 백엔드

- **FastAPI**: 경량 웹 프레임워크
- **uvicorn**: ASGI 서버
- **WebSocket**: 실시간 스트리밍

### 프론트엔드

- **HTML5 + CSS3**: 기본 구조
- **Vanilla JavaScript**: 의존성 최소화
- **Chart.js**: 차트 라이브러리 (CDN)
- **Fetch API**: HTTP 요청

### 데이터

- **JSONL**: 메트릭/알림 저장 (Phase 4에서 생성)
- **JSON**: API 응답 포맷

---

## 📁 파일 구조

```
fdo_agi_repo/monitoring/
├── metrics_collector.py      (Phase 4)
├── alert_manager.py          (Phase 4)
├── monitoring_daemon.py      (Phase 4)
├── web_server.py             (NEW - FastAPI 서버)
├── static/
│   ├── index.html            (NEW - 메인 페이지)
│   ├── app.js                (NEW - 로직)
│   └── style.css             (NEW - 스타일)
└── __init__.py
```

---

## 🚀 Quick Start (Phase 5 완료 후)

```bash
# 터미널 1: Task Queue Server
cd C:\workspace\agi\LLM_Unified\ion-mentoring
.\.venv\Scripts\python.exe task_queue_server.py --port 8091

# 터미널 2: RPA Worker
cd C:\workspace\agi\fdo_agi_repo
.\.venv\Scripts\python.exe integrations\rpa_worker.py --server http://127.0.0.1:8091

# 터미널 3: Web Dashboard
cd C:\workspace\agi\fdo_agi_repo
.\.venv\Scripts\python.exe monitoring\web_server.py --port 8000

# 브라우저에서 접속
http://localhost:8000
```

---

## 📊 예상 성과

### 사용성 개선

- ✅ 콘솔 → 웹 브라우저 (시각적)
- ✅ 한 화면에서 모든 정보 확인
- ✅ 차트로 트렌드 즉시 파악
- ✅ 모바일에서도 접근 가능

### 기능 추가

- ✅ 실시간 차트 (성공률, 응답시간)
- ✅ 히스토리 데이터 조회 (30분, 1시간, 24시간)
- ✅ 알림 필터링 (Critical/Warning/Info)
- ✅ 시스템 상태 요약 (한눈에)

### 확장성

- ✅ API 기반 → 다른 클라이언트 연동 가능
- ✅ WebSocket → 실시간 푸시 알림
- ✅ 정적 파일 → CDN 배포 가능
- ✅ 반응형 디자인 → 다양한 디바이스 지원

---

## 🎯 성공 기준

1. **기능 완성도**: 모든 엔드포인트 정상 동작 (5개)
2. **실시간성**: 3초 간격 차트 업데이트
3. **정확성**: 메트릭 값 100% 정확
4. **반응성**: API 응답 시간 < 50ms
5. **안정성**: 1시간 연속 실행 무중단

---

## 📈 Phase 5 이후 로드맵

### Phase 6 (선택)

- **Option A**: 알림 통합 (Slack, Email, SMS)
- **Option B**: 고급 분석 (이상 탐지, 예측)
- **Option C**: 인프라 자동화 (Auto-scaling)
- **Option D**: 다중 서버 모니터링

---

## 🚦 시작 준비

**Prerequisites**:

- ✅ Phase 4 완료 (메트릭 수집, 알림 시스템)
- ✅ JSONL 데이터 파일 존재
- ✅ Python 3.8+ 설치
- ⚠️ FastAPI, uvicorn 설치 필요

**시작 명령**:

```bash
# FastAPI 설치
pip install fastapi uvicorn websockets

# 개발 시작
code c:\workspace\agi\fdo_agi_repo\monitoring\web_server.py
```

---

**다음 단계**: 1단계 (FastAPI 백엔드) 구축 시작! 🚀
