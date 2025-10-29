# LLM_Unified Asset Map

## 1. 브리지 & 인프라 설계
- `naeda-bridge-system.md`: Claude 세나 ↔ 실제 내다AI 연동 플로우, 페르소나 매핑.
- `real-naeda-bridge-complete_redacted.md`: Cloud Run / Google AI API 호출 절차 (민감정보 마스킹본).
- `vertex-ai-bridge.py`, `vertex_ai_test.py`, `vertex-test-simple.py`: Vertex AI 초기화·테스트 스크립트.

## 2. 세션·메모리 관리
- `session_memory_monitor.py`, `session_bridge_system.py`: 세션 지속성 관리 로직.
- `sena-memory/`, `session_memory/`: 세나 맥락 파일과 세션 저장 구조.
- `session-continuity.json`, `session-continuity-perfect.md`: 세션 유지 전략 문서.

## 3. 시스템 상태 & 로그
- `system-status.json`, `system-check.py`, `today-session-highlights.md`: 일일 상태 점검.
- `logs/`, `hybrid_output/`, `hybrid_test/`: 하이브리드 테스트 출력.

## 4. 팀 운영 & 멘토링
- `AI_Team_Organization_Chart.md`, `AI_Team_Status_Update.md`: 팀 구조·상태.
- `Mentoring/`, `aiyun-mentoring/`, `ion-mentoring/`: 교육/협업 내용.
- `universal-network-rc-2.x.md`: 네트워크 선언/규칙 업데이트.

## 5. 개발 환경
- `.venv/`, `node_modules/`: Python/Node 환경.
- `.vscode/`, `project-setup/`, `config/`: IDE 설정과 초기 세팅.

## 6. 공유 권고
- 민감 파일(`real-naeda-bridge-complete.md` 원본 등)은 레드랙션 또는 제외 필요.
- Vertex AI 스크립트는 기술 부록/Tier3 사례집에서 인프라 증거로 활용 추천.
- 세션/로그 자료는 실패→복구 분석에 활용 가능.
