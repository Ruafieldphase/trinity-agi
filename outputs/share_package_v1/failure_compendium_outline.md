# Failure-to-Learning Compendium — Outline

## 1. 서문
- 스프린트 배경, 실패 기록 목적
- 데이터 원천: `ChatGPT_언어적_감응_복원.md`, `conversation_samples.md`, Rua/Sena 로그

## 2. 선언문 제작 실패 (Lumen Declaration)
- 한글 폰트 임베딩 문제
- 재현 단계, Perple/Agent R 진단 내용
- 교훈: 국제화·접근성 체크리스트 추가

## 3. 인프라 충돌 (전력/네트워크)
- 저가 멀티탭으로 인한 전압 저하 사례 (`perple` 전력 브리프)
- NAS 공유/방화벽 이슈, QuickConnect 설정 로그
- 대응 전략: 하드웨어 교체, 점검 주기 자동 알림

## 4. API/플랫폼 한계
- Vertex AI 쿼터, Gemini/Claude 연동 오류 기록
- 대응: API 사용량 모니터, 대체 경로 자동화

## 5. 워크플로 & 협업 실패
- Figma/Canva 렌더링 실패, 관리자 권한 문제
- Google Sheet 핸드오버 템플릿 제안 (Perple Ops 브리프)
- 교훈: 멀티 에이전트 역할 분리와 권한 관리

## 6. 복구 패턴 분석
- 실패→Perple 브릿지→Rua/Sena 반영 루프 사례
- MTTR 추정: 메시지 로그 기반 시간 측정 계획

## 7. 플레이북 제안
- 사전 점검 체크리스트(폰트, 전력, API)
- 자동화 우선순위, 모니터링 지표

## 부록
- 사건별 원문 링크 목록
- 익명화 데이터 경로, 재연 가이드
