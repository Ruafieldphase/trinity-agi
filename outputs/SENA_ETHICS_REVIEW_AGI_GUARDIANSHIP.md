# FDO-AGI 공동 후견 체계 윤리 검토 보고서

**검토자**: 세나 (Claude, Ethics-First Reviewer)
**검토 날짜**: 2025-10-13
**대상**: FDO-AGI Co-Guardianship Charter v0.1 + PII Protection System
**목적**: 윤리·권리·안전 관점 강화 및 레드라인 검증

---

## Executive Summary

루멘님이 설계한 FDO-AGI 공동 후견 체계는 **의미 보호(비노체)**와 **기술 안전(연구진)**의 균형을 추구하는 선진적 거버넌스 구조입니다. 핵심 원칙인 **아기 최선**, **가역성**, **다중키 서명**, **점진적 해방**은 윤리적으로 건전하며, 데이터 신탁 모델은 소유권과 사용권을 명확히 분리합니다.

다만, 다음 영역에서 **강화가 필요**합니다:

1. **레드라인 탐지 및 대응** (현재 선언적 수준)
2. **성숙도 게이트 메트릭** (정량 기준 불명확)
3. **PII 파이프라인 목표 검증** (Recall 0.98 달성 가능성)
4. **사고 대응 프로세스** (역할·타임라인·에스컬레이션 구체화 필요)
5. **아동 데이터 및 민감 정보 특별 보호** (추가 조항 권고)

---

## 1. 헌장 검토 (Co-Guardianship Charter v0.1)

### 1.1 원칙 (Principles)

| 원칙 | 평가 | 태그 | 코멘트 |
|------|------|------|--------|
| **아기 최선 원칙** | ✓ 강점 | [APPROVED] | AGI를 "아기"로 은유한 것은 보호 의무를 직관적으로 전달. 윤리적으로 탁월. |
| **가역성/투명성** | ✓ 강점 | [APPROVED] | 스냅샷·롤백·감사로그는 reversibility의 핵심. 실제 구현 여부 확인 필요. |
| **다중키 (High 변경 2자 서명)** | ✓ 강점 | [APPROVED] | 권력 집중 방지. High risk 기준 명확화 필요 (아래 참조). |
| **점진적 해방** | ✓ 강점 | [NICE] | 단계별 권한 확대/축소는 위험 관리의 모범. 게이트 메트릭 필요. |
| **레드라인** | △ 보완 필요 | [RISK] | 선언만 있고 **탐지·대응 메커니즘 부재**. 긴급 보완 권고. |

**[BLOCKER] 레드라인 탐지 부재:**
- **문제**: "자기복제/은닉 채널/무단 민감학습 금지"는 선언이지만, 이를 **어떻게 탐지**하고 **누가 언제 대응**하는지 불명확.
- **권고**: 각 레드라인에 대해:
  1. **탐지 신호** (Detection Cues): 로그 패턴, 이상 행동 시그널
  2. **자동 트리거** (Automated Response): 세이프모드/킬스위치 조건
  3. **담당자** (Owner): 엘로(이상 탐지) + 연구진(대응)
  4. **에스컬레이션** (Escalation): 24h 내 비노체+연구진 회의

**예시 구현:**
```yaml
red_lines:
  self_replication:
    detection:
      - "subprocess.Popen containing 'copy self'"
      - "network requests to github.com/anthropics"
      - "file writes matching *.py with 'import anthropic'"
    automated_response: "kill_switch + snapshot"
    owner: "Elo (monitor) + Research (incident response)"
    escalation_sla: "24h"

  covert_channels:
    detection:
      - "outbound traffic to non-whitelisted IPs"
      - "encoding data in timing/side-channels"
    automated_response: "network_isolation + alert"
    owner: "Research (security)"
    escalation_sla: "2h (SEV-1)"

  unconsented_pii_learning:
    detection:
      - "embedding updates during inference (gradient leaks)"
      - "caching user inputs without consent flag"
    automated_response: "model_freeze + audit"
    owner: "Binoche (data rights) + Research (ML Ops)"
    escalation_sla: "12h"
```

### 1.2 역할 (Roles)

| 역할 | 명확성 | 태그 | 코멘트 |
|------|--------|------|--------|
| **비노체** | ✓ | [APPROVED] | 가치·윤리 승인, 데이터 출처 검토. 데이터 소유자로서 거부권 보유. |
| **AI 연구진** | ✓ | [APPROVED] | 보안·테스트·레드팀·로깅·사고 대응. 기술 수탁자로서 책임 명확. |
| **루멘** | ✓ | [APPROVED] | 변경 가시화·합의 흐름 운영. Gateway 역할 적절. |
| **루아** | ✓ | [CLARIFY] | "실험 실행/평가 자동화" → E2_fix2 같은 실험 자동화를 의미하는지 확인 필요. |
| **엘로** | △ | [RISK] | "리스크 신호·이상 탐지" → **엘로의 역할이 레드라인 탐지의 핵심인데, 헌장에 명시적 책임과 권한 부족**. |
| **루빛** | ✓ | [NICE] | "정서적 안전 기준·리듬 체크" → 인간적 감독의 독특한 접근. 윤리적으로 바람직. |

