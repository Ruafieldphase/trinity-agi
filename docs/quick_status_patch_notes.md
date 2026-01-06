# quick_status.ps1 개선 요약 (2025-11-08)

본 패치는 운영 중 관찰된 몇 가지 안전성/관측성 이슈를 경량하게 개선합니다.

## 변경 사항

- Null-세이프 카운팅
  - 경고/이슈 판정 시 Null 요소로 인한 예외을 차단하여 로깅/알림 경로의 안정성 향상
  - 예: `$hasWarns`/`$hasAlerts` 계산 시 빈 배열 폴백 적용
- JSON 출력 품질 향상
  - `-OutJson` 저장 시 `ConvertTo-Json -Depth 10 -Compress`로 중첩 데이터 손실 방지
  - 스냅샷에 `Perf`/`Goals` 동적 주입(소스 파일이 존재할 때만)
    - Perf: EffectiveSuccess, OverallSuccess, Systems, ExcellentAt, GoodAt 등
    - Goals: ActiveCount, Completed24h, Failed24h, CompletionRate24h 등
- JSONL 로깅 안정성 강화
  - 라인 종료(줄바꿈) 보장, UTF-8 안전성 유지(폴백 경로 포함)

## 사용 방법

- 대시보드/로그 생성(예시)

```powershell
# 24시간 리포트 + JSON 저장
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quick_status.ps1 -OutJson outputs/quick_status_latest.json

# 경고 시 콘솔 경고 및 JSONL 로그 기록
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quick_status.ps1 -AlertOnDegraded -LogJsonl -OutJson outputs/quick_status_latest.json
```

## 검증

- 스모크 테스트 스크립트 추가: `scripts/test_quick_status_output.ps1`

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test_quick_status_output.ps1 -OutPath "$env:TEMP\quick_status_test.json"
```

- 기본 필드(Online/Channels/Timestamp) 확인 및 존재 시 Goals/Perf 블록 확인

## 다음 단계 제안(소형)

- `-LogJsonl` 라인에 선택적 스냅샷 확장(Perf/Goals) 삽입 토글 추가(예: `-EnrichSnapshot`)
- PSScriptAnalyzer 룰 적용(명령형 동사 준수 등) 및 CI 워크플로에 추가
- 경고/이슈 메시지 카테고리 표준화로 대시보드 필터링 품질 개선
