# NAEDA Open Roadmap

## Near-Term (0–2주)
- 연구 재현 가이드 정리 및 테스트 스크립트 추가 (`invoke` 혹은 PowerShell 기반 실행 워크플로우).
- 정반합 오케스트레이터 로그 → 메트릭 변환 스크립트 도입, 대표 시나리오 2–3개 결과 공유.
- Phase Injection on/off 비교 실험 재실행, affect/freedom/stability 테이블 업데이트.
- 외부 리뷰어용 빠른 시작 노트(환경 설치, 데이터 경고, 실행 체크리스트) 작성.

## Mid-Term (2–6주)
- 경계 언어/Phase Injection 규칙 정교화: affect 범위, 휴먼 인터벤션 포인트 명시.
- Persona 오케스트레이션 다이어그램 및 React 시각화 연동, 로그 기반 트리/타임라인 시각화 자동화.
- Latency·비용·품질 관점에서 로컬/클라우드 LLM 믹스 실측 데이터 축적.
- Docker/Colab 템플릿 제공, PR/이슈 템플릿 마련해 외부 협력 흐름 구성.

## Longer-Term (6주 이상)
- arXiv 초안 완성 및 워크샵 투고 준비.
- UX 실험: 사용 시나리오, 인터랙션 모의, 감정 회복 코칭 데모 영상 제작.
- 데이터·모델 연동 확장(다중 에이전트, 추가 boundary 모듈), 심층 분석 보고서 발간.

## How to Collaborate
1. `docs/PHASE_INJECTION_README.md` 따라 환경 설치 및 기본 메트릭 실행.
2. 새 발견이나 개선 아이디어는 GitHub 이슈 혹은 `docs/OPEN_ROADMAP.md`에 언급된 섹션을 참고해 카테고리 지정.
3. 로그·메트릭 공유 시 `outputs/phase_injection/`·`outputs/persona_runs/` 디렉터리 구조 유지.
4. 실험 결과 요약 시 사용한 퍼소나 설정(`configs/persona_registry.json`)과 실행 명령어를 함께 첨부.