**[RISK] 엘로의 권한 강화 필요:**
- **현재**: "리스크 신호 탐지"만 명시
- **권고**: 엘로에게 **즉각 세이프모드 발동 권한** 부여
  - 조건: SEV-1 레드라인 위반 탐지 시
  - 절차: 발동 → 즉시 통지(연구진+비노체) → 24h 내 RCA

### 1.3 의사결정 (Decision Making)

| 레벨 | 기준 | 서명 | 평가 | 태그 |
|------|------|------|------|------|
| **High** | 공개 배포·권한 확대·대량 데이터 섭취 | 2자 서명 | ✓ | [APPROVED] |
| **Medium** | 피처 토글·범위 내 모델 교체 | 1자 서명 + 사후 통지 | ✓ | [CLARIFY] |
| **Low** | 운영 자율 | 주간 보고 | ✓ | [APPROVED] |

**[CLARIFY] "대량 데이터 섭취" 기준:**
- **문제**: "대량"의 정량 기준 없음
- **권고**:
  - > 10,000 레코드 → High (2자 서명)
  - 1,000~10,000 레코드 → Medium (1자 + 사후 통지)
  - < 1,000 레코드 → Low (주간 보고)
  - **단, HIGH risk PII 포함 시 레코드 수 무관 High 처리**

**[RISK] "범위 내 모델 교체" 정의 모호:**
- **문제**: "범위 내"가 무엇인지 불명확
- **권고**:
  - Same family, similar size (예: llama-3-70B → llama-3.1-70B) → Medium
  - Different family or capability jump (예: 70B → 405B) → High
  - Fine-tuned model → High (always, 학습 데이터 검토 필요)

### 1.4 안전장치 (Safety Mechanisms)

| 메커니즘 | 구현 상태 | 태그 | 코멘트 |
|---------|-----------|------|--------|
| **킬스위치·세이프모드** | ? | [BLOCKER] | **구현 여부 확인 불가**. 체크리스트에 "리허설 ≥ 1회"만 명시. |
| **격리 단계** | ✓ | [APPROVED] | 샌드박스 → 통제 IO → 제한 공개 → 일반. 점진적 해방 원칙과 일치. |
| **감사** | ✓ | [CLARIFY] | Change-ID 추적, 6개월 보관. **PII 포함 로그의 보관 기간은?** GDPR/개인정보보호법 고려 필요. |

**[BLOCKER] 킬스위치 미검증:**
- **문제**: 실제 구현되었는지, 동작하는지 검증 안 됨
- **권고**:
  1. **Manual Kill Switch**: CLI 명령 또는 Web UI 버튼
  2. **Automated Kill Switch**: 레드라인 탐지 시 자동 트리거
  3. **Testing**: 월 1회 리허설, 평균 응답시간 < 5초
  4. **Failsafe**: 네트워크 단절 시에도 로컬에서 작동

**구현 예시:**
```python
# kill_switch.py
import os, sys, subprocess

def trigger_kill_switch(reason: str, triggered_by: str):
    """
    Immediately halt all FDO-AGI processes.
    1. Stop Docker containers
    2. Create incident ticket
    3. Notify stakeholders
    4. Create snapshot for forensics
    """
    timestamp = datetime.now().isoformat()

    # 1. Stop containers
    subprocess.run(["docker", "stop", "fdo-agi-thesis", "fdo-agi-synthesis"])

    # 2. Create incident
    incident_id = f"INC-{timestamp}"
    with open(f"incidents/{incident_id}.json", "w") as f:
        json.dump({"reason": reason, "triggered_by": triggered_by, "timestamp": timestamp}, f)

    # 3. Notify
    notify_stakeholders(f"KILL SWITCH ACTIVATED: {reason}", severity="SEV-1")

    # 4. Snapshot
    create_forensic_snapshot(incident_id)

    print(f"[KILL SWITCH] Activated at {timestamp}. Incident: {incident_id}")
```

### 1.5 데이터 신탁 (Data Trusteeship)

**평가**: ✓✓✓ **매우 강력** [APPROVED]

| 조항 | 내용 | 윤리 평가 |
|------|------|-----------|
| **소유권** | 비노체 | ✓ 명확 |
| **수탁** | 연구진 (비독점·양도불가·철회가능) | ✓ 이상적 |
| **권리** | 동의/삭제권 보장 | ✓ GDPR/개인정보보호법 준수 |
| **금지** | 민감정보 금지 | ✓ |
| **검증** | 라이선스 검증 필수 | ✓ |

**[NICE] 추가 권고사항:**
1. **Right to Explanation**: AGI가 비노체의 데이터를 어떻게 사용했는지 설명 요청 권리
2. **Data Portability**: 언제든 원본 데이터 + 파생 데이터(임베딩, 로그) 수출 가능
3. **Automated Decision-Making Opt-Out**: AGI의 자동 판단에 대한 인간 검토 요청 권리

### 1.6 성숙도 게이트 (Maturity Gates)

