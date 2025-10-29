# Ledger 품질 지표 필터링 가이드 (2025-10-26 업데이트)

회귀 테스트 시나리오(`integration_test_*`, `low_confidence_test_*`, `temp_low_conf_*`)는 의도적으로 품질 0.4 평가를 남겨 운영 평균을 왜곡합니다. 아래 절차를 따라 테스트 태스크를 운영 지표에서 분리할 수 있습니다.

## 1. `summarize_ledger.py` 필터 옵션 활용
스크립트는 기본적으로 위 세 접두사를 제외하며, 필요 시 `--no-default-excludes`로 해제할 수 있습니다. `--exclude-prefix`를 추가로 지정하면 해당 접두사도 제외됩니다.

```bash
python fdo_agi_repo/scripts/summarize_ledger.py --last-hours 6 \
    --exclude-prefix integration_test_ \
    --exclude-prefix low_confidence_test_ \
    --exclude-prefix temp_low_conf_
```

PowerShell 예시:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python fdo_agi_repo/scripts/summarize_ledger.py --last-hours 6 `
    --exclude-prefix integration_test_ `
    --exclude-prefix low_confidence_test_ `
    --exclude-prefix temp_low_conf_
```

결과 `metrics.avg_quality`는 테스트가 제외된 값으로 계산되며, `notes.exclude_prefixes`와 `notes.default_excludes_applied`로 적용 여부를 확인할 수 있습니다.

테스트 품질을 함께 보고 싶다면 `--no-default-excludes`를 사용하거나, `--exclude-prefix` 인자를 조정하세요.

## 2. 운영 품질 수동 분석(선택)
보다 세밀한 분석이 필요하다면 다음 스니펫으로 테스트 태스크를 제외하고 평균 품질을 직접 계산할 수 있습니다.

```bash
python - <<'PY'
import json, statistics
from pathlib import Path
prefixes = ("integration_test_", "low_confidence_test_", "temp_low_conf_")
ledger = Path("fdo_agi_repo/memory/resonance_ledger.jsonl")
qualities = []
with ledger.open(encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        if data.get("event") != "eval":
            continue
        q = data.get("quality")
        task_id = data.get("task_id")
        if not isinstance(q, (int, float)):
            continue
        if task_id and task_id.startswith(prefixes):
            continue
        qualities.append(q)
print("filtered_avg_quality:", statistics.mean(qualities) if qualities else None)
PY
```

## 3. 대시보드 및 알람 적용
- SQL/쿼리: `WHERE NOT task_id LIKE 'integration_test_%'` 등으로 테스트 태스크 제외
- Ops Dashboard & Alert System: `metrics_collector.py`가 기본 제외 접두사를 자동 적용합니다. 원본 지표가 필요하면 `alert_system.py --no-default-excludes` 또는 `--exclude-prefix` 옵션으로 조정하세요.
- 자동화 파이프라인: CI/배치 워크플로에서 기본적으로 접두사를 제외한 요약을 생성

## 4. 후속 권장 사항
1. `summarize_ledger.py`를 호출하는 모든 자동화(일일 리포트, 알람 등)는 기본 제외가 적용됩니다. 원본 지표가 필요하면 `--no-default-excludes` 플래그를 명시적으로 전달하세요.
2. 필요하다면 테스트 전용 품질을 `metrics.test_task_quality`와 같은 별도 필드로 기록하는 개선을 검토하세요.

이 가이드는 테스트 이벤트가 운영 지표에 미치는 영향을 최소화하기 위한 기준 문서입니다. 접두사 목록이 변경되면 본 문서도 함께 갱신해 주세요.
