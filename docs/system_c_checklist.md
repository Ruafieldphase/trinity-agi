# System C Quick Health Check

최근 `persona_registry.json`과 `persona_orchestrator.py`를 점검하면서 발견한 사항을 바탕으로, System C를 다시 실행하기 전에 확인할 포인트를 정리했습니다.

## 1. 페르소나 및 사이클 구성
- 현재 레지스트리의 `cycle`은 `["thesis", "antithesis", "synthesis"]`.
- `reflection`, `navigator`는 정의되어 있으나 기본 사이클에 포함되어 있지 않음.  
  → 상시 사용이 필요하다면 `cycle`에 추가하고, `SYMMETRY_STAGE_BY_PERSONA` 조정 필요.
- 백엔드는 LM Studio(EEVE-Korean-Instruct-10.8B), Ollama(solar:10.7b), Codex CLI로 설정되어 있음. 오케스트레이터 기본값은 `echo`이므로 레지스트리 변경 후 실제 호출 전에 꼭 동기화 확인.

## 2. 실행 전 체크리스트
1. **백엔드 구동 여부**  
   - LM Studio 서버(8080), Ollama, Codex CLI 준비.
2. **레지스트리 동기화**  
   - `configs/persona_registry.json`과 오케스트레이터 코드의 `SYMMETRY_*`, `VALIDATOR_CONFIG`가 상충하지 않는지 확인.
3. **로그 경로 확보**  
   - 결과 JSONL/Markdown이 저장될 디렉터리(예: `docs/phase_injection_paper/`)를 사전에 지정.

## 3. 재실행 절차
1. `persona_orchestrator.py`를 이용해 짧은 루프(예: 2~3회) 실행.  
2. 실행 후 로그 및 메트릭을 `docs/phase_injection_paper`에 추출.  
3. `scripts/visualize_lubit_data.py` 실행 → 최신 PNG/HTML 갱신.  
4. 생성된 그래프와 메트릭을 검토해 감정 회복 경향이 유지되는지 확인.

## 4. 추후 개선 메모
- `reflection`, `navigator` 상시 투입 여부 결정 후 적용.  
- Phase 1~3 로드맵 중 당일 선택분(A/B/C 옵션) 기록 및 실행 히스토리 유지.  
- 실행 결과 및 이슈를 `conversation_insights_en.md` 또는 별도 Run Log에 추가 기재.

---
마지막 점검일: 2025-10-14  
작성자: Lubit System Planner