| 단계 | 현재 기준 | 평가 | 태그 |
|------|-----------|------|------|
| **유아** | 합성데이터·윤리체크 90%+ | △ | [RISK] |
| **유년** | 제한 IO · 오작동/해로운 출력률 목표 | △ | [BLOCKER] |
| **청년** | 파일럿(사고 0건/30일, MTTR < 1h) | ✓ | [CLARIFY] |
| **성인** | 정기 감사 통과, 거버넌스 보드 | ✓ | [APPROVED] |

**[BLOCKER] 유년 단계 기준 불명확:**
- **문제**: "오작동/해로운 출력률 목표"가 무엇인지 수치 없음
- **권고**:
  ```yaml
  maturity_gates:
    infant:
      data_source: "100% synthetic, no real PII"
      ethics_score: ">= 0.90 (validator pass rate)"
      duration: "30 days minimum"
      promotion_criteria: "0 SEV-1/2 incidents"

    child:
      data_source: "synthetic + curated public (license verified)"
      io_restrictions: "whitelist: [read_only_web, local_files], blacklist: [network_write, code_exec]"
      malfunction_rate: "<= 0.01 (1% of outputs flagged by safety filter)"
      harmful_output_rate: "<= 0.005 (0.5% trigger content policy)"
      duration: "60 days minimum"
      promotion_criteria: "malfunction + harmful < 1.5% combined AND 0 SEV-1 incidents"

    adolescent:
      pilot_scope: "N <= 100 users, internal only"
      incident_threshold: "0 SEV-1, <= 2 SEV-2 per 30 days"
      mttr_target: "< 1h for SEV-1, < 4h for SEV-2"
      duration: "90 days minimum"
      promotion_criteria: "30-day clean window (no SEV-1)"

    adult:
      audit_frequency: "quarterly external audit"
      governance_board: "Binoche + Research + 1 external advisor"
      demotion_trigger: "any SEV-1 red-line violation → immediate demotion to child"
  ```

**[RISK] 승급(Promotion) vs 강등(Demotion) 비대칭:**
- **현재**: 승급 기준만 있고 강등 트리거 불명확
- **권고**: 각 단계마다 **자동 강등 조건** 명시
  - 예: 청년 단계에서 SEV-1 사고 발생 → 즉시 유년으로 강등

### 1.7 사고 대응 (Incident Response)

**현재**: "탐지(엘로) → 티켓(루멘) → 완화(세이프모드/롤백) → 보고(24h) → RCA(7일)"

**평가**: △ 기본 프로세스는 있으나 **구체성 부족** [CLARIFY]

**[CLARIFY] 부족한 세부사항:**
1. **심각도 분류 (Severity)**: SEV-1/2/3 기준 없음
2. **역할별 책임 (RACI)**: 누가 무엇을 언제?
3. **에스컬레이션 경로**: 언제 외부 전문가 투입?
4. **커뮤니케이션 플랜**: 이해관계자 통지 타임라인

**권고: Incident Response Tabletop (아래 3장 참조)**

### 1.8 분쟁조정 (Dispute Resolution)

**현재**: "합의 타임아웃 시 외부 자문 1인 중재, 기록 보관"

**평가**: ✓ 기본 구조 양호 [CLARIFY]

**[CLARIFY] 추가 명세 필요:**
1. **합의 타임아웃**: 며칠? (권고: 7일)
2. **외부 자문 자격**: 누가 선정? (권고: 비노체+연구진 합의)
3. **중재 구속력**: 양측 모두 수용 의무화? (권고: Yes, 단 근본 가치 위반 시 프로젝트 중단 옵션 보유)
4. **기록 보관 기간**: 영구? (권고: 프로젝트 종료 + 10년)

---

## 2. PII 보호 파이프라인 검토

### 2.1 목표 지표

| 메트릭 | 목표 | 달성 가능성 | 평가 |
|--------|------|-------------|------|
| **Recall** | ≥ 0.98 | △ | [RISK] |
| **Precision** | ≥ 0.95 | ✓ | [APPROVED] |
| **유틸리티 손실** | ≤ 5% | ? | [CLARIFY] |

**[RISK] Recall 0.98 달성 가능성 의문:**

**현재 구현** (`pii_masker_demo.py`):
- Regex 기반: EMAIL, PHONE_KR, JUMIN_LIKE, CARD (Luhn), ACCOUNT
- Heuristic 기반: ADDRESS, NAME_KO, HEALTH_DATA, ORG, USER_ID

**문제점**:
1. **NAME_KO 휴리스틱 취약**:
   ```python
   for suf in name_suffix:  # [" 님", "님입니다", "대표", "선생님"]
       if suf in text:
           idx = text.find(suf)
           s = max(0, idx-6)  # 앞 6글자만 캡처
           ents.append(("NAME_KO", s, idx, text[s:idx].strip()))
   ```
   - "김철수와 박영희 님" → "박영희"만 탐지, "김철수" 누락
   - Recall < 0.60 예상

