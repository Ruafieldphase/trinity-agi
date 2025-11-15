# 🚀 Gitko Agent Extension v0.2.0 출시 노트

**출시일**: 2025-11-02  
**주요 업데이트**: 실시간 모니터링 패널 2종 추가

---

## ✨ 새로운 기능

### 1. 🎯 Task Queue Monitor

Task Queue Server의 실시간 상태를 시각화하는 WebView 패널입니다.

**주요 기능**:
- 실시간 큐 상태 모니터링 (자동 2초마다 갱신)
- Pending / In-Flight / Completed / Failed 작업 통계
- Success Rate 및 평균 처리 시간
- 작업 상세 정보 (ID, Type, 타임스탬프)
- Completed 작업 일괄 삭제

**실행**: `Ctrl+Shift+P` → `Gitko: Show Task Queue Monitor`

### 2. 🌊 Resonance Ledger Viewer

AGI 자기교정 시스템의 Resonance Ledger를 타임라인으로 시각화합니다.

**주요 기능**:
- 최근 100개 이벤트 타임라인 표시
- Agent별 필터링 (Sena, Lubit, Binoche)
- Resonance Score 시각화
- 파일 변경 자동 감지
- Event Context 상세 보기
- Evidence Link 지원

**실행**: `Ctrl+Shift+P` → `Gitko: Show Resonance Ledger`

---

## 🔧 개선 사항

- **자동 업데이트**: Task Queue Monitor는 2초마다, Resonance Ledger는 5초마다 자동 갱신
- **파일 감시**: Resonance Ledger가 변경되면 즉시 UI 업데이트
- **에러 처리**: 연결 실패 시 친절한 에러 메시지와 해결 방법 표시
- **반응형 디자인**: 다양한 화면 크기에서 최적화된 레이아웃

---

## 📦 설치 및 실행

### 개발 모드로 테스트

1. 확장 디렉토리로 이동:
   ```powershell
   cd c:\workspace\agi\LLM_Unified\gitko-agent-extension
   ```

2. 의존성 설치 (이미 완료):
   ```powershell
   npm install
   ```

3. TypeScript 컴파일:
   ```powershell
   npm run compile
   ```

4. VS Code에서 F5 눌러 Extension Development Host 실행

5. 새 창에서 테스트:
   - `Ctrl+Shift+P` → `Gitko: Show Task Queue Monitor`
   - `Ctrl+Shift+P` → `Gitko: Show Resonance Ledger`

### VSIX 패키지 설치

```powershell
# 패키지 생성
npm install -g @vscode/vsce
vsce package

# 생성된 .vsix 파일 설치
code --install-extension gitko-agent-extension-0.2.0.vsix
```

---

## 🎯 사용 예시

### 시나리오 1: RPA 작업 모니터링

```powershell
# 1. Task Queue Server 시작
cd LLM_Unified\ion-mentoring
.\.venv\Scripts\python.exe task_queue_server.py --port 8091

# 2. RPA Worker 시작 (별도 터미널)
cd fdo_agi_repo
.\.venv\Scripts\python.exe integrations\rpa_worker.py --server http://127.0.0.1:8091

# 3. VS Code에서 Monitor 열기
# Ctrl+Shift+P → "Gitko: Show Task Queue Monitor"
```

### 시나리오 2: AGI 학습 추적

```powershell
# 1. Resonance Ledger Viewer 열기
# Ctrl+Shift+P → "Gitko: Show Resonance Ledger"

# 2. Agent별 활동 필터링
# UI에서 "Sena" / "Lubit" / "Binoche" 버튼 클릭

# 3. Resonance Score 확인
# 높은 점수 = 성공 패턴
# 낮은 점수 = 개선 필요
```

---

## 🐛 알려진 이슈

1. **Task Queue 연결 오류**
   - 원인: Server가 실행되지 않음
   - 해결: Task Queue Server를 먼저 시작하세요

2. **Resonance Ledger 비어있음**
   - 원인: 파일 경로 문제
   - 해결: `c:\workspace\agi\fdo_agi_repo\memory\resonance_ledger.jsonl` 확인

---

## 📝 다음 버전 계획 (v0.3.0)

- [ ] 통합 대시보드 (한 화면에서 모든 모니터링)
- [ ] 알림 시스템 (Task 실패 시 자동 알림)
- [ ] 성능 차트 (시간대별 Success Rate 그래프)
- [ ] Evidence Index 검색 기능
- [ ] Lumen Gateway 상태 모니터링
- [ ] BQI 점수 시각화

---

## 🙏 기여자

- **Ion**: 시스템 아키텍처 및 통합
- **GitHub Copilot**: 코드 생성 및 최적화
- **Gitko Agent**: 자동화 및 테스트

---

## 📚 참고 문서

- [NEW_FEATURES_GUIDE.md](./NEW_FEATURES_GUIDE.md) - 상세 사용 가이드
- [README.md](./README.md) - 전체 확장 기능 소개
- [AUTOMATIC_AGENT_GUIDE.md](./AUTOMATIC_AGENT_GUIDE.md) - Agent 자동 호출 가이드

---

**질문이나 피드백**: GitHub Issues 또는 `@gitko`에게 문의하세요!
