# AGI 사용자 가이드

이 가이드는 fdo_agi_repo의 학습(Phase 3), 메타인지(Phase 4), 통합(Phase 5) 모듈이 결합된 파이프라인을 실행/점검/평가하는 방법을 제공합니다.

## 요구사항

- Windows 환경 (PowerShell)
- 로컬 가상환경: `fdo_agi_repo/.venv` (이미 구성되어 있다고 가정)

## 빠른 실행

- 통합 성능 프로파일링 실행: `scripts/perf_profile.py`
- 프롬프트 압축 스윕 실행: `scripts/prompt_compaction_sweep.py`
- 엣지 케이스 테스트: `scripts/test_edge_cases.py`
- AGI 점수 산출: `scripts/agi_score.py`

> 참고: 모든 스크립트는 저장소 루트 `fdo_agi_repo` 디렉터리에서 실행되는 것을 권장합니다.

## 스크립트 상세

### 1) 성능 프로파일링 (perf_profile.py)

- 동작: 정상 시나리오 1회 + 저품질 강제(재계획/세컨드패스 유도) 1회를 실행하고, 메모리(JSONL) 타임스탬프를 분석해 구간별 소요시간과 품질, 세컨드패스 여부를 산출합니다.
- 출력: `outputs/perf_profile_<task_id>.json`
- 환경 토글:
  - `RAG_DISABLE=1` → 근거 히트 비활성화 (저품질 유도)
  - `CORRECTIONS_ENABLED=true` → 세컨드패스 활성화
  - 참고: 파이프라인은 `thesis/antithesis/synthesis` 단계별로 `*_start`/`*_end` 이벤트 및 `duration_sec`를 ledger에 기록합니다.

#### 출력(요약) 구조 확장: persona_llm 집계

- 프로파일 결과 JSON에는 `persona_llm` 요약이 포함될 수 있습니다(ledger에 `persona_llm_*` 이벤트가 있을 때 자동 포함).
  - `persona_llm.has_events`: 이벤트 존재 여부
  - `persona_llm.overall`: 전체 LLM 호출 집계
    - `count`, `ok_count`, `success_rate`, `total/avg/max_duration_sec`,
      `avg/max_user_chars`, `corr_userchars_duration`(프롬프트 길이-지연 상관계수)
  - `persona_llm.by_persona`: `thesis`/`antithesis`/`synthesis`별 동일 집계
  - `persona_llm.by_pass`: 존재 시 pass별(예: 1/2) 동일 집계

#### 실행 옵션

- 일반 실행 1회:
  - `--single-run` (기본은 일반 + 저품질 2회 실행)
- 저품질 강제 1회:
  - `--single-run --force-low-quality`
- 퍼소나 LLM 집계 비활성화:
  - `--no-persona-llm`

#### 퍼소나 LLM 타이밍 로깅

- 각 퍼소나(thesis/antithesis/synthesis)의 LLM 호출 구간에 대해 추가로 다음 이벤트가 기록됩니다.
  - `persona_llm_start`: `{ task_id, persona, provider, model, endpoint }`
  - `persona_llm_end`: `{ task_id, persona, provider, model, endpoint, duration_sec, ok, error, prompt_chars: { system, user } }`
- 이를 통해 스테이지 전체 시간 중 LLM 대기/추론에 소요된 비중을 분리해 분석할 수 있습니다.
  - 추가 팁: 프로파일러의 `persona_llm.*.corr_userchars_duration` 값이 높다면(>0.6), 프롬프트 길이 축소가 지연 개선에 직접적 효과가 있음을 시사합니다.

#### 프롬프트 압축(Compaction) 환경변수

- `SYNTHESIS_SECTION_MAX_CHARS` (기본 1200, **권장 900**)
  - synthesis 퍼소나가 LLM에 전달하는 `Thesis`/`Antithesis` 텍스트를 섹션별로 이 최대 글자수에 맞춰 앞·뒤를 남기고 중간을 요약 표식으로 축약합니다.
  - 효과: 프롬프트 크기 축소 → 추론 시간 단축, 실패율(타임아웃 등) 감소 가능
  - **실험 결과(2025-10-26)**: 3점 스윕 테스트에서 **900**으로 설정 시
    - synthesis 성공률: 0.5 → **1.0** (100%, 2배 향상)
    - 평균 추론 시간: 21.4s → **17.3s** (19% 단축)
    - 평균 프롬프트 크기: 1569자 → **1175자** (25% 축소)
  - 추가 확인(2025-10-26 05:50): 단일 추가 테스트에서 **800**도 성공률 1.0을 유지하며 평균 지연이 더 낮게 측정되는 경우가 있었음. 네트워크/모델 상태 변동성이 크므로 다회 반복 실험이 권장됩니다. 기본값은 **900**을 유지하되, 고지연 환경에서는 **800**도 고려해보세요.
  - 권장: **900** (최적 균형점), 극단 압축 필요 시 800까지 테스트 가능