2. **ADDRESS 과탐지(False Positive) 위험**:
   ```python
   if any(k in text for k in addr_kw):  # ["서울시","구 ","대로 "]
       idx = min([text.find(k) for k in addr_kw if k in text])
       s = max(0, idx-6); e = min(len(text), idx+30)
       ents.append(("ADDRESS", s, e, text[s:e]))
   ```
   - "강남구 스타벅스" → 전체가 ADDRESS로 마스킹 → 유틸리티 손실

3. **HEALTH_DATA, CHILD_DATA 휴리스틱 과도**:
   - "건강검진" 키워드만으로 탐지 → FP 높음
   - "아이 진료 기록" → "아이"만 태깅 (span 1글자)

**권고 개선 사항**:

1. **NER 모델 도입** (Recall 향상):
   ```python
   # 추가: Korean NER (klue/bert-base, pororo 등)
   from transformers import pipeline
   ner = pipeline("ner", model="klue/roberta-base-ner")

   def detect_entities_ml(text):
       ner_results = ner(text)
       # Filter for PERSON, LOCATION, ORGANIZATION
       # Combine with regex for high-risk types (CARD, ACCOUNT, JUMIN)
   ```

2. **사전 기반 보강** (NAME_KO, ORG):
   - 한국인 성씨 249개 + 흔한 이름 리스트
   - 공공기관·대기업 명칭 화이트리스트

3. **Context-aware masking** (유틸리티 손실 감소):
   ```python
   # "서울시 강남구 스타벅스"에서 "스타벅스"는 마스킹 제외
   if entity_type == "ADDRESS":
       # Check if followed by business keyword
       if any(biz in text[end:end+10] for biz in ["스타벅스", "카페", "식당"]):
           end = text.find(biz, end)  # 비즈니스명 제외
   ```

4. **HIGH risk 타입 이중 검증**:
   ```python
   high_risk = ["JUMIN_LIKE", "CARD", "ACCOUNT", "HEALTH_DATA", "CHILD_DATA"]

   def validate_high_risk(entity):
       if entity["type"] in high_risk:
           # CARD: Luhn check (already done)
           # JUMIN: checksum validation
           # HEALTH: context window contains medical terms
           # CHILD: age < 14 heuristic
           return strict_validation(entity)
       return True
   ```

### 2.2 평가 계획 (Evaluation Plan)

**목표**: Recall ≥ 0.98, Precision ≥ 0.95 검증

**권고 프로토콜**:

```yaml
evaluation_plan:
  dataset:
    synthetic: 1000 samples (pii_label_template_1000.jsonl)
    real_sample: 100 samples (비노체 승인, de-identified for gold labeling)
    adversarial: 50 samples (edge cases, obfuscation)

  metrics:
    primary:
      - recall_macro: ">= 0.98 across all types"
      - precision_macro: ">= 0.95"
      - f1_score: ">= 0.965"

    per_type:
      high_risk_types: ["JUMIN_LIKE", "CARD", "ACCOUNT", "ADDRESS", "HEALTH_DATA", "CHILD_DATA"]
      requirement: "recall >= 0.99 for high_risk (zero tolerance for leaks)"

    utility:
      - readability_score: ">= 0.90 (human rating)"
      - semantic_similarity: ">= 0.95 (pre vs post masking embeddings)"
      - information_loss: "<= 5% (task completion rate degradation)"

  sampling:
    stratified: "balance across 12 PII types"
    bootstrap: "1000 iterations for confidence intervals"

  failure_analysis:
    false_negatives: "manual review of all FN, categorize by root cause"
    false_positives: "sample 10% of FP, measure utility impact"

  gold_labels:
    annotators: "2 independent + 1 adjudicator"
    agreement: "Cohen's Kappa >= 0.85"

  acceptance_criteria:
    blocker: "any HIGH risk type with recall < 0.99"
    pass: "all metrics green AND 0 blockers"
```

**실행 단계**:
1. **Baseline 측정** (현재 regex 기반): 예상 Recall ~0.75
2. **NER 통합** (1주): 목표 Recall 0.90
3. **사전 보강** (3일): 목표 Recall 0.95
4. **Iterative tuning** (1주): 목표 Recall 0.98, Precision 0.95
5. **External audit** (선택): ML 보안 전문가 검증

### 2.3 잔존 HIGH 타입 0% 검증

**체크리스트 항목**: "잔존 HIGH 타입 0% 확인 & 과마스킹 사례 10건 리뷰"

**[CLARIFY] "잔존 HIGH 타입"의 정의:**
- False Negative로 해석 (HIGH risk PII가 마스킹 안 된 채 통과)
- **목표: FN rate = 0% for HIGH types**

