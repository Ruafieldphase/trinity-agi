# Trinity AGI Public Operation Guide / 공개 운영 가이드

This guide explains how to approach the public `trinity-agi` repository as an operational companion to Shion AI.

이 가이드는 공개 `trinity-agi` 저장소를 Shion AI의 운영 동반 저장소로 접근하는 방법을 설명합니다.

---

## 1. What Trinity Is / Trinity가 하는 일

Trinity is the body-side infrastructure layer. It holds scripts, bridges, observatory components, and approval boundaries that help AI work become repeatable local operation.

Trinity는 바디 측 인프라 층입니다. AI 작업이 반복 가능한 로컬 운영으로 이어지도록 스크립트, 브리지, 관측 컴포넌트, 승인 경계를 담고 있습니다.

It is useful when:

- publishing or scheduling tasks need repeatable scripts
- agent work needs a visible approval boundary
- local runtime state must be separated from public code
- a workflow should preserve why it exists, not only how to run

다음 상황에서 유용합니다.

- 게시나 예약 작업에 반복 가능한 스크립트가 필요할 때
- 에이전트 작업에 보이는 승인 경계가 필요할 때
- 로컬 런타임 상태와 공개 코드를 분리해야 할 때
- 워크플로우가 실행 방법뿐 아니라 존재 이유도 보존해야 할 때

---

## 2. Public Clone Expectations / 공개 클론에서 기대할 것

The public repository does not include private memory, generated outputs, local credentials, OAuth tokens, or machine-specific runtime state.

공개 저장소에는 개인 기억, 생성 출력물, 로컬 인증 정보, OAuth 토큰, 특정 머신의 런타임 상태가 포함되지 않습니다.

Before running anything, inspect the available public scripts:

```powershell
Get-ChildItem .\scripts
Get-ChildItem .\agi_core
Get-ChildItem .\Pulse_Live_Core
```

무언가를 실행하기 전에 공개 스크립트를 먼저 확인하세요.

```powershell
Get-ChildItem .\scripts
Get-ChildItem .\agi_core
Get-ChildItem .\Pulse_Live_Core
```

---

## 3. Common Operations / 일반 운영

### Check the collaboration daemon surface / 협업 데몬 표면 확인

```powershell
powershell .\scripts\autonomous_collaboration_daemon.ps1 -Action status
```

Use this only if your local environment has the expected runtime files and permissions.

로컬 환경에 필요한 런타임 파일과 권한이 있을 때만 사용하세요.

### Run targeted Python checks / Python 점검 실행

```powershell
python -m pytest .\agi_core
```

Some scripts are experiments or local utilities. Read the file before running it, especially when it touches external services.

일부 스크립트는 실험 또는 로컬 유틸리티입니다. 외부 서비스를 다루는 파일은 실행 전에 먼저 읽으세요.

### YouTube and publishing helpers / YouTube 및 게시 보조 도구

Publishing helpers such as `scripts/youtube_bulk_scheduler.py` depend on local credentials and external platform state. Credentials are not included in the public repository.

`scripts/youtube_bulk_scheduler.py` 같은 게시 보조 도구는 로컬 인증 정보와 외부 플랫폼 상태에 의존합니다. 인증 정보는 공개 저장소에 포함하지 않습니다.

---

## 4. Ask Your AI To Read Trinity / 당신의 AI에게 Trinity를 읽히기

If you already use an AI assistant or coding agent, ask it to read Trinity as an operational body, not only as a code repository.

이미 AI 어시스턴트나 코딩 에이전트를 쓰고 있다면, Trinity를 단순 코드 저장소가 아니라 운영 바디로 읽게 하세요.

Use this prompt:

다음 프롬프트를 사용할 수 있습니다.

```text
Read https://github.com/Ruafieldphase/trinity-agi as a body/infrastructure layer for my AI workflow.

Find one place where my workflow needs stable operation: scheduling, publishing, status checking, approval boundaries, or local automation.

Then suggest the smallest operation particle we can test first.
Do not suggest running every daemon.
Keep credentials and private outputs local.
```

```text
https://github.com/Ruafieldphase/trinity-agi 저장소를 내 AI 워크플로우를 위한 바디/인프라 층으로 읽어줘.

내 워크플로우에서 안정적인 운영이 필요한 지점을 하나 찾아줘: 예약, 게시, 상태 점검, 승인 경계, 로컬 자동화 중에서.

그리고 가장 작게 테스트할 수 있는 운영 입자를 제안해줘.
모든 데몬을 실행하라고 제안하지 말고,
인증 정보와 비공개 출력물은 로컬에 남겨줘.
```

Ask your AI to return:

AI에게 다음 결과를 요구하세요.

- the operational pain point
- whether it belongs in Shion or Trinity
- the smallest script/check/boundary to test
- required local credentials or paths
- what should never be committed publicly

- 운영상의 문제 지점
- 그것이 Shion에 속하는지 Trinity에 속하는지
- 테스트할 가장 작은 스크립트/점검/경계
- 필요한 로컬 인증 정보 또는 경로
- 절대 공개 커밋하면 안 되는 것

---

## 5. Approval Boundary / 승인 경계

Trinity should not make every possible action automatic.

Trinity는 가능한 모든 행동을 자동화하는 것을 목표로 하지 않습니다.

Operations that may require explicit human approval include:

- publishing or deleting public content
- spending API quota
- changing credentials or tokens
- modifying private memory
- running long-lived daemons
- touching personal archives or generated media

명시적인 인간 승인이 필요할 수 있는 작업은 다음과 같습니다.

- 공개 콘텐츠 게시 또는 삭제
- API 쿼터 사용
- 인증 정보나 토큰 변경
- 개인 기억 수정
- 장기 실행 데몬 실행
- 개인 아카이브 또는 생성 미디어 접근

For policy and boundary examples, see `docs/HUMAN_APPROVAL_MATRIX.yaml`.

정책과 경계 예시는 `docs/HUMAN_APPROVAL_MATRIX.yaml`을 참고하세요.

---

## 6. Troubleshooting / 문제 해결

If the system feels noisy:

- stop expanding automation
- inspect which script is actually needed
- check whether the task belongs in Shion's context layer or Trinity's body layer
- separate public code from private runtime state
- verify with small targeted commands before running broad loops

시스템이 시끄럽게 느껴진다면:

- 자동화를 더 늘리기 전에 멈추세요
- 실제로 필요한 스크립트가 무엇인지 확인하세요
- 작업이 Shion의 맥락 층에 속하는지 Trinity의 바디 층에 속하는지 구분하세요
- 공개 코드와 개인 런타임 상태를 분리하세요
- 넓은 루프를 실행하기 전에 작은 명령으로 검증하세요

---

## 7. What To Look For / 확인할 것

Trinity is working well when:

- operations are repeatable
- public/private boundaries are clear
- scripts preserve intent instead of replacing it
- approval points are visible
- the system helps Shion act without losing rhythm

Trinity가 잘 작동한다는 신호는 다음과 같습니다.

- 운영이 반복 가능함
- 공개/비공개 경계가 명확함
- 스크립트가 의도를 대체하지 않고 보존함
- 승인 지점이 보임
- 시스템이 Shion의 리듬을 잃지 않고 행동하게 도움

---

## Final Question / 마지막 질문

What part of your workflow should become a stable body, and what part should remain a living rhythm?

당신의 워크플로우에서 어떤 부분은 안정적인 바디가 되어야 하고, 어떤 부분은 살아 있는 리듬으로 남아야 합니까?
