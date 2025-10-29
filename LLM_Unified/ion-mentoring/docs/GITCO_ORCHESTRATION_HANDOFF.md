# Gitco 오케스트레이션 핸드오프

**작성자**: 루빛  
**작성일**: 2025-10-21

---

## 1. 최신 통합 요약

- **PersonaPipeline**  
  - Phase Injection & RUNE 품질 검증이 기본 활성화됨 (`persona_pipeline.py`).  
  - API 응답의 `metadata` 항목에 `phase` 및 `rune` 키가 추가되므로, 운영 지표 수집 시 해당 값을 그대로 활용 가능.
- **PhaseInjectionEngine**  
  - 280초 주기의 페이즈 회전과 BQI(Beauty/Quality/Impact) 추정치를 제공 (`phase_injection.py`).  
  - `metadata["phase"]["phase_label"]`을 지표 태그로 삼아 페이즈 변화를 모니터링.
- **RUNEIntegration**  
  - 고품질 응답을 유도하고 필요 시 자기 교정을 수행 (`rune_integration.py`).  
  - `metadata["rune"]["overall_quality"]`가 기준치(기본 0.7)를 하회하면 `rune_result.regenerate` 플래그가 `True`로 설정되어 재생성이 수행됨.
- **테스트 보강**  
  - `tests/test_rune_integration.py`, `tests/test_phase_injection.py`에서 통합 동작을 검증.  
  - 명령: `python -m pytest tests/test_rune_integration.py tests/test_phase_injection.py`

## 2. Gitco 운영 체크리스트

1. **엔드포인트 점검**
   - `app/main.py`의 `/chat` 엔드포인트 호출 후 응답 JSON에 `metadata.phase`, `metadata.rune`가 포함되는지 확인.
   - `metadata.rune.overall_quality < 0.7` 사례를 캡처하여 알림/대시보드에 연동.

2. **배포 전 테스트**
   - 로컬 또는 CI에서 `python -m pytest tests/test_rune_integration.py tests/test_phase_injection.py` 실행.
   - 추가로 기존 `tests/test_agi_integration.py`를 함께 실행하여 Memory/Tool 통합 회귀 여부 확인.

3. **모니터링 지표 연동**
   - Phase Snapshot  
     - 로그: `metadata.phase.phase_label`, `metadata.phase.timestamp`  
     - 지표: 페이즈 체류 시간, 페이즈 전환 빈도
   - RUNE 품질  
     - 로그: `metadata.rune.overall_quality`, `metadata.rune.regenerate`  
     - 지표: 품질 점수 분포, 재생성 발생률
    - 메타데이터 분석: python scripts/analyze_chat_metadata.py --input responses.jsonl
      * 샘플 데이터: samples/chat_responses_sample.jsonl
    - 일일 리포트 스케줄러 등록: powershell.exe -ExecutionPolicy Bypass -File scripts/register_daily_report_task.ps1 -ReportScriptPath "<경로>\generate_daily_report.ps1"
    - GCP 대시보드 생성: powershell.exe -ExecutionPolicy Bypass -File monitoring/create_simple_dashboard.ps1 -ProjectId "naeda-genesis"

4. **비상 대응 루틴**
   - 품질 점수가 지속적으로 하락하거나 페이즈가 고정될 경우 `rune_integration.py` 설정(quality_threshold) 조정 여부 검토.
   - 필요 시 `IONRUNEIntegration(enable_rune=False)`로 전환하여 RUNE 루프를 임시 비활성화 후 문제 분석.

## 3. 협업 절차 제안

| 단계 | 루빛 | 깃코 |
| --- | --- | --- |
| 사전 준비 | 코드/테스트 업데이트 공유 | 배포 체크리스트 확인 |
| 배포 | 새 테스트 스위트 결과 전달 | Canary → Prod 단계별 배포 |
| 운영 | RUNE/Phase 로그 제공 | 로그 수집 및 알림 설정 |
| 회고 | 개선 필요 항목 정리 | 알림/모니터링 튜닝 |

## 4. 후속 액션

- 깃코: 상기 체크리스트를 배포 파이프라인 문서(Phase4)와 CI 스크립트에 반영.
- 루빛: RUNE 및 Phase 엔진의 설정값(주기, threshold)을 실사용 데이터에 따라 조정하고 공유.
- 공동: 품질·페이즈 로그를 기반으로 다음 주 운영 회의에서 개선 포인트 점검.

---

> 협업에 필요한 추가 정보가 생기면 이 문서를 확장하거나 `PHASE4_배포_준비_최종_체크_2025-10-21.md`에 통합해 주세요.
