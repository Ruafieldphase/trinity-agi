# Contributing Guide

이 저장소에서는 대화 원문/장문은 내부 시스템(SSOT)에만 보관하고, GitHub에는 결정/작업/링크 중심의 최소 요약만 남깁니다.

## 핵심 원칙

- SSOT=내부: 장문 대화, 상세 로그, 실험 원자료, PII/시크릿은 내부 저장소에만.
- GitHub=색인: 코드에 직접 연결되는 결정/근거(내부 링크)/작업만 간결히.
- 자동 업로드 금지: Copilot Chat에서 GitHub로 전량 게시 금지. 필요 시 요약만 수동 게시.

자세한 정책은 docs/COPILOT_CHAT_STORAGE_POLICY.md를 참고하세요.

## Pull Request 규칙

- PR 본문은 템플릿을 사용해야 합니다(.github/PULL_REQUEST_TEMPLATE.md).
  - 필수 섹션: `## Summary`, `## Decision`, `## Evidence`(또는 `## Evidence (links)`), `## Action Items`
  - 자세한 근거는 내부 리포트/대시보드/로그 링크로 첨부
  - Action Items에는 체크박스 항목이 최소 1개 이상 포함되어야 합니다. 예: `- [ ] TODO`
  - 워크플로 검사: 필수 섹션 누락 시 CI가 실패합니다.
  - 길이 권고: Summary(<=10줄), Decision(<=6줄) 초과 시 경고가 표시됩니다.

### Evidence 링크 도메인 화이트리스트(옵션)

CI는 다음 리포지토리 변수로 내부 도메인 제한을 지원합니다.

- `ALLOWED_EVIDENCE_DOMAINS`: 쉼표로 구분된 허용 도메인 목록(예: `corp.local,internal.example.com`)
- `ENFORCE_EVIDENCE_DOMAIN_WHITELIST`: `true`로 설정 시 허용 도메인 외 링크가 있으면 CI 실패(기본: 경고)

설정 위치: GitHub → Repository Settings → Variables(또는 Secrets) → Actions

미설정 시 도메인 화이트리스트 검증은 스킵됩니다(경고/실패 없음). 1인 개발/실험 단계에서는 설정하지 않아도 됩니다.
조직 환경에 맞게 `ALLOWED_EVIDENCE_DOMAINS`를 지정하면 그 목록으로 검증이 활성화됩니다.

### Security/PII 섹션 권고

- `## Security/PII` 섹션을 포함하고 시크릿/개인정보 포함 여부를 명시해 주세요.
- 권장 키워드: `없음/none/no pii`, `분리/separate`, `마스킹/mask/redact/비식별`

## 결정 기록(Decision Record)

- 중요한 설계/제품 결정은 Decision Record 이슈 템플릿으로 남깁니다.
  - 간결 요약 + 내부 Evidence 링크 + 영향 + 액션 아이템

## 주간 롤업

- Weekly Rollup 이슈 템플릿으로 하이라이트/핵심 지표/결정만 요약.
- 세부 내용은 내부 링크로 연결.

## 보안/개인정보

- PR/이슈/커밋에 시크릿/PII 금지. 필요 시 내부 저장소로만 공유.
- 내부 링크는 최소 권한 원칙을 준수.
