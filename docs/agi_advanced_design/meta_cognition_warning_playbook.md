# 메타인지 저신뢰 경고 대응 플레이북 (2025-10-26 초안)

새로운 Ops Dashboard 위젯 **“Meta-Cognition Signals”**와 연계해 저신뢰 경고(`low_confidence_warning`)가 발생했을 때의 기본 대응 절차를 정리했습니다.

## 1. 경고 발생 사실 확인
- `scripts/ops_dashboard.py` 출력에서 `Low confidence warnings: N` 항목을 확인합니다.
- 경고 비율(`Warning ratio`)이 0에 가깝다면 일시적일 수 있으나, 0.3 이상일 경우 즉시 2단계로 이동합니다.
- `scripts/analyze_recent.py --hours <윈도우>`로 최근 이벤트를 재확인하고, 필요한 경우 `summarize_ledger.py --last-hours <윈도우>`(기본 제외 적용)로 세부 로그 파일(`ledger_summary_latest.*`)을 새로 생성하세요. 원본 지표가 필요하면 `--no-default-excludes`를 함께 사용하세요.

## 2. 원인 분류 체크리스트
1. **도구 토글 상태 확인**
   - 환경 변수: `WEBSEARCH_DISABLE`, `RAG_DISABLE`, `CODEEXEC_DISABLE` 등을 점검합니다.
   - `orchestrator/tool_registry.py`는 플래그 값에 따라 도구를 제외하므로, 불필요한 비활성화가 없는지 확인합니다.
2. **네트워크/외부 API 상태**
   - Ops Dashboard의 Core/Proxy 상태가 비정상이면 먼저 연결 문제를 해소합니다.
   - 외부 검색 엔드포인트 사용 시, HTTP 429/5xx 응답이 없는지 로그를 살펴봅니다.
3. **태스크 스코프 적합성 검토**
   - 경고 대상 `task_id`와 `goal`을 Ledger에서 찾아 사람이 해결해야 하는 주제인지 판단합니다.
   - 이미 테스트/시뮬레이션 태스크라면(예: `low_confidence_test_*`) 영향 범위를 운영 지표에서 제외합니다.

## 3. 대응 선택지
| 상황 | 조치 |
| --- | --- |
| 도구 비활성화가 의도된 테스트 | 영향도를 메모리에 기록하고, 운영 지표 산출 시 제외 |
| 도구/네트워크 장애 | 관련 서비스 재시동 또는 플래그 복구 후 동일 태스크 재실행 |
| 본질적으로 사람이 필요한 태스크 | 메타인지 결과를 받아들여 수동 핸드오프, 또는 프롬프트/권한을 조정 |

## 4. 후속 문서화
- 경고가 1회 이상 발생한 경우 `docs/` 하위에 날짜별 노트를 남겨 패턴을 축적합니다.
- 재발 가능성이 있는 유형은 `OPERATIONS_RUNBOOK.md` 또는 관련 서비스 플레이북에 반영합니다.

## 5. 자동화 개선 아이디어
- 회귀 테스트처럼 경고가 의도된 경우, 태스크 ID 접두사 기준으로 대시보드 경고 카운터에서 제외하는 옵션을 추가합니다.
- `summarize_ledger.py`는 기본적으로 회귀 테스트 접두사를 제거합니다. 추가 제외가 필요하면 `--exclude-prefix`, 원본 비교가 필요하면 `--no-default-excludes` 옵션을 활용하세요.

> **참고**: 본 플레이북은 초안입니다. 루빛이 현장 운영 중 발견한 케이스를 반영해 주기적으로 갱신해 주세요.
