# Trinity AGI Operation Map / 트리니티 AGI 운영 지도

This map explains how to read the **public repository** without confusing it with a private live operational environment.

이 지도는 공개 저장소를 읽는 방법을 설명합니다. 공개 GitHub를 private live 운영 환경과 동일시하지 않습니다.

## 1. Role / 역할

Trinity is the operation/body boundary for a longer AI workflow.

```text
intent
→ current conditions
→ approval / credentials / target
→ bounded operation
→ readback
→ receipt
```

Shion can preserve context and why an action was formed. Trinity asks whether that action is still valid at the present boundary.

## 2. Current public entry / 현재 공개 진입점

Read first:

- `README.md`
- `OPERATION_CURRENTNESS_CONTRACT.md`
- `REPOSITORY_CURRENTNESS_AUDIT.md`
- `CODE_STATUS.md`
- `AI_READ_THIS_FIRST.md`

These documents define the reading and operation boundary. They do not certify private runtime status.

## 3. Public code surfaces / 공개 코드 표면

The repository preserves several code families from different phases:

| Area | Public status |
| --- | --- |
| `scripts/` | operational helpers and historical/current candidates; inspect before use |
| `agi_core/` | infrastructure and bridge experiments; inspect before use |
| `Pulse_Live_Core/` | prior pulse/observatory/body experiments; not automatically live |
| `lumen_factory/` | media/interpretation utilities; inspect dependencies and targets |
| `.agents/`, `.agent/` | agent/workflow instructions; currentness boundary applies before execution |
| configuration/workflow files | templates or historical operational assumptions unless freshly verified |

A path being in this table does **not** mean every file is obsolete. It means current operational status must be established separately.

## 4. Stale-assumption hotspots / 오래된 가정이 생기기 쉬운 곳

Older code may contain assumptions such as:

- `C:/workspace/agi`
- Windows/Linux sync topology
- fixed localhost ports
- Slack/channel identifiers
- publishing or Moltbook targets
- OAuth/API credentials
- background daemons
- specific local-model/provider routes

These are part of repository history until a current authorized check re-verifies them.

## 5. Historical and conceptual layers / 역사·개념 층

The following material can remain valuable without being current operation authority:

- `PHASE_TRANSITION_MAP.md`
- `LIVE_WORK_ARCHIVE.md`
- `Manifest_Future_Products/`
- older architecture reports and proposals
- scientific/artistic/rhythm-language grounding documents
- previous application and product narratives

Do not rewrite old dates merely to make them look current. Preserve the time axis.

## 6. Auto-start boundary / 자동 시작 경계

`.agents/workflows/auto_start.md` is retained as a **historical disabled recipe**.

No repository file should silently:

- restore permissive approval settings;
- start a daemon;
- initialize a sync route;
- contact a remote target;
- publish content;
- spend quota.

Those actions require current preconditions and the appropriate approval at the action boundary.

## 7. Promotion from history to current use / 역사에서 현재 사용으로 승격

```text
historical component
→ identify exact current need
→ inspect code and side effects
→ verify path / dependency / target / permission
→ read-only check or dry-run
→ bounded execution if justified
→ readback
→ receipt
```

Only the directly verified claim is promoted.

## 8. Public/private boundary / 공개·비공개 경계

Do not commit or infer as public truth:

- credentials
- private local state
- current process secrets
- personal archives
- generated private logs
- live account/session identifiers
- current action permission

The public repository is an **operational history, code surface, and boundary map**. The current authorized environment remains the authority for present execution.

## 9. Relationship to the other repositories / 다른 저장소와의 관계

- `shion-ai` — context, evidence state, re-entry
- `trinity-agi` — operation boundary, current conditions, bounded execution
- `shion-presence` — public discovery/rendering surface, not private operation authority

The separation is intentional. A public metaphor or historical script should not become permission simply by crossing repository boundaries.
