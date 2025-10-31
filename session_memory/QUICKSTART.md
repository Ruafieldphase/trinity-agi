# Session Memory System - Quick Start Guide

## 🎯 30초 요약

```powershell
# 1. 세션 시작
chatops_router.ps1 -Say "세션 시작해"

# 2. 과거 작업 찾기
chatops_router.ps1 -Say "지난번에 뭐 했지?"

# 3. 키워드 검색
chatops_router.ps1 -Say "BQI 작업 찾아줘"

# 4. 세션 종료
chatops_router.ps1 -Say "세션 종료"
```

## 📋 핵심 명령어 (자연어)

| 한국어 | 영어 | 설명 |
|--------|------|------|
| 세션 시작해 | start session | 새 작업 세션 시작 |
| 작업 추가 | add task | 현재 세션에 작업 추가 |
| 세션 종료 | end session | 세션 종료 (resonance 점수 입력) |
| 지난번에 뭐 했지? | what did I do? | 최근 10개 세션 보기 |
| BQI 작업 찾아줘 | find BQI work | "BQI" 키워드 검색 |
| 활성 세션 | active sessions | 진행중인 세션 확인 |
| 세션 통계 | session stats | 페르소나별 통계 |

## 🚀 첫 세션 만들기

### PowerShell에서

```powershell
cd C:\workspace\agi
.\session_memory\session_tools.ps1 start "My First Session"
.\session_memory\session_tools.ps1 task "Learn session memory"
.\session_memory\session_tools.ps1 end 0.9
```

### ChatOps로 (자연어)

```powershell
chatops_router.ps1 -Say "세션 시작해"
# Title 입력: My First Session

chatops_router.ps1 -Say "작업 추가"
# Task 입력: Learn session memory

chatops_router.ps1 -Say "세션 종료"
# Resonance (0-1) 입력: 0.9
```

## 🔍 검색 예제

```powershell
# 최근 작업 (자연어)
chatops_router.ps1 -Say "지난번에 뭐 했지?"

# 키워드 검색 (자연어)
chatops_router.ps1 -Say "ChatOps 작업 찾아줘"

# 직접 검색 (고급)
.\session_memory\session_tools.ps1 search "machine learning"
.\session_memory\session_tools.ps1 by-file "chatops_router.ps1"
```

## 📊 상태 확인

```powershell
# 활성 세션
chatops_router.ps1 -Say "활성 세션"

# 통계
chatops_router.ps1 -Say "세션 통계"

# 최근 작업
.\session_memory\session_tools.ps1 recent 5
```

## 💾 데이터 위치

- **Database**: `C:\workspace\agi\session_memory\sessions.db`
- **Log**: `C:\workspace\agi\session_memory\session_log.jsonl`
- **Exports**: `C:\workspace\agi\session_memory\outputs\`

## 🧪 테스트

```powershell
cd C:\workspace\agi\session_memory
python test_session_memory.py
# Expected: ✅ All tests passed!
```

## 📚 자세한 문서

→ `C:\workspace\agi\session_memory\README.md` (470 lines, 완전 가이드)

## 🎉 완료

이제 작업을 잃어버리지 않습니다! 🚀

**Phase 1 (완료) - 5/9 tasks:**

- ✅ Database schema (FTS5)
- ✅ Core logger (JSONL + SQLite)
- ✅ Search tool (CLI)
- ✅ PowerShell wrapper
- ✅ ChatOps integration

**Phase 2 (다음 단계) - 4/9 tasks:**

- ⏳ Resonance Ledger 연동
- ⏳ VS Code 파일 모니터링
- ⏳ Daily Summary 자동 생성
- ⏳ 추가 고급 기능

---

**Created**: 2025-10-29  
**Status**: ✅ Production Ready  
**Test Coverage**: 6 test suites, all passing