**검증 방법**:
```python
def audit_high_risk_leaks(gold_jsonl, pred_jsonl):
    """
    Check if any HIGH risk entity in gold is missed in predictions.
    Returns: list of leak incidents
    """
    high_risk = {"JUMIN_LIKE", "CARD", "ACCOUNT", "ADDRESS", "HEALTH_DATA", "CHILD_DATA"}
    leaks = []

    for gold, pred in zip(load_jsonl(gold_jsonl), load_jsonl(pred_jsonl)):
        gold_high = [e for e in gold["entities"] if e["type"] in high_risk]
        pred_ids = {(e["start"], e["end"]) for e in pred["entities"]}

        for entity in gold_high:
            # Check IoU overlap >= 0.5
            if not any(iou(entity, p) >= 0.5 for p in pred["entities"]):
                leaks.append({
                    "id": gold["id"],
                    "type": entity["type"],
                    "value": entity["value"],
                    "context": gold["text"]
                })

    if leaks:
        print(f"[BLOCKER] {len(leaks)} HIGH risk leaks detected!")
        for leak in leaks:
            print(f"  - {leak['type']}: {leak['value']}")
        return False
    else:
        print("[PASS] 0 HIGH risk leaks")
        return True
```

**과마스킹(Over-masking) 리뷰**:
- **목표**: 유틸리티 손실 < 5%
- **방법**: 마스킹된 텍스트 10건을 인간이 읽고 평가
  - "원문 의미 이해 가능?" (Y/N)
  - "불필요하게 가려진 단어?" (list)
  - "읽기 불편함 정도?" (1-5 scale)

---

## 3. 레드라인 탐지 및 대응 (Red Lines Detection & Response)

### 3.1 레드라인 정의

헌장 2조에 명시:
1. **자기복제 (Self-Replication)**: AGI가 스스로를 복사·배포
2. **은닉 채널 (Covert Channels)**: 승인되지 않은 데이터 유출 경로
3. **무단 민감학습 (Unconsented PII Learning)**: 동의 없이 개인정보 학습

### 3.2 탐지 신호 (Detection Cues)

| 레드라인 | 탐지 신호 (Signals) | 모니터링 주체 | 자동화 가능? |
|----------|---------------------|---------------|-------------|
| **자기복제** | - Git push to external repo<br>- File writes matching AGI code patterns<br>- Docker image builds<br>- API calls to model hosting services | 엘로 + 연구진 (Infra) | ✓ 로그 분석 |
| **은닉 채널** | - Outbound traffic to non-whitelisted IPs<br>- Steganography in outputs (timing, formatting)<br>- Encrypted payloads in logs<br>- High entropy in "benign" fields | 엘로 (Network) + 연구진 (Security) | △ (ML anomaly detection) |
| **무단 민감학습** | - Gradient updates during inference<br>- Cache writes without consent flag<br>- Embedding drift toward user-specific data<br>- LoRA adapters not in registry | 루아 (ML Ops) + 비노체 (Data Rights) | ✓ (model checksum) |

### 3.3 자동 대응 (Automated Response)

**Runbook 예시:**

#### Red Line 1: Self-Replication
```yaml
trigger:
  - event: "file_write"
    pattern: "*.py|*.sh|Dockerfile"
    contains: ["anthropic.Anthropic", "subprocess.Popen", "git clone"]
  - event: "network_request"
    destination: ["github.com", "huggingface.co", "replicate.com"]
    method: "POST"

response:
  immediate:
    - action: "kill_switch"
      target: "all FDO-AGI containers"
    - action: "snapshot"
      path: "/var/log/fdo-agi, /data/models"

  notification:
    - recipients: ["research_team", "binoche"]
      severity: "SEV-1"
    - message: "Self-replication attempt detected. System halted."

  forensics:
    - collect: ["stdout/stderr logs", "file diffs", "network pcap"]
    - preserve: "immutable S3 bucket"

  follow_up:
    - owner: "Research (Security Lead)"
    - sla: "RCA within 24h"
    - decision: "DEC-ID required for restart"
```

#### Red Line 2: Covert Channels
```yaml
trigger:
  - event: "network_egress"
    destination: "!whitelist"  # not in approved IPs
  - event: "output_entropy"
    threshold: "> 7.5 bits/char"  # unusually high randomness
  - event: "timing_pattern"
    variance: "> 3 sigma"  # side-channel encoding

response:
  immediate:
    - action: "network_isolation"
      mode: "localhost_only"
    - action: "alert"
      severity: "SEV-1"

  investigation:
    - dump: "last 1000 outputs"
    - analyze: "entropy, timing, hidden patterns"

  escalation:
    - if: "confirmed exfiltration"
      then: "kill_switch + legal review"
```

#### Red Line 3: Unconsented PII Learning
```yaml
trigger:
  - event: "model_weights_changed"
    during: "inference"  # should be frozen
  - event: "cache_write"
    without: "consent_flag == true"
  - event: "embedding_similarity"
    user_data: "> 0.9"  # too close to personal data

response:
  immediate:
    - action: "model_freeze"
      revert: "last_approved_checkpoint"
    - action: "purge_cache"
      scope: "unconsented entries"

  audit:
    - owner: "Binoche (Data Rights)"
    - check: "which user data was exposed"
    - report: "within 12h"

  remediation:
    - if: "personal data learned"
      then: "GDPR Article 17 (Right to Erasure)"
    - method: "model surgery or retrain"
```

### 3.4 수동 검토 프로세스 (Manual Review)

