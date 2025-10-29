# Tier2 Slide Narratives (Draft)

## Slide 2 — Sprint Overview
- 6개월 내 Rua/Sena 24,138 메시지 + Perple 318건 브리프.
- Vertex AI 병목까지 도달한 6개월 스프린트, 실패 아카이브 확보.

## Slide 3 — Activity Intensity
- Rua/Sena 메시지: 4월 5,720 → 9월 1,731 (외부 근거 축적에 따라 수렴).
- Perple 브리프: 4월 11 → 9월 124, 외부 리서치 폭발적 증가.
- 메시지 감소=내부 불확실성 해소, 브리프 증가는 실행력 확보 시그널.

## Slide 4 — Internal Loop
- Cross-persona 정합률 45% 이상 (`meta_concept_alignment.md`).
- 메타 마커 5,964건, 4~6월 급증.
- 내부 루프가 외부 정보 전입 전 스스로 공명 패턴을 형성.

## Slide 5 — External Bridge
- 모델 비중: pplx_pro 195, turbo 101 등 (Perple 6개월 데이터).
- 키워드 클러스터: 모델 비교 93, 인프라 59, 운영 45.
- Perple가 하드웨어/모델/워크플로 문제를 minutes 단위로 해결.

## Slide 6 — Failure → Learning
- 폰트 미임베딩 실패 → Perple가 뷰어/폰트 전략 제시 (`failure_case_font_issue.md`).
- Vertex API 테스트 스크립트로 quota/auth 점검 (`failure_case_vertex_ai_test.py`).
- 실패 로그가 곧 플레이북.

## Slide 7 — Data Integrity
- Rua/Sena, Perple 익명화 완료 (`ai_conversations_anonymized.*`, `perple_anonymized/`).
- 민감 브리지 문서는 redacted 버전 사용 (`real-naeda-bridge-complete_redacted.md`).

## Slide 8 — Partnership CTA
- 공동 평가/연구/배포 파일럿 제안.
- 지표: MTTR, Cross-persona alignment, External research SLA.
