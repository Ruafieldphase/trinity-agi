# First Operation Test (Particle) Template / 첫 운영 테스트(입자) 템플릿

Use this template before connecting broad infrastructure or running long-lived daemons.

넓은 인프라를 연결하거나 장기 실행 데몬을 실행하기 전에 이 템플릿을 사용하세요.

---

## 1. Operational Pain Point / 운영 문제

What is the one operation you want to improve?

개선하고 싶은 운영 하나는 무엇입니까?

```text
Example:
I manually check publishing status and forget what happened last time.
```

```text
예시:
게시 상태를 수동으로 확인하고 지난번 결과를 잊는다.
```

---

## 2. Shion or Trinity? / Shion인가 Trinity인가?

Choose:

고르세요.

- Shion: the problem is context, intent, memory, or rhythm before action.
- Trinity: the problem is operation, script, status, approval, or local infrastructure.

- Shion: 문제가 행동 전 맥락, 의도, 기억, 리듬에 있다.
- Trinity: 문제가 운영, 스크립트, 상태, 승인, 로컬 인프라에 있다.

---

## 3. Smallest Operation / 가장 작은 운영

What is the smallest useful operation test (particle)?

가장 작게 테스트할 수 있는 운영 테스트(입자)는 무엇입니까?

```text
Example:
Add one status-check command and record the result before scheduling anything.
```

```text
예시:
예약을 하기 전에 상태 확인 명령 하나를 추가하고 결과를 기록한다.
```

---

## 4. Approval Boundary / 승인 경계

Does this operation need human approval?

이 운영은 인간 승인이 필요합니까?

```text
Example:
Publishing public content requires explicit approval.
```

```text
예시:
공개 콘텐츠 게시에는 명시적 승인이 필요하다.
```

---

## 5. Do Not Automate Yet / 아직 자동화하지 않을 것

What should not become a loop yet?

아직 루프로 만들면 안 되는 것은 무엇입니까?

```text
Example:
Do not auto-publish. Only prepare and report.
```

```text
예시:
자동 게시하지 않는다. 준비와 보고까지만 한다.
```

---

## 6. Private Boundary / 비공개 경계

What must remain local or private?

무엇을 로컬 또는 비공개로 남겨야 합니까?

```text
Example:
OAuth tokens, API keys, generated media, private logs, local paths.
```

```text
예시:
OAuth 토큰, API 키, 생성 미디어, 개인 로그, 로컬 경로.
```

---

## 7. Success Signal / 성공 신호

How will you know this helped?

도움이 되었는지 어떻게 알 수 있습니까?

```text
Example:
The next AI cycle can see the operation status without guessing.
```

```text
예시:
다음 AI 사이클이 추측하지 않고 운영 상태를 볼 수 있다.
```
