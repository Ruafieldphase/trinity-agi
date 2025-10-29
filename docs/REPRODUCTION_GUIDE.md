# Reproduction Guide

이 문서는 NAEDA 연구 패키지를 처음 받은 사용자가 “환경 준비 → 데이터 확보 → 메트릭 산출 → 오케스트레이터 실행 → 리포트 갱신”을 한 번에 끝낼 수 있도록 정리한 체크리스트입니다.

## 1. 환경 준비
1. Python 3.10 이상 (Windows PowerShell 기준).
2. 필수 패키지 설치:
   ```bash
   python -m pip install --user pandas matplotlib langgraph jsonschema notebook
   ```
3. 선택 패키지:
   - `matplotlib` 플롯이 한글 폰트를 찾지 못할 경우, Windows는 기본적으로 Malgun Gothic을 사용합니다.
   - Jupyter Lab을 실행하려면 `python -m jupyter lab`.

## 2. 데이터 및 설정
1. `ai_binoche_conversation_origin/` – 원본 대화 로그.
2. `batch_config.json`, `batch_summary.json`, `batch_boosted.json` – LangGraph 배치 실행 결과.
3. `configs/persona_registry.json` – 정반합 페르소나/백엔드 선언.

## 3. 실행 순서
0. 자동 실행(선택): 아래 명령 하나로 1~5단계를 순차 실행합니다.
   ```bash
   python scripts/run_research_pipeline.py --scenario creative_coach
   ```
   CLI 기반 백엔드가 없는 경우 `--skip-orchestrator` 플래그를 추가하면 페르소나 단계만 건너뜁니다.
   - 시나리오 목록은 `scripts/prompt_scenarios.json`에서 확인/수정할 수 있고, `--prompt "..."` 플래그로 직접 입력해도 됩니다.
   - `claude` 토큰이 만료돼 있으면 자동으로 `local_ollama`(기본값) 백엔드로 전환합니다. 전환을 막으려면 `--force-external`을 추가하세요.

0-1. (옵션) 페르소나 CLI 가용성 점검  
   ```bash
   python scripts/check_persona_backends.py
   ```
   `available: no`로 표시되는 커맨드는 PATH를 수정하거나 `configs/persona_registry.json`에서 백엔드 정의를 원하는 도구로 교체하세요.
   - LM Studio를 도커/VSCode 확장으로 실행 중이라면 `configs/persona_registry.json`의 `"local_lmstudio"` 백엔드를 `python scripts/lmstudio_chat.py --endpoint http://192.168.0.67:8080 --model <모델명>` 형태로 유지하면 됩니다. LM Studio 개발자 페이지에서 사용하는 모델을 Load 해 두고, UI에 표시된 정확한 이름을 `<모델명>` 자리에 넣어 주세요.

1. Phase-injection 데이터셋 생성  
   ```bash
   python scripts/prepare_phase_injection_dataset.py --config batch_config.json --summary batch_summary.json
   ```
2. 시뮬레이션 메트릭 + 그래프  
   ```bash
   python analysis/phase_metrics.py --plots
   ```
3. 대화 다양성 분석  
   ```bash
   python analysis/conversation_diversity.py --input outputs/ai_conversations_combined.csv --plots
   ```
4. 페르소나 오케스트레이션 (샘플)  
   ```bash
   python orchestration/persona_orchestrator.py ^
     --prompt "Design an empathic AI coach for creative writers." ^
     --depth 2 ^
     --config configs/persona_registry.json ^
     --log outputs/persona_runs/session_001.jsonl
   ```
5. 오케스트레이션 로그 요약  
   ```bash
   python analysis/persona_metrics.py outputs/persona_runs/session_001.jsonl --plots
   ```

## 4. 결과 검증
- `outputs/phase_injection/metrics/*.csv` 파일과 `affect_summary.png` 존재 여부 확인.
- `outputs/conversation_metrics/` 하위 CSV/PNG 생성 여부 확인.
- `outputs/persona_runs/*.jsonl`, `outputs/persona_metrics/*.csv` 생성 여부 확인.
- 각 CSV는 Pandas로 열었을 때 NaN/empty가 아닌지 체크:
  ```python
  import pandas as pd
  pd.read_csv("outputs/phase_injection/metrics/affect_metrics.csv").head()
  ```

## 5. 문서 업데이트
- `docs/preliminary_study.md` Results 섹션에 새 메트릭/그래프 반영.
- 로드맵 갱신: `docs/OPEN_ROADMAP.md`.
- 오케스트레이션 사례 추가: `docs/PERSONA_ORCHESTRATION.md` Sample Scenario 표 업데이트.

## 6. 자동화 아이디어
- PowerShell 스크립트나 `invoke`/`make` 명령으로 위 명령들을 순서대로 수행하는 배치 작성.
- GitHub Actions 혹은 로컬 CI에서 `--plots` 제외 버전을 돌려 결과 CSV만 검증.
- Docker/Colab 버전에서는 위 명령을 `ENTRYPOINT` 또는 노트북 셀로 제공.
