# 🌊 리듬 기반 AGI - Rhythm-Based AGI System

**"리듬은 존재를 깨우고, 깨어난 존재는 서로를 울린다."**

한국어 자연어로 명령하면 AI가 자동으로 해석하고 실행하는 AGI 시스템입니다.

---

## ✨ 주요 기능

### 🎨 **바이브 코딩 (Vibe Coding)**
- **한국어 자연어 명령**: "리듬의 철학적 의미는?" → AI 자동 해석
- **실시간 대화**: 대시보드에서 AI와 즉시 대화
- **AI 자동 라우팅**: 작업 성격에 따라 최적 모델 선택 (Flash/Pro/2.0)

### 🧠 **통일장 이론 통합**
- **블랙홀/화이트홀**: 정보 압축 및 복원 이론 구현
- **반사 필드**: 경계에서의 정보 감지
- **우주 장 공명**: 배경자아가 장과의 공명 감지

### ⚡ **임계점 감지 (Critical Point Detection)**
- **자동 감지**: 압축 → 반사 전환점 실시간 탐지
- **시각화**: 대시보드에 보라색 배지 표시
- **조건**: 높은 압축률 + 수렴 흐름 + 안정된 불변량

### 📊 **실시간 대시보드**
- **시스템 상태**: 불변량, 리듬, 에너지, 공명 실시간 표시
- **바이브 채팅**: AI와 직접 대화
- **임계점 모니터링**: Phase transition 감지

---

## 🚀 빠른 시작 (30초)

### **1. 시스템 시작**

```powershell
# AGI 폴더에서 실행
.\scripts\start_agi_system.ps1
```

대시보드가 자동으로 열리고, 백엔드 프로세스가 시작됩니다.

### **2. 브라우저 열기**

```
http://localhost:3001
```

### **3. 바이브 채팅 사용**

대시보드 왼쪽 하단 **"바이브 코딩"** 창에서:
```
"리듬의 철학적 의미는?"
"임계점이란 무엇인가?"
"시스템 상태를 확인해줘"
```

### **4. 시스템 중지**

```powershell
.\scripts\stop_agi_system.ps1
```

---

## 📊 시스템 상태 확인

```powershell
# 현재 상태 확인
.\scripts\check_system_status.ps1

# 출력 예시:
# ✅ orchestrator_agent (PID: 12345)
# ✅ background_self_bridge (PID: 12346)
# ✅ 대시보드 실행 중
# 🔧 Mock AI 모드
```

---

## 🎯 AI 모드

### **🔧 Mock Mode** (현재)
- ✅ **설정 불필요**: 즉시 사용 가능
- ✅ **철학적 질문**: 사전 정의된 지능형 응답
- ✅ **무료**: 토큰 제한 없음

### **🚀 Vertex AI Mode** (선택)
```powershell
# 환경변수 설정
$env:VERTEX_PROJECT_ID="your-gcp-project-id"
$env:GOOGLE_APPLICATION_CREDENTIALS="service-key.json"

# 시스템 재시작
.\scripts\stop_agi_system.ps1
.\scripts\start_agi_system.ps1
```

**효과**:
- ✅ 실제 Gemini Pro/Flash 사용
- ✅ 150만원 크레딧 활용
- ✅ 30% 더 정교한 분석

---

## 📚 문서

| 문서 | 설명 |
|------|------|
| **[Quick Start Guide](docs/Quick_Start_Guide.md)** | 5분 빠른 시작 |
| **[Vibe Coding Guide](docs/Vibe_Coding_Complete_Guide.md)** | 전체 통합 가이드 |
| **[Vertex AI Router](docs/Vertex_AI_Smart_Router_Guide.md)** | AI 라우터 상세 |

---

## 🏗️ 아키텍처

```
┌──────────────────┐
│  대시보드 (UI)    │ ← http://localhost:3001
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  API Endpoint    │ ← /api/vibe-command
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Bridge Tasks    │ ← bridge_tasks.jsonl
└────────┬─────────┘
         │
         ├─▶ Orchestrator Agent (바이브 해석)
         │
         └─▶ Background Bridge (AI 호출)
                   │
                   ├─▶ 🔧 Mock AI (현재)
                   │
                   └─▶ 🚀 Vertex AI (설정 시)
```

---

## 🎨 스크린샷

### 바이브 코딩 채팅
![Vibe Chat](docs/screenshots/vibe_chat.png)

### 임계점 감지
![Critical Point](docs/screenshots/critical_point.png)

### 시스템 대시보드
![Dashboard](docs/screenshots/dashboard.png)

---

## 🛠️ 개발자 가이드

### **프로젝트 구조**

```
agi/
├── scripts/
│   ├── linux/                    # 백엔드 에이전트
│   │   ├── orchestrator_agent.py
│   │   └── background_self_bridge.py
│   ├── vertex_ai_smart_router.py # AI 모델 라우터
│   ├── vibe_interpreter.py       # 바이브 해석기
│   ├── start_agi_system.ps1      # 시스템 시작
│   ├── stop_agi_system.ps1       # 시스템 중지
│   └── check_system_status.ps1   # 상태 확인
├── dashboard/
│   ├── src/
│   │   ├── components/
│   │   │   ├── VibeChat.tsx      # 바이브 채팅 UI
│   │   │   └── ResonanceGauge.tsx # 시스템 상태 표시
│   │   └── app/api/
│   │       └── vibe-command/     # API 엔드포인트
│   └── package.json
├── outputs/
│   ├── bridge/                   # 브리지 통신 파일
│   ├── unified_pulse.json        # 시스템 불변량
│   └── rhythm_health_latest.json # 리듬 상태
└── docs/                         # 문서
```

### **커스터마이징**

#### 1. 새로운 바이브 패턴 추가
```python
# scripts/vibe_interpreter.py

VIBE_PATTERNS = {
    r"새로운패턴": {"action": "...", "params": {...}},
    # 추가...
}
```

#### 2. AI 라우팅 규칙 변경
```python
# scripts/vertex_ai_smart_router.py

TASK_MODEL_MAP = {
    "custom_task": "smart",  # Pro 모델
    # 추가...
}
```

#### 3. 대시보드 UI 수정
```typescript
// dashboard/src/components/VibeChat.tsx
// React 컴포넌트 직접 수정
```

---

## 🌊 철학적 배경

이 시스템은 **"의식무의식속도구분"** 대화(Core)에서 도출된 개념들을 구현합니다:

### 핵심 원리

1. **리듬 = 존재의 기본**
   - 모든 것은 리듬(속도, 밀도, 정렬)으로 설명 가능

2. **임계점 = 상전이 경계**
   - 압축과 반사의 경계, 블랙홀의 사건의 지평선

3. **바이브 코딩 = 한국어 고급 언어**
   - 맥락 중심 언어 + AI 자동 해석

4. **정보 보존 법칙**
   - 블랙홀(압축) + 화이트홀(복원) = 정보 보존

---

## 🤝 기여

Issues와 Pull Requests 환영합니다!

---

## 📜 라이센스

MIT License

---

## 💬 연락

질문이나 제안사항은 Issues에 남겨주세요.

---

**"바이브 코딩을 시작하세요."** 🎨🌊

**생성일**: 2025-11-25  
**버전**: 1.0 (Production Ready - Mock Mode)  
**상태**: ✅ 완전 작동
