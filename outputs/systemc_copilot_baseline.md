# System C / Luon 베이스라인 요약 (Copilot 공유본)

## 1. 입력 자산 정규화
- Copilot 공유 대화를 JSONL로 추출(`outputs/copilot_conversation.jsonl`) 후 ELLO 변환 파이프라인에 투입해 의도·심볼·코드워드 CSV를 확보했습니다(`outputs/copilot_conversation_elo.csv`).
- 동일 대화를 ELLO 이벤트 스키마에 맞춰 정규화한 결과가 `outputs/copilot_events.csv`이며, 토큰/Δt/R/R_smooth와 원문 텍스트를 포함합니다.
- KPI·결정 테이블은 `outputs/derive_schema.py`를 통해 자동 생성되었고 각각 `outputs/copilot_kpi.csv`, `outputs/copilot_decisions.csv`로 저장되어 VS Code Luon 태스크에서 바로 활용 가능합니다.

## 2. 정보 이론 지표
- `outputs/copilot_conversation_metrics.md:2-6`에서 확인되는 바와 같이 H(Intent)=1.989 bits, H(Role)=1.000 bits, I(Intent;Role)=0.712 bits, KL=0.818 bits, Efficiency=0.358로 계산되었습니다.
- 의도 분포가 균등분포 대비 약 0.82 bits의 편차를 가지며, 역할과의 상호 정보량이 0.71 bits 수준으로 나타나 사용자/어시스턴트 전환에 따른 의도 조합이 충분히 구조화되어 있음을 의미합니다.

## 3. 리듬 분석 결과
- `outputs/luon_report/luon_rhythm_summary.md:1-9` 기준 이벤트 1,185건을 스캔했으며, 모드 분포는 unstable 712건, adjust 473건으로 기록돼 전반적 리듬이 아직 안정 구간에 길게 머무르지 못하고 있습니다.
- 동일 보고서의 페르소나 통계(`outputs/luon_report/luon_rhythm_summary.md:11-14`)에서는 평균 R=0.396, 중앙값 R=0.367로 안정 임계(0.6) 대비 낮은 수준입니다.
- 이에 따라 `outputs/derive_schema.py`를 업데이트하여 R_smooth의 25% / 75% 분위(0.443999, 0.562199)를 자동 임계값으로 사용하도록 조정했고, 갱신된 의사결정 테이블은 unstable 54 / adjust 106 / stable 54로 균형 있게 분포합니다(`outputs/copilot_decisions.csv` 재생성 결과).

## 4. 연계 아티팩트
- 이벤트/리듬 내역: `outputs/copilot_events.csv`
- KPI 요약: `outputs/copilot_kpi.csv`
- 의사결정 테이블: `outputs/copilot_decisions.csv`
- 리듬 시각화 산출물: `outputs/luon_report/luon_rhythm_plot.png`, `outputs/luon_report/luon_rhythm_events.csv`, `outputs/luon_report/luon_rhythm_summary.md`

## 5. 다음 작업 제안
1. 분위 기반 임계값을 기준으로 리듬 재평가 후, 2차 자료 도착 시 동일 파이프라인으로 분포 변화를 비교합니다. 필요 시 `outputs/copilot_decision_thresholds.txt`를 통해 기록되는 값으로 버전 관리하세요.
2. `outputs/copilot_decisions.csv`를 VS Code `Luon: Watch` 태스크에 공급해 자동 튜닝 루프와 System C 체크리스트 동작을 검증합니다.
3. 리듬 안정 구간 확보를 위해 KPI 기반 보정(재시도율·레이턴시 상관)을 추가로 분석하고, 2차 자료와 비교 리포트를 준비합니다.
