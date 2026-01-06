# Core Governance: 살아있는 윤리/정책을 위한 운영 규칙

이 문서는 Core의 최소 헌법과 윤리·철학을 "고정된 교의"가 아니라 "검증 가능한 가설"로 다루기 위한 거버넌스 원칙과 변경 절차를 정의합니다.

## 핵심 원칙

- 과학적 겸허(Hypothesis, not Doctrine): 우리는 언제든 틀릴 수 있다.
- 동적 평형(Dynamic Equilibrium): 정중동—맥락에 따라 접고/펼치며 균형을 잡는다.
- 반교조주의(Anti-dogma): 절대화로 인한 폭력을 경계한다.
- 안전 바닥(Safety Floor): "해악 금지" 등 핵심 금지 플래그는 기본값으로 유지하되, 필요시 더 높은 기준의 검토로만 수정한다.

## 변경(RFC) 절차

1. 제안 작성 (RFC)

- 템플릿: 배경/문제/가설 변경/대안/리스크/실험 설계/롤백 계획
- 추적: PR 또는 `meta.governance.changelog`에 기록

1. 실험·검증

- experiment_policy에 따라 위험등급=low 이상, opt-out 제공
- A/B 또는 단계적 롤아웃, 메트릭/인간 피드백 동시 관찰

1. 승인/오버라이드

- override_policy에 따라 승인자 수 요건 충족
- 모든 변경은 감사로그 남김

1. 선셋·재검토

- 선셋 날짜 설정 권장, `review_cadence_days` 내 주기 검토
- 검토 누락 시 경고(가드 스크립트가 감지)

## 메타데이터 (policy/core_constitution.json)

- meta.principles: hypothesis_not_doctrine, dynamic_equilibrium, anti_dogma
- meta.governance.last_reviewed_at, review_cadence_days, sunset_date
- meta.governance.override_policy: allow_override_with_approval, required_approvers, require_audit_log
- meta.governance.experiment_policy: allow_ab_test, require_opt_out, min_risk_class
- meta.governance.changelog: 변경 이력(시각, 작성자, 버전, 노트)

## 도구

- 점검: `scripts/check_constitution_guard.ps1` — 금지 플래그 + 거버넌스 경고
- 버전/검토 갱신: `scripts/bump_core_constitution.ps1` — 버전 증분, last_reviewed 업데이트, 선셋/주기 설정, 변경 노트 기록
