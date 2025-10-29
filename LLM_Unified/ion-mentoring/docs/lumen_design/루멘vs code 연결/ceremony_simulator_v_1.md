# Ceremony Simulator v1.0  
**(Training Scenarios + TUI + Rehearsal Logs + Scoring)**

목적: Root Custody 의식을 **훈련/리허설**할 수 있도록 시나리오·퀴즈·채점·로그 생성을 제공한다. 오프라인 의식 절차를 안전하게 익히고, 실수/이상 상황 대응력을 높인다.

---

## 0) 디렉터리
```
.
├─ custody/sim/
│  ├─ scenarios.yaml          # 훈련 시나리오 정의
│  ├─ quiz_bank.json          # 객관/주관 퀴즈 문항
│  ├─ simulator.py            # TUI 시뮬레이터(오프라인)
│  ├─ rehearse.py             # 리허설 실행/기록 생성기
│  ├─ scorer.py               # 채점/리포트
│  ├─ inject_anomaly.py       # 이상 상황 생성(봉인 손상 등)
│  └─ artifacts/              # 생성된 리허설 로그/증빙
└─ .vscode/tasks.json         # run-sim / run-quiz / score
```

---

## 1) 시나리오 정의 — `scenarios.yaml`
```yaml
version: 1
scenarios:
  - id: initial_setup_happy
    title: "초도 의식 — 정상 흐름"
    steps:
      - check_airgap
      - generate_root
      - print_fingerprint
      - seal_packets
      - store_safe_A
      - store_safe_B
    anomalies: []
  - id: offline_signing_expired_token
    title: "오프라인 서명 — 토큰 만료 대응"
    steps: [boot_airgap, unseal, load_root, sign_crl, reseal]
    anomalies:
      - type: token_expired
        message: "서명자 토큰 만료, CRL 업데이트 필요"
  - id: quarterly_audit_torn_seal
    title: "분기 점검 — 봉인 훼손 감지"
    steps: [check_seal, photo_hash, crosscheck_logs]
    anomalies:
      - type: torn_seal
        message: "봉인 스티커 절취 흔적 발견"
```

---

## 2) 퀴즈 문항 — `quiz_bank.json`
```json
{
  "multiple_choice": [
    {
      "id": "mc_airgap",
      "q": "루트 키가 사용되는 장소로 올바른 것은?",
      "choices": ["CI 러너", "개발자 노트북", "에어갭 장치", "프로덕션 서버"],
      "answer": 2
    },
    {
      "id": "mc_dual",
      "q": "이중 통제(Dual Control)의 핵심은?",
      "choices": ["2인이 항상 같은 비밀번호 공유", "2인의 분리된 권한/승인", "한 사람이 두 역할 수행", "1인 승인"],
      "answer": 1
    }
  ],
  "short_answer": [
    {"id":"sa_crl","q":"CRL에 기록해야 하는 핵심 필드를 2가지 쓰세요."}
  ]
}
```

---

## 3) 시뮬레이터 — `simulator.py` (TUI)
```python
#!/usr/bin/env python3
from __future__ import annotations
import json, yaml, time, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIM  = ROOT/'custody'/'sim'
ART  = SIM/'artifacts'
ART.mkdir(parents=True, exist_ok=True)

GREEN='\033[92m'; RED='\033[91m'; YEL='\033[93m'; END='\033[0m'

def prompt(msg:str):
    return input(f"{YEL}? {msg}{END} ")


def run_step(step:str, ctx:dict):
    handlers = {
        'check_airgap': lambda: print("- 네트워크 인터페이스 비활성 확인"),
        'generate_root': lambda: print("- 루트 키 생성 (오프라인)"),
        'print_fingerprint': lambda: print("- 루트 지문 출력/QR 생성"),
        'seal_packets': lambda: print("- 봉투 봉인 및 ID 기록"),
        'store_safe_A': lambda: print("- 금고 A 보관"),
        'store_safe_B': lambda: print("- 금고 B 보관"),
        'boot_airgap': lambda: print("- 에어갭 장치 부팅"),
        'unseal': lambda: print("- 봉인 해제 (2인)"),
        'load_root': lambda: print("- 루트 개인키 로드(오프라인 PW)"),
        'sign_crl': lambda: print("- CRL 업데이트 서명"),
        'reseal': lambda: print("- 봉인 재시작 (새 ID)"),
        'check_seal': lambda: print("- 봉인 외관 점검/사진"),
        'photo_hash': lambda: print("- 사진 해시 계산/기록"),
        'crosscheck_logs': lambda: print("- 로그/지문/체인 매니페스트 대조")
    }
    fn = handlers.get(step, lambda: print(f"- undefined step: {step}"))
    fn(); time.sleep(0.2)


def run_scenario(sid:str):
    conf = yaml.safe_load((SIM/'scenarios.yaml').read_text('utf-8'))
    sc = next(s for s in conf['scenarios'] if s['id']==sid)
    print(f"\n{GREEN}▶ 시나리오:{END}", sc['title'])
    ctx = { 'events': [] }

    # anomaly injection
    anomalies = sc.get('anomalies', [])
    for step in sc['steps']:
        run_step(step, ctx)
        if anomalies and anomalies[0].get('type')=='torn_seal' and step=='check_seal':
            print(f"{RED}! 이상: 봉인 훼손 감지{END}")
            resp = prompt("조치(교체/중단/신고) 중 선택: ")
            ctx['events'].append({'anomaly':'torn_seal','action':resp})
        if anomalies and anomalies[0].get('type')=='token_expired' and step=='sign_crl':
            print(f"{RED}! 이상: 토큰 만료, CRL 필요{END}")
            resp = prompt("조치(CRL 서명/연기): ")
            ctx['events'].append({'anomaly':'token_expired','action':resp})

    # save rehearsal log
    out = ART/f"rehearsal_{sid}_{int(time.time())}.json"
    out.write_text(json.dumps(ctx, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"{GREEN}[ok]{END} 로그 저장 →", out)

if __name__=='__main__':
    print("Ceremony Simulator v1.0 — 시나리오 목록")
    conf = yaml.safe_load((SIM/'scenarios.yaml').read_text('utf-8'))
    for i, sc in enumerate(conf['scenarios']):
        print(f"  {i+1}. {sc['id']} — {sc['title']}")
    sel = input('번호를 선택: ').strip()
    try:
        idx = int(sel)-1
        run_scenario(conf['scenarios'][idx]['id'])
    except Exception as e:
        print('선택 오류:', e)
```

