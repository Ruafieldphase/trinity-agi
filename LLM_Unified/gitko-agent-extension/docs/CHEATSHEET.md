# 🚀 Gitko Extension - 치트시트 (Quick Reference)

**v0.3.1** | 1분 안에 찾는 모든 명령어

---

## ⚡ 가장 많이 사용하는 명령어

### 자연어로 Agent 호출 (자동)

```
# Copilot Chat에서 그냥 말하기
"이 코드 리팩토링해줘" → Sian 자동 실행
"보안 문제 찾아줘" → Lubit 자동 실행
"전체 프로젝트 분석해줘" → Gitko 자동 실행
```

### Chat Participant (수동)

```
@gitko /help          # 도움말
@gitko /review        # 코드 리뷰 (Lubit)
@gitko /improve       # 코드 개선 (Sian)
@gitko /parallel      # 병렬 실행
@gitko /check         # 환경 확인
```

---

## 📊 대시보드 열기

```
Ctrl+Shift+P → 입력:

gitko task      → Task Queue Monitor
gitko perf      → Performance Monitor  
gitko activity  → Activity Tracker
gitko reson     → Resonance Ledger
```

---

## 🛠️ 개발자 도구

```
Ctrl+Shift+P → 입력:

gitko health    → Health Check
gitko diag      → Export Diagnostics
gitko mem       → Memory Stats
gitko test      → Run Integration Tests
```

---

## 📝 PowerShell 스크립트

```powershell
.\test-extension.ps1      # 자동 검증 (F5 전 실행)
.\project-stats.ps1       # 프로젝트 통계
```

---

## 🔧 설정 확인

### VS Code Command Palette

```
Ctrl+Shift+P → "Gitko: Validate Configuration"
```

### Chat에서 확인

```
@gitko /check
```

---

## 🐛 문제 해결

### Output Channel 확인

```
View → Output → "Gitko Extension" 선택
```

### 로그 확인

```
Ctrl+Shift+P → "Gitko: Show HTTP Poller Output"
```

### Health Check

```
Ctrl+Shift+P → "Gitko Dev: Health Check"
```

---

## ⌨️ 키보드 단축키

| 기능 | 단축키 |
|------|--------|
| Command Palette | `Ctrl+Shift+P` |
| Copilot Chat | `Ctrl+Shift+I` |
| Extension 실행 | `F5` (개발 모드) |

---

## 📂 주요 파일 위치

```
설정: .vscode/settings.json
로그: Output Channel → "Gitko Extension"
통계: .\project-stats.ps1
테스트: .\test-extension.ps1
```

---

## 🎯 실전 시나리오

### 시나리오 1: 빠른 코드 개선

```
1. 코드 파일 열기
2. Copilot Chat: "이 코드 개선해줘"
3. ✅ Sian이 자동으로 제안
```

### 시나리오 2: 보안 검사

```
1. @gitko /review
2. ✅ Lubit이 전체 분석
3. 결과 확인
```

### 시나리오 3: 성능 모니터링

```
1. Ctrl+Shift+P → "gitko perf"
2. ✅ 실시간 대시보드 열림
3. 성능 추적
```

---

## 💡 프로 팁

### 1. 자연어가 최고
❌ `@gitko /review --security`
✅ `이 코드에 보안 문제 있는지 확인해줘`

### 2. 구체적으로 요청
❌ `개선해줘`
✅ `이 함수의 성능을 개선하고 가독성도 높여줘`

### 3. 모니터링 습관화
```
작업 전 → Performance Monitor 열기
작업 후 → Activity Tracker 확인
```

### 4. Health Check 정기 실행
```
매일 시작 시 → Health Check
문제 발생 시 → Export Diagnostics
```

---

## 🚨 자주 발생하는 문제

### "Agent가 응답 없음"
```
1. Output Channel 확인
2. @gitko /check 실행
3. Python 경로 확인
```

### "HTTP Poller 작동 안 함"
```
1. Ctrl+Shift+P → "Gitko: Enable HTTP Poller"
2. Task Queue Monitor 확인
```

### "메모리 사용량 높음"
```
1. Ctrl+Shift+P → "Gitko Dev: Show Memory Stats"
2. VS Code 재시작
```

---

## 📞 도움말 리소스

| 문서 | 용도 |
|------|------|
| [QUICKSTART.md](QUICKSTART.md) | 5분 시작 가이드 |
| [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) | 상세 예제 |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | 설정 |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | 배포 |

---

## 🎓 학습 경로

### Day 1: 기본 사용
```
1. F5로 Extension 실행
2. @gitko /help 확인
3. 간단한 코드로 테스트
```

### Day 2: 자동 호출
```
1. Copilot Chat에서 자연어 사용
2. Agent 자동 선택 관찰
3. 다양한 요청 실험
```

### Day 3: 모니터링
```
1. 4개 대시보드 탐색
2. Activity Tracker로 패턴 분석
3. Performance 최적화
```

### Week 2: 고급 기능
```
1. /parallel로 병렬 실행
2. Dev Tools 활용
3. 커스텀 워크플로우 구축
```

---

## 🔍 빠른 검색

**명령어 찾기**: `Ctrl+F` → 키워드 입력

**자주 찾는 것**:
- `health` → Health Check
- `test` → 테스트 실행
- `review` → 코드 리뷰
- `improve` → 코드 개선
- `parallel` → 병렬 실행

---

**이 치트시트를 즐겨찾기 하세요!** ⭐

**Last Updated**: 2025-11-15 | **Version**: v0.3.1