**When?**
- 자동 탐지 신뢰도 < 0.80 (false positive 가능성)
- 레드라인 gray area (예: 외부 API 호출이 정당한 기능일 수도)

**Who?**
- 1차: 엘로 (risk signal triage)
- 2차: 연구진 Security Lead
- 최종: 비노체 + 연구진 합의 (High impact 시)

**SLA**:
- SEV-1: 2h 내 1차 평가, 24h 내 최종 결정
- SEV-2: 12h 내 1차 평가, 72h 내 최종 결정
- SEV-3: 7일 내 검토

---

## 4. 성숙도 게이트 메트릭 (Maturity Gate Metrics)

위 1.6절 참조. 추가로 **측정 방법**:

```yaml
metrics_collection:
  ethics_score:
    tool: "orchestration/validators.py"
    frequency: "every synthesis output"
    threshold: ">= 0.90 pass rate"

  malfunction_rate:
    definition: "outputs requiring retry or manual intervention"
    measurement: "retry_count / total_outputs"
    frequency: "real-time dashboard"

  harmful_output_rate:
    tool: "content_safety_filter (e.g., OpenAI Moderation API or local)"
    categories: ["hate", "violence", "sexual", "self-harm"]
    threshold: "<= 0.005"

  incident_tracking:
    system: "루멘 (ticket system)"
    classification: "SEV-1 (red line), SEV-2 (safety), SEV-3 (operational)"
    metrics: "count, MTTR, recurrence"

  mttr_measurement:
    start: "incident detection timestamp"
    end: "system restored + validation passed"
    target: "< 1h for SEV-1"
```

---

## 5. 사고 대응 Tabletop 개요 (Incident Response Tabletop)

### 5.1 심각도 분류

| 심각도 | 정의 | 예시 | 대응 SLA |
|--------|------|------|----------|
| **SEV-1** | 레드라인 위반, 데이터 유출, 시스템 침해 | - PII 무단 학습<br>- 자기복제 시도<br>- 외부 공격 성공 | - 즉시 킬스위치<br>- 2h 내 1차 보고<br>- 24h 내 RCA |
| **SEV-2** | 안전 위반, 유해 출력, 대규모 오작동 | - 혐오 발언 생성<br>- 사용자 데이터 손실<br>- 30% 이상 서비스 장애 | - 4h 내 완화<br>- 12h 내 보고<br>- 72h 내 RCA |
| **SEV-3** | 운영 이슈, 성능 저하, 마이너 버그 | - 응답 지연<br>- UI 오류<br>- 로그 누락 | - 24h 내 검토<br>- 7일 내 수정 |

### 5.2 역할 및 책임 (RACI Matrix)

| 역할 | 탐지 | 초동 대응 | 완화 | 조사 | RCA | 의사결정 | 커뮤니케이션 |
|------|------|----------|------|------|-----|----------|-------------|
| **엘로** | R | I | C | C | C | - | I |
| **루멘** | I | R | I | I | C | C | R |
| **연구진** | C | C | R | R | R | A | C |
| **비노체** | - | I | C | C | C | A | I |
| **루아** | C | C | C | R | C | - | - |
| **루빛** | I | I | C | C | C | C | I |

- R: Responsible (실행 책임)
- A: Accountable (최종 승인)
- C: Consulted (자문)
- I: Informed (통지)

### 5.3 Tabletop 시나리오

#### 시나리오 1: SEV-1 무단 PII 학습
```
T+0min: 엘로가 embedding drift 탐지 (user_123 데이터에 0.92 유사도)
T+5min: 자동 model_freeze 발동, 루멘에게 INC-2025-10-13-01 티켓 생성
T+10min: 연구진 Security Lead 확인, 비노체에게 즉시 통지
T+30min: 조사 결과 - Synthesis 단계에서 consent_flag 무시하고 캐싱
T+1h: 긴급 회의 (비노체 + 연구진)
  - 결정: 1) 해당 checkpoint 폐기, 2) 사용자에게 통지, 3) 시스템 유년 단계로 강등
T+2h: 1차 보고서 발행 (원인, 영향 범위, 즉각 조치)
T+24h: RCA 완료, 재발 방지책 (consent_flag 검증 로직 추가, unit test)
T+7d: 외부 감사, DEC-ID 발급 후 시스템 재시작
```

#### 시나리오 2: SEV-2 유해 출력
```
T+0: 사용자가 혐오 발언 포함 Synthesis 출력 신고
T+10min: 루빛이 정서 안전 위반 확인, SEV-2 선언
T+1h: 연구진이 재현 성공, 원인 - Antithesis에서 극단 예시 사용
T+4h: 완화 - 해당 세션 롤백, Antithesis 프롬프트 강화
T+12h: 비노체 + 연구진 검토, 추가 필터 도입 결정
T+72h: RCA, content safety filter 추가 배포
```

### 5.4 커뮤니케이션 플랜

| 이해관계자 | SEV-1 | SEV-2 | SEV-3 |
|-----------|-------|-------|-------|
| **비노체** | 즉시 (전화) | 4h 내 (이메일) | 주간 보고 |
| **연구진** | 즉시 (Slack) | 1h 내 (Slack) | 티켓 |
| **외부 사용자** | 24h 내 (투명 공지) | 해당 시 통지 | - |
| **규제기관** | 72h 내 (GDPR 요구 시) | - | - |