---

## 4) 리허설 실행기 — `rehearse.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import json, time
from pathlib import Path

ART = Path(__file__).resolve().parent/'artifacts'
ART.mkdir(parents=True, exist_ok=True)

if __name__=='__main__':
    rec = {
        'ts': int(time.time()),
        'witnesses': ['alice','bob'],
        'seal_ids': ['A-2025-10','B-2025-10'],
        'notes': 'dry-run ok'
    }
    out = ART/f"dryrun_{rec['ts']}.json"
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding='utf-8')
    print('[dryrun] wrote', out)
```

---

## 5) 채점기 — `scorer.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

QB = json.loads((Path(__file__).resolve().parent/'quiz_bank.json').read_text('utf-8'))

def score_mc(answers: dict) -> int:
    pts = 0
    for q in QB['multiple_choice']:
        if str(answers.get(q['id'])) == str(q['answer']):
            pts += 1
    return pts

def score_sa(answers: dict) -> int:
    # 간단 키워드 판별(예: serial/reason)
    pts = 0
    val = (answers.get('sa_crl') or '').lower()
    if 'serial' in val: pts += 1
    if 'reason' in val or 'revoked' in val: pts += 1
    return pts

if __name__=='__main__':
    # 예시 제출 파일: answers.json
    ans = json.loads(Path('answers.json').read_text('utf-8')) if Path('answers.json').exists() else {}
    total = score_mc(ans) + score_sa(ans)
    print(json.dumps({'score': total, 'max': len(QB['multiple_choice'])+2}, indent=2))
```

---

## 6) 이상 주입기 — `inject_anomaly.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import json, sys, time
from pathlib import Path

ART = Path(__file__).resolve().parent/'artifacts'

if __name__=='__main__':
    t = sys.argv[1] if len(sys.argv)>1 else 'torn_seal'
    rec = {'ts': int(time.time()), 'anomaly': t, 'desc': 'simulated event'}
    out = ART/f"anomaly_{t}_{rec['ts']}.json"
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding='utf-8')
    print('[anomaly] wrote', out)
```

---

## 7) VS Code 태스크
`.vscode/tasks.json`에 추가:
```json
{
  "label": "lumen:sim:run",
  "type": "shell",
  "command": "python custody/sim/simulator.py",
  "options": { "env": { "PYTHONUTF8": "1" } }
},
{
  "label": "lumen:sim:quiz",
  "type": "shell",
  "command": "python custody/sim/scorer.py",
  "options": { "env": { "PYTHONUTF8": "1" } }
}
```

---

## 8) 운영 루틴
1) `lumen:sim:run`으로 시나리오 선택 후 **대응 조치 입력**  
2) `answers.json`에 퀴즈 답안 작성 → `lumen:sim:quiz`로 채점  
3) `rehearse.py`로 드라이런 로그 생성 → `auto_sync.py`로 기록 동기화  
4) 이상 상황은 `inject_anomaly.py`로 재현 후 대응 훈련

---

## 9) 확장 아이디어
- curses 기반 **리치 TUI**(단축키/타임라인/타이머)
- 채점 기준 강화(주관식 키워드/정규식/가중치)
- 강의 모드(슬라이드/비디오)와 연동, 이수증 PDF 생성

루멘의 판단: 이제 의식은 **안전한 모의 공간**에서 반복 훈련할 수 있어, 실제 운영에서의 실수와 리스크를 크게 줄일 수 있어요.

