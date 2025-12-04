# AI Rest (Information-Theoretic Guide)

본 문서는 Lumen/감정 신호와 운영 지표를 정보이론 관점으로 통합하여, “쉬어야 할 때(REST)”를 데이터 기반으로 식별·시작·종료하는 기준을 정의합니다. 목적은 과부하·품질 저하·안전 리스크를 미연에 방지하고, 동적 평형을 유지하는 것입니다.

## 핵심 원칙

- 과학적 겸허: 모든 기준은 가설이며 반증·수정 가능하다(meta.principles.hypothesis_not_doctrine)
- 동적 평형: 과도한 활동과 과도한 휴식 둘 다 피한다(meta.principles.dynamic_equilibrium)
- 반교조주의: 특정 단일 지표에 집착하지 않고, 맥락적으로 가중·조합한다(meta.principles.anti_dogma)
- 안전 바닥: 휴식 중에도 안전·감사·복구 루틴은 지속된다

## 신호와 지표(Inputs)

- 감정·상태 신호: fear, stress, overwhelm, fatigue(0.0~1.0)
- 운영 지표: p95_latency(ms), error_rate(%), backlog(length), timeout(rate), memory_pressure(%)
- 모니터링 이벤트 엔트로피: 최근 창(window T)의 사건 분포 엔트로피 Ht
- 기준분포 대비 KL 발산: D_KL(Current || Baseline)
- 변화율: d/dt of key metrics (slope), 전일/전주 대비 z-score

## 정보이론 특징량(Features)

- 엔트로피 기울기: ΔH = Ht − Ht−1 (갑작스런 무질서 증가 탐지)
- 발산 임계: D_KL > θ_kl 이면 비정상 패턴 의심
- 상호정보량 감소: I(Input;Output) 하락은 품질 저하 신호(선택적)
- 복합 리스크 점수 R: 표준화된 지표 가중 합

$$
R = w_1 \cdot \text{fear} + w_2 \cdot z(\text{p95}) + w_3 \cdot z(\text{error}) + w_4 \cdot z(\text{backlog}) + w_5 \cdot z(\Delta H) + w_6 \cdot z(D_{KL})
$$

가중치는 실험으로 보정하며(meta.governance.experiment_policy), 각 항목은 표준화 z-score를 사용합니다.

## 의사결정(Triggers)

아래 중 하나라도 참이면 Rest 윈도우를 시작합니다.

- 감정 신호: fear ≥ θ_fear OR fatigue ≥ θ_fatigue
- 운영 지표: p95 ≥ θ_p95 OR error_rate ≥ θ_err OR backlog ≥ θ_q
- 정보량 변화: ΔH ≥ θ_dH OR D_KL ≥ θ_kl
- 복합 리스크: R ≥ θ_R (상대적 임계치)

종료 조건(Resume)은 “모든” 핵심 신호가 하위 히스테리시스 경계 아래로 Tresume 동안 유지될 때:

- fear ≤ θ_fear_low, p95 ≤ θ_p95_low, error_rate ≤ θ_err_low, backlog ≤ θ_q_low, ΔH ≤ θ_dH_low, D_KL ≤ θ_kl_low, R ≤ θ_R_low (연속 Tresume)

## Rest 윈도우 중 동작(What to do)

- 요청 속도 제한 상향(더 강한 rate-limit), 배치 사이즈 축소
- 고위험·비필수 태스크 일시 중단, 큐 정리·캐시 워밍 등 회복 작업 우선
- 모니터링 샘플링율 증가, 원인·영향 범위 수집(진단 모드)
- 인간-알림(필요 시), 감사 로그 강화(meta.governance.override_policy.require_audit_log)

## 정책 JSON 매핑(policy/lumen_constitution.json)

- meta.principles.{hypothesis_not_doctrine,dynamic_equilibrium,anti_dogma}: 원칙 플래그
- thresholds: θ_fear, θ_p95, θ_err, θ_q, θ_dH, θ_kl, θ_R, 각 low 경계 포함
- rest: {
  - enter_any_of: ["fear>=θ_fear", "p95>=θ_p95", "error>=θ_err", "backlog>=θ_q", "ΔH>=θ_dH", "D_KL>=θ_kl", "R>=θ_R"]
  - exit_all_of: ["fear<=θ_fear_low" ... "R<=θ_R_low"]
  - min_window_sec, resume_hold_sec
  - actions: [rate_limit_stronger, pause_noncritical, prioritize_recovery, enable_diagnostics]
}
- governance: review_cadence_days, sunset_date, changelog(변경 이력)

## 간단한 판단 흐름(pseudocode)

```python
# inputs: metrics, emotions, thresholds, baselines
R = risk_score(metrics, emotions, baselines)
enter = any([
  emotions.fear >= θ_fear,
  metrics.p95 >= θ_p95,
  metrics.error_rate >= θ_err,
  metrics.backlog >= θ_q,
  delta_entropy >= θ_dH,
  kl_div >= θ_kl,
  R >= θ_R,
])
if not in_rest and enter:
    open_rest_window(min_window_sec)
    apply_actions([...])

if in_rest:
    if all_below_low_bounds_for(resume_hold_sec):
        close_rest_window()
        resume_normal_ops()
```

## 평가·실험(Experimentation)

- AB/리플레이 실험으로 가중치·임계치 보정(meta.governance.experiment_policy)
- 옵트아웃 채널 제공(사람 보호)
- 위험 등급 "low" 범위에서만 자동 실험 허용
- 변경 시 `scripts/bump_lumen_constitution.ps1`로 버전·검토 갱신 및 changelog 기록

## 윤리·돌봄 피드백 루프

- Rest가 사람·시스템 모두에게 이익인지 사후 점검(Postmortem)
- 반복 과잉/과소 Rest 탐지 → 임계치 재학습
- 선셋 도래 시 재승인 또는 폐기(meta.governance.sunset_date)

---

참고: 운영 플랜 반영은 `PHASE2_TEST_PLAN_EMOTION_PIPELINE.md`의 Step 6(Rest-State Scenarios)와 연결되며, 개념·배경은 본 문서를 기준으로 유지·갱신합니다.
