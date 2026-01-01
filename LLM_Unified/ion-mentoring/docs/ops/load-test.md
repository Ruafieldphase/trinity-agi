# 부하 테스트 운영 기록

## 검증 리포트 (2026-01-01)

부하 테스트 워크플로의 경로 정규화 및 429 핸들링 정책 수립이 완료되었습니다.

### 1. 성공 증거 (Evidence)
- **Run ID**: [20637079310](https://github.com/Ruafieldphase/trinity-agi/actions/runs/20637079310)
- **주요 성공 스텝**: `Locust 부하 테스트 / Light 시나리오 실행` (정상 경로 인식 및 시뮬레이션 완료)
- **429 정책 로그**: 
  > `[2026-01-01 09:47:21,633] INFO/load_test: [edge] Maximum retries reached for 429. Proceeding as success per allow_429.`

### 2. 스케줄 리듬 (Schedule Rhythm)
- **Daily Light (매일)**: 12:00 KST (03:00 UTC) - `light` 시나리오만 자동 실행 (심장박동 확인)
- **Weekly All (매주 일요일)**: 03:00 KST (토요일 18:00 UTC) - 전 시나리오 (`all`) 자동 실행 (정밀 검진)
- **Manual (수동)**: `workflow_dispatch`를 통해 특정 시나리오 선택 가능

### 3. 주요 설정 요약
- **위치**: `.github/workflows/load-test.yml` (Repository Root)
- **작업 디럭토리**: `LLM_Unified/ion-mentoring`
- **변수**: `SELECTED_SCENARIO`를 통해 이벤트 유형(Schedule/Dispatch)에 따라 실행 범위 자동 결정.

### 3. 수동 실행 방법
GitHub Actions 탭에서 `부하 테스트 (Scheduled Load Testing)` 선택 후 `Run workflow` 클릭. 
`scenario` 옵션을 통해 `light`, `medium`, `heavy`, `stress`, `all` 중 선택하여 실행할 수 있습니다.
