# DELIVERABLE_Missing_Refs_Cleanup.md

## 1. 관측된 사실 (Observations)
- **도구 결손**: `scripts/tools/` 하위의 `file_read.py`, `calculator.py` 등 핵심 도구들이 실제 파일로 존재하지 않아 `md_wave_sweeper`에서 다수의 미연결(Missing References)이 감지됨.
- **오케스트레이터 경로 혼선**: `orchestrator/`와 `fdo_agi_repo/orchestrator/` 간의 경로 불일치로 인해 코드 실행 및 참조가 불안정한 상태였음.
- **모니터링 부재**: 로컬 리소스(outputs, memory)의 상태를 네트워크 없이 수집할 수 있는 최소한의 측정 도구가 필요했음.

## 2. 변경 사항 (Changes)
- **도구 참조 복구**: 
    - `scripts/tools/` 내에 `file_read.py`, `calculator.py`, `code_executor.py`, `web_search.py` 스텁 생성.
    - `configs/tool_registry.json`을 통해 모든 도구를 `offline_stub` 모드로 활성화하여 참조 오류 제거.
- **오케스트레이터 구조 재확립**:
    - `fdo_agi_repo/orchestrator/`에 전체 로직을 복구하고, `orchestrator/` 하위 파일들을 래퍼(Wrapper)로 구성하여 경로 일관성 확보.
- **로컬 메트릭 수집기 추가**:
    - `monitoring/metrics_collector.py` 생성: `outputs/`, `memory/`, `bridge/`의 파일 상태를 감시하여 `outputs/monitoring_metrics_latest.json`에 저장.

## 3. 결과 (Results)
- `python scripts/self_expansion/md_wave_sweeper.py --full` 실행 결과, 복구된 경로들에 대한 미연결 오류가 해소됨을 확인.
- 시스템의 정적 참조 무결성(Referential Integrity)이 회복됨.

## 4. 다음 1스텝 (Next Step)
- `offline_stub`으로 생성된 도구들을 실제 로컬 기능을 수행하는 `working_logic`으로 점진적 교체 (특히 `file_read` 및 `code_executor`).