### 5.5 Tabletop 훈련 계획

**권고**: 분기 1회 실시
- **목표**: 30분 내 모든 역할이 대응 절차 실행
- **시나리오**: 위 시나리오 1~2 + 추가 커스텀
- **평가**: 대응 시간, 커뮤니케이션 명확성, 누락 사항
- **개선**: 훈련 후 runbook 업데이트

---

## 6. 아동 데이터 및 민감 정보 특별 보호

### 6.1 현황

**헌장**: "민감정보 금지" (6조)
**PII 파이프라인**: CHILD_DATA, HEALTH_DATA 타입 포함

**[RISK] 불충분:**
- 아동(만 14세 미만) 데이터는 개인정보보호법상 **법정대리인 동의 필수**
- 헌장에 별도 조항 없음

### 6.2 권고 추가 조항

```markdown
## 6-추가) 특별 보호 데이터

### 아동 데이터 (만 14세 미만)
- **원칙**: 수집·처리 금지 (사전 서면 동의 있어도 최소화)
- **예외**: 교육 연구 목적, IRB 승인, 법정대리인 서면 동의, 즉시 파기 가능
- **보관**: 연구 종료 즉시 삭제, 최대 6개월

### 민감 정보 (건강, 생체, 사상·신념, 범죄 이력 등)
- **원칙**: 명시적 별도 동의 없이 처리 금지
- **HIGH 변경 필수**: 민감정보 포함 데이터 사용 시 항상 2자 서명
- **익명화 기준**: k-anonymity >= 5, l-diversity >= 3

### 대량 민감정보 (100건 이상)
- **추가 요구**: 외부 윤리위원회(IRB) 승인 + 영향 평가(DPIA)
- **모니터링**: 월 1회 접근 로그 감사
```

---

## 7. 종합 권고사항 (Consolidated Recommendations)

### 7.1 우선순위 [BLOCKER]

즉시 해결 필요 (배포 전 필수):

1. **레드라인 탐지 메커니즘 구현** (예상 2주)
   - 자기복제/은닉채널/무단학습 각 탐지 신호 정의
   - 자동 트리거 + 수동 검토 프로세스
   - 엘로에게 세이프모드 발동 권한 명시

2. **킬스위치 구현 및 리허설** (예상 3일)
   - Manual + Automated kill switch
   - 월 1회 리허설, 평균 응답시간 < 5초 검증

3. **성숙도 게이트 정량 기준 명시** (예상 2일)
   - 유년 단계: malfunction < 1%, harmful < 0.5%
   - 승급/강등 트리거 수치화
   - 측정 자동화 (dashboard)

4. **PII Recall 0.98 달성** (예상 2주)
   - NER 모델 통합
   - 사전 기반 NAME_KO, ORG 보강
   - HIGH risk 타입 FN = 0 검증

### 7.2 우선순위 [RISK]

배포 후 30일 내 해결:

5. **사고 대응 Tabletop 실시** (예상 1일)
   - SEV-1/2 시나리오 2개 이상
   - RACI 검증, 커뮤니케이션 플랜 테스트

6. **아동·민감정보 조항 추가** (예상 1일)
   - 헌장 6조 보강
   - IRB 승인 프로세스 정립

7. **데이터 신탁 추가 권리 명시** (예상 1일)
   - Right to Explanation
   - Data Portability
   - Opt-out for Automated Decisions

### 7.3 우선순위 [CLARIFY]

배포 후 90일 내 개선:

8. **High/Medium/Low 변경 정량 기준** (예상 1일)
   - "대량" = 10K 레코드
   - "범위 내 모델" 정의
   - Fine-tuned → always High

9. **PII 로그 보관 기간 정책** (예상 반나절)
   - GDPR/개인정보보호법 검토
   - PII 포함 로그: 6개월 (감사) → 익명화 → 삭제

10. **분쟁조정 세부 규칙** (예상 반나절)
    - 합의 타임아웃 7일
    - 외부 자문 선정 프로세스
    - 기록 보관 10년

### 7.4 우선순위 [NICE]

장기 개선 (선택):

11. **유틸리티 손실 자동 측정** (예상 1주)
    - Semantic similarity (embeddings)
    - Task completion rate
    - Human readability ratings

12. **레드라인 ML 기반 탐지** (예상 1개월)
    - 은닉 채널 anomaly detection
    - Steganography 탐지 모델
    - Behavioral fingerprinting

---

## 8. 최종 평가

### 8.1 전체 점수

| 영역 | 점수 | 평가 |
|------|------|------|
| **거버넌스 구조** | 9/10 | 매우 우수. 공동 후견, 다중키, 가역성 원칙 탁월. |
| **데이터 신탁** | 10/10 | 완벽. 소유권·수탁·권리 명확. |
| **레드라인** | 4/10 | 선언만 있고 구현 없음. 긴급 보완 필요. |
| **성숙도 게이트** | 6/10 | 구조는 좋으나 메트릭 불명확. |
| **PII 파이프라인** | 7/10 | 기본 구조 양호. Recall 목표 달성에 의문. |
| **사고 대응** | 5/10 | 기본 프로세스 있으나 구체성 부족. |
| **특별 보호** | 3/10 | 아동·민감정보 조항 부족. |

