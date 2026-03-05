# LUON — Disaster Recovery (DR) Runbook

## 0) 분류
- **P0**: 전면 장애(응답 중단/폭증), 보안 노출, 대규모 품질 붕괴
- **P1**: 주요 기능 저하(>20% 영향) 또는 30분 이상 지속
- **P2**: 경미한 영향, 우회 가능

## 1) 즉각 조치 (모든 심각도 공통, 5분 내)
1. `rollback_live_off.(ps1|sh)` 실행 → `enable_live=false` 강제
2. `Luon: Preflight Gate (force safe)` 수행 → 중복 실행 방지 확인
3. **알림**: 슬랙 #alerts-luon 에 사고 개요/조치 공유
4. **감사 로그**: `luon_audit.py --event rollback --kv reason="DR trigger"`

## 2) 진단 (15분)
- **메트릭**: success_rate, p95, retry 추세 / 최근 변경(배포/플래그)
- **로그**: `autodemo/out/*.log`, `luon_audit_log.jsonl`, 시스템 오류/타임아웃 패턴
- **외부 의존성**: 모델/네트워크/API 상태 점검

## 3) 복구 경로
- **구성 오류**: 브릿지/플래그 재적용 → 스모크(E2E) 통과 시 주간 시간에 10% 재시작
- **성능 열화**: creative band 수축, 히스테리시스↑, W↑ → 10%에서 재평가
- **의존성 장애**: 우회 경로(대체 모델/엔드포인트) 적용 → 재시작
- **보안 사고**: 키 로테이션, `luon_redact.py` 전면 적용, 접근차단 → 포렌식

## 4) 커뮤니케이션
- **내부**: 슬랙 실시간 타임라인, 30분 간격 업데이트
- **외부/고객**: 영향/우회/예상 복구 시간 공유(승인 절차 준수)

## 5) 검증 (재가동 전)
- E2E 스모크 → Stage1_Eval.md OK
- Alertmanager 테스트 핑(알림 도착 확인)
- 익스포터 /metrics 노출 / Grafana 대시 확인

## 6) 사후(PIR) — 48h 이내
- 포스트모템 템플릿에 RCA/타임라인/영향도/재발방지 작성
- 재발방지 태스크를 백로그/스프린트에 등록