- `SYNTHESIS_DYNAMIC_COMPACTION` (기본 1=활성)
  - 설명: 사용자 프롬프트 전체 길이가 목표치를 초과하면 섹션별 최대 글자수를 비율로 자동 축소합니다.
  - 관련: `SYNTHESIS_USER_PROMPT_TARGET_CHARS`와 함께 동작

- `SYNTHESIS_USER_PROMPT_TARGET_CHARS` (기본 2400)
  - 설명: synthesis 사용자 프롬프트(Thesis+Antithesis+지시문)의 목표 최대 글자수
  - 효과: LLM 지연/타임아웃 리스크 추가 완화

- `SYNTHESIS_RETRY_MAX` (기본 1), `SYNTHESIS_RETRY_BACKOFF_SEC` (기본 2.0), `SYNTHESIS_RETRY_COMPACTION_STEP` (기본 200)
  - 설명: LLM 호출 실패 시 더 강한 압축으로 재시도합니다. 재시도 간 백오프 대기 포함

- `SYNTHESIS_TIMEOUT_SEC` (기본 30)
  - 설명: LLM HTTP 호출 타임아웃(초). 로컬 프록시/원격 API 환경에서 지연이 클 때 단축 가능
  
- `THESIS_LEARNING_MAX_CHARS` (기본 1000)
  - thesis 퍼소나의 few-shot/learning 컨텍스트가 과도하게 길어지는 경우 앞·뒤를 남기고 축약합니다.
  - 효과: 초기 제안 초안 생성 시 불필요한 토큰 낭비 감소

- `ANTITHESIS_SOURCE_MAX_CHARS` (기본 1200)
  - antithesis 퍼소나에서 입력으로 사용하는 thesis 초안이 과도하게 길 때 축약합니다.
  - 효과: 검증 단계에서 지연/타임아웃 리스크 감소

### 2) 엣지 케이스 테스트 (test_edge_cases.py)

- 시나리오:
  1. 매우 긴 입력 처리 안정성 확인
  2. 메타인지 이벤트 로깅 검증(도메인/confidence 합리성 확인)
  3. 저품질 유도 시 세컨드패스(second_pass) 발생 확인
- 실패 시 프로세스 종료코드 1 반환

### 3) AGI 점수 산출 (agi_score.py)

### 4) 프롬프트 압축 스윕 (prompt_compaction_sweep.py)

- 목적: 압축 강도(환경변수 조합)에 따른 성능/성공률 변화를 빠르게 비교합니다.
- 기본 동작: `SYNTHESIS_SECTION_MAX_CHARS=1200,1000` × `THESIS_LEARNING_MAX_CHARS=1000` × `ANTITHESIS_SOURCE_MAX_CHARS=1200`
- 사용 예시:
  - 드라이런(실행 계획만 출력):
    - `--dryrun`
  - synthesis만 1000으로 단일 실행:
    - `--synth-values 1000`
  - synthesis 1200,1000,900 / thesis 1000 / antithesis 1200:
    - `--synth-values 1200,1000,900`
- 출력: `outputs/prompt_compaction_sweep_<ts>.json` + 동명 `.md` 표 요약

- 최근 작업(최대 50개)을 기준으로 다음 지표를 산출합니다.
  - Autonomy: 위임 권고 발생 비율이 낮을수록 높음
  - Learning rate: learning 이벤트 발생 비율
  - Adaptation rate: second_pass 이벤트 발생 비율
  - Evidence rate: 평가에서 `evidence_ok=True` 비율
  - Overall AGI Score: 가중 합(0.35/0.35/0.2/0.1)
- 출력:
  - `outputs/agi_score_summary.json`
  - `outputs/agi_score_report.md`

## 메타인지 도구 가용성

- 메타인지에 제공되는 도구 목록은 레지스트리에서 동적으로 산출됩니다.
  - `rag`: `RAG_DISABLE=1` 시 목록에서 제외
  - `websearch`, `fileio`, `codeexec`, `tabular`: 개념적으로 항상 포함(일부는 오프라인 더미 동작일 수 있음)

## 문제 해결 팁

- JSONL 파싱 문제: JSONL 포맷이므로 한 줄씩 `json.loads`로 처리하세요.
- RAG 히트 없음: 의도된 더미 동작이며, `RAG_DISABLE`로 제어합니다.
- LLM 호출 실패: LLM 미연결 시 휴리스틱으로 폴백됩니다(정상 동작).
  - 세부 진단: `persona_llm_end.ok=false` 또는 `error` 필드를 확인해 원인을 파악하세요. 프롬프트 길이(`prompt_chars`)도 함께 참고하면 효과적입니다.
  - 로컬 프록시 포트 불일치 점검: 시스템 기본은 `http://localhost:8080`을 사용합니다. 8090으로 띄우는 스크립트와 혼용되면 실패율이 증가할 수 있습니다.
    - 헬스체크 예: `GET http://localhost:8080/health` 응답이 200이어야 정상입니다.

## 확장 포인트

- 파이프라인 내부 구간별 상세 타이밍 로깅(별도 ledger 이벤트 추가)
- Persona 선택/위임 자동화(현재는 경고 이벤트까지만 로깅)
- 툴 가용성 시뮬레이션을 위한 환경 플래그 확대