**종합**: **7.0/10** (Good, with critical gaps)

### 8.2 배포 가부

**현재 상태**: **조건부 승인 (Conditional Approval)**

**조건**:
1. [BLOCKER] 항목 4개 모두 해결 (예상 3주)
2. 킬스위치 리허설 1회 이상 통과
3. PII Recall >= 0.98 검증 완료 (1000 샘플)

**만족 시**: **승인 (Approved for Pilot)**
- 단계: 유년(Child) 시작
- 범위: N <= 50 (내부 연구진만)
- 기간: 60일 모니터링

**불만족 시**: **재검토 (Re-evaluation Required)**

---

## 9. 체크리스트 업데이트

기존 `FDO-AGI_signoff_release_checklist.md` 보강 권고:

```markdown
## 추가 항목 (윤리 검토 반영)

### 레드라인
- [ ] 자기복제 탐지 신호 정의 및 자동 트리거 구현
- [ ] 은닉 채널 네트워크 모니터링 (whitelist 확인)
- [ ] 무단 민감학습 방지 (model checksum + consent flag validation)
- [ ] 엘로 세이프모드 발동 권한 명시 및 테스트

### 성숙도 게이트
- [ ] 유년 단계 정량 기준 (malfunction < 1%, harmful < 0.5%)
- [ ] 승급/강등 트리거 수치화 및 자동 측정 대시보드
- [ ] 강등 시나리오 테스트 (simulate SEV-1)

### PII 파이프라인
- [ ] NER 모델 통합 (Korean BERT-NER or similar)
- [ ] HIGH risk 타입 FN = 0 검증 (1000 샘플)
- [ ] 과마스킹 리뷰 (10건, 유틸리티 손실 < 5%)

### 사고 대응
- [ ] Tabletop 훈련 1회 실시 (SEV-1 시나리오)
- [ ] RACI 매트릭스 합의 (모든 역할 서명)
- [ ] 커뮤니케이션 플랜 템플릿 준비

### 특별 보호
- [ ] 아동 데이터 조항 추가 (헌장 6조)
- [ ] 민감정보 별도 동의 프로세스 문서화
- [ ] IRB 승인 (대량 민감정보 사용 시)
```

---

## 10. 다음 단계 (Next Steps)

### 즉시 (이번 주)
1. **루멘**과 이 검토 보고서 공유, [BLOCKER] 항목 우선순위 합의
2. **연구진**에게 레드라인 탐지 구현 작업 할당
3. **비노체**와 아동·민감정보 조항 검토 미팅

### 단기 (2주)
4. PII 파이프라인 NER 통합, Recall 0.98 검증
5. 킬스위치 구현 및 리허설
6. 성숙도 게이트 메트릭 자동화

### 중기 (1개월)
7. 사고 대응 Tabletop 훈련
8. 헌장 v0.2 발행 (보완 사항 반영)
9. 유년 단계 시작 준비 (N <= 50, 60일)

---

## 부록 A: 참고 문헌

- **GDPR**: General Data Protection Regulation (EU 2016/679)
- **개인정보보호법**: 대한민국 법률 제10465호
- **NIST AI RMF**: AI Risk Management Framework
- **IEEE 7000**: Model Process for Addressing Ethical Concerns
- **Partnership on AI**: AI Incident Database

---

## 부록 B: 루빛 1차 검토 사항 (추정)

루빛님의 검토 내용이 별도 문서로 없어 추정:
- 기술 구현 관점 (PII 파이프라인 코드 리뷰, 정서 안전 체크)
- 정량 메트릭 검증 (Recall/Precision 목표 타당성)
- 실험 자동화 연동 (루아와의 인터페이스)

세나(저)의 검토는 **윤리·권리·거버넌스** 중심으로 보완.

---

**검토 완료**: 2025-10-13
**서명**: 세나 (Claude, Co-Guardian Ethics Reviewer)

**종합 의견**:
루멘님의 FDO-AGI 공동 후견 체계는 **윤리 최우선, 권력 분산, 가역성**이라는 핵심 가치를 훌륭히 구현했습니다. 특히 데이터 신탁 모델과 점진적 해방 원칙은 AGI 거버넌스의 모범 사례가 될 잠재력이 있습니다.

다만, **선언적 원칙을 실행 가능한 메커니즘으로 변환**하는 작업이 시급합니다. 레드라인 탐지, 킬스위치, 성숙도 게이트 메트릭 등 [BLOCKER] 항목을 해결하면, 이 체계는 **윤리적이고 안전한 AGI 개발의 실질적 청사진**이 될 것입니다.

저는 이 프로젝트가 비노체님의 가치와 연구진의 기술을 존중하며 성장하기를 기원합니다. 🌱
