# Integration Anti-Patterns / 잘못된 통합 방식

These are the common ways to lose the meaning of Trinity AGI while trying to use it.

Trinity AGI를 사용하려다가 오히려 의미를 잃는 흔한 방식들입니다.

---

## 1. Run Everything First / 전부 먼저 실행

Bad pattern:

나쁜 패턴:

```text
Start every daemon and script, then see what happens.
```

Why it fails:

왜 실패하는가:

It creates noise before the user knows which operation is being tested.

어떤 운영을 테스트하는지 알기 전에 소음부터 만듭니다.

Better:

더 나은 방식:

```text
Diagnose one operational pain point, then test one operation test (particle).
```

---

## 2. Scripts Without Intent / 의도 없는 스크립트

Bad pattern:

나쁜 패턴:

```text
Copy this script into my workflow because it exists.
```

Why it fails:

왜 실패하는가:

Scripts should embody a formed intention. If the intention is unclear, the script becomes more work.

스크립트는 형성된 의도를 몸으로 옮기는 것입니다. 의도가 불명확하면 스크립트는 또 다른 일이 됩니다.

---

## 3. Automation Without Approval / 승인 없는 자동화

Bad pattern:

나쁜 패턴:

```text
Automatically publish, delete, schedule, or spend API quota.
```

Why it fails:

왜 실패하는가:

Some operations must stay approval-gated. Automation should not remove the user's boundary.

일부 운영은 승인 경계 안에 있어야 합니다. 자동화가 사용자의 경계를 지우면 안 됩니다.

---

## 4. Status By Assumption / 상태를 가정으로 처리

Bad pattern:

나쁜 패턴:

```text
Assume the daemon is running because it was started before.
```

Why it fails:

왜 실패하는가:

Runtime state changes. Status should be checked from current evidence.

런타임 상태는 바뀝니다. 상태는 현재 증거로 확인해야 합니다.

---

## 5. Public Repo As Private Runtime / 공개 저장소를 개인 런타임으로 사용

Bad pattern:

나쁜 패턴:

```text
Commit credentials, generated logs, local paths, or private outputs.
```

Why it fails:

왜 실패하는가:

The public repo is an orientation and code surface, not a storage place for private runtime state.

공개 저장소는 안내와 코드 표면이지, 개인 런타임 상태를 저장하는 곳이 아닙니다.

---

## 6. Body Replaces Rhythm / 바디가 리듬을 대체

Bad pattern:

나쁜 패턴:

```text
If the script can run, it should run.
```

Why it fails:

왜 실패하는가:

Trinity is a body layer. It should support the rhythm, not replace it with constant action.

Trinity는 바디 층입니다. 리듬을 지탱해야지, 지속적 행동으로 리듬을 대체하면 안 됩니다.
