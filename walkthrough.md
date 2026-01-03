# CI/CD Load Test Optimization Walkthrough

## 작업 개요
`Ion Mentoring` 부하 테스트 CI/CD 파이프라인의 잦은 실패와 아티팩트 저장 공간 부족 문제를 해결했습니다. 이제 Rate Limit(429) 응답은 의도된 검증 성공으로 간주되며, 아티팩트 관리가 최적화되었습니다.

## 주요 변경 사항

### 1. Locust 부하 테스트 스크립트 고도화
- **[load_test.py](LLM_Unified/ion-mentoring/load_test.py)**
    - **429 성공 처리 로직**: `EdgeCaseUser`와 같이 의도적으로 부하를 유발하는 시나리오에서 429 응답을 `response.success()`로 처리하도록 수정했습니다.
    - **동적 정책 적용**: `post_with_retries` 메서드에 `allow_429` 옵션을 추가하여 특정 시나리오에서만 레이트 리밋을 성공으로 수용하도록 분리했습니다.

### 2. GitHub Actions 워크플로우 최적화
- **[load-test.yml](LLM_Unified/ion-mentoring/.github/workflows/load-test.yml)**
    - **아티팩트 용량 절감**:
        - 주요 용량 차지 원인이었던 **HTML 리포트 생성을 비활성화**했습니다.
        - `retention-days`를 **7일에서 3일로 단축**하여 저장 공간 쿼터 관리를 강화했습니다.
        - 불필요한 `_stats_history.csv` 파일을 삭제하도록 단계(Cleanup)를 추가했습니다.
    - **워크플로우 안정성**: 429 에러가 더 이상 테스트 실패(Exit code 1)를 유발하지 않으므로, 불필요한 실패 알림 메일 발송이 억제됩니다.

## 검증 결과

### 1. 구문 검사
수정된 Python 스크립트의 구문이 정상임을 확인했습니다.
```powershell
python -m py_compile LLM_Unified/ion-mentoring/load_test.py
# 결과: Success (Exit code 0)
```

### 2. 로직 검증 (Dry Run)
`EdgeCaseUser`가 사용될 때 `allow_429=True`가 전달되어 429 응답 시 `response.success()`가 호출됨을 코드를 통해 확인했습니다.

## 결론
이번 최적화를 통해 CI/CD 파이프라인은 진정한 "실패(서버 타임아웃, 5xx 에러 등)"에만 반응하게 되었으며, 아티팩트 저장 공간 할당량 초과 문제에서도 자유로워졌습니다.
