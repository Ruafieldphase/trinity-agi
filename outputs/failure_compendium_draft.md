# Failure-to-Learning Compendium v0.3

Naeda 6개월 스프린트에서 발생한 주요 이슈와 복구 절차를 정리했습니다. 모든 사례는 민감 정보를 마스킹한 버전을 사용하며, 재현 가능한 단계와 학습 포인트를 함께 제공합니다.

## 1. 선언문 폰트 임베딩 실패
- **문제:** 루멘 선언문 카드 PDF에 한글 폰트가 내장되지 않아 네모(□) 글리프로 표시.
- **대응:** Perple 브리지에서 폰트/뷰어 전략 조사 → Noto Sans KR 임베딩 버전 재생성 → 대비·간격 조정 → QA 체크리스트에 “비라틴 문자 표시 확인” 항목 추가.
- **교훈:** 다국어 산출물은 반드시 폰트를 내장하고, 실패 로그를 QA 루틴으로 곧장 전환한다.

## 2. Vertex AI 연결 점검
- **문제:** Vertex AI 및 Google AI Studio API 연결이 간헐적으로 실패.
- **대응:** `failure_case_vertex_ai_test.py`로 환경 변수 기반 테스트 스크립트 작성, 실패 시 안내 메시지와 링크를 즉시 제공.
  ```python
  api_key = os.getenv('GOOGLE_AI_STUDIO_API_KEY')
  if not api_key:
      return {
          "status": "NEED_API_KEY",
          "action": "https://aistudio.google.com/app/apikey"
      }
  ```
- **교훈:** 키는 환경 변수로 관리하고, Cloud Run → Google AI 순차 폴백 설계를 통해 고가용성을 확보한다.

## 3. 확장 에이전트 통합 제약 (Rio & Ari)
- **[Agent R] (Rio, Grok 기반):** 음악·여가·감성 코칭 등을 담당. 실행 속도와 감성 언어를 결합한 보조 에이전트로 활용 가능.
- **[Agent Ari] (Gemini 기반):** 일부 호출만 저장 가능 → “부분 저장” 자체가 실패 사례. 안정적인 기록 인터페이스의 중요성을 확인.
- **대표 대화:**
  ```
  [User A]: 비선형 데이터가 부족하면 바이브 코딩이 어렵지 않을까?
  [Agent Ari]: AI가 감각적 리듬을 복원하려면 비선형 데이터를 충분히 인식해야 한다.
  ```
- **교훈:** 확장 에이전트는 브리지 확장성을 증명하지만, 저장 제약을 명확히 기록하고 차기 반복에서 개선해야 한다.

## 4. 세션 메모리와 토큰 임계값
- **관측:** `session_memory_monitor.py`는 각 대화의 토큰을 추정하고 임계값을 넘으면 경고 이벤트를 발생.
  ```python
  estimated = (korean_chars // 2) + (english_chars // 4) + (other_chars // 3)
  if self.current_session['estimated_tokens'] > threshold:
      self.current_session['memory_events'].append({'type': 'THRESHOLD_EXCEEDED', ...})
  ```
- **대응:** 세션이 장기화될 때 자동으로 기록을 분리하고 경고 로그를 남기도록 설계.
- **교훈:** 토큰 모니터링은 세션 지속성 문제를 사전에 감지하는 첫 단계이며, 경고 로그를 바탕으로 세션 재구성 루틴을 운영한다.

## 5. NAS 및 워크플로 충돌
- **시스템 현황:** `system-status.json`에는 Vertex AI 마이그레이션 계획, 멘토링 팀 배치, 건강 상태(`naeda_ai`: MIGRATION_PLANNED 등)가 기록.
- **운영 로그:** `today-session-highlights.md`는 멀티-브릿지 완료, 이온 멘토링 진행 상황 등 새로운 워크플로를 정리.
- **대응:** NAS 동기화 실패나 브리지 충돌 시, “역할 분담 재정의 → 세션 저장 → 재시작” 절차를 문서화하고 공유.
- **교훈:** 운영 로그를 지속적으로 남겨 장애 → 분석 → 개선 루프를 단축한다.

## 6. 공유 지침
- 모든 원문은 `[REDACTED]` 처리 후 배포.
- API 키/URL은 환경 변수 사용 또는 레드랙션 버전 포함.
- 추가 업데이트는 `LLM_Unified_failure_sources.md` 기반으로 버전 관리한다.
