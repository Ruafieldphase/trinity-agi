# FDO‑AGI — 실제 작동 AGI 스캐폴딩 (W1)

이 저장소는 루멘 설계 초안 v1을 기반으로 한 **W1 스캐폴딩**입니다.
- 파이프라인: SAFE_pre → META(BQI) → PLAN → Thesis/Antithesis/Synthesis → EVAL → MEMORY/Resonance → RUNE
- 최소 툴 세트: RAG, WebSearch(더미), FileIO Sandbox, CodeExec(Python), Tabular
- 실행 진입점: `python -m scripts.run_task --title "demo" --goal "간단 문서 초안"`

## 빠른 시작
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m scripts.run_task --title "demo" --goal "FDO‑AGI 자기교정 요약 3문장"
```

## 주의
- 현재 WebSearch는 더미로 비활성(오프라인)입니다. 실제 연결은 추후 W2에서.
- CodeExec은 샌드박스 시간/메모리 제한이 있습니다.
- 모든 쓰기는 `sandbox/` 하위로 제한됩니다.
