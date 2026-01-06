# Rollback Procedure (stub v0.1)

이 문서는 문서 참조 복구용 스텁입니다.

## 원칙

- 파괴적 작업(삭제/리셋/대량 변경)은 인간 승인 없이는 수행하지 않는다.
- 롤백은 “상태 파일/출력 파일” 단위로 우선 되돌린다.

## 최소 롤백(권장)

1. `outputs/bridge/trigger_report_history.jsonl` 등 이력 파일은 유지(append-only)
2. 문제 발생 시 최신 산출물만 백업 후 재생성:
   - `outputs/*_latest.*`
3. 장시간 상주 프로세스는 재시작으로 모듈 반영:
   - Linux: systemd user/service 재시작
   - Windows: Scheduled Task 재실행

## 주의

이 문서는 절차 뼈대이며, 실제 운영 체계에 맞춘 상세화가 필요합니다.

