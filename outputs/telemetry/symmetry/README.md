# Symmetry Telemetry

이 경로는 퍼소나 오케스트레이터 실행 로그에서 추출한 대칭 텔레메트리(JSONL/CSV)를 보관하기 위한 저장소입니다.

## 기록 규칙
- 파일 이름은 session_<date>_<slug>.jsonl 형태로 저장하세요.
- 각 레코드는 symmetry_stage, esidual_symmetry_delta, symmetry_tension, symmetry_decision 필드를 포함해야 합니다.
- 실험(E1~E3) 실행 후에는 대응되는 노트(예: E1_residual_band_notes.md)를 함께 추가해 정성 메모를 남깁니다.

## 활용 체크리스트
1. nalysis/persona_metrics.py --symmetry로 요약 CSV와 밴드 점유율을 생성합니다.
2. 생성된 CSV는 outputs/persona_metrics/ 아래에 자동 저장되며, 시각화 PNG는 동일 경로에 출력됩니다.
3. 창의 밴드(0.15~0.35)에 위치한 턴은 후속 세션 설계 시 재사용 후보로 태깅합니다.

