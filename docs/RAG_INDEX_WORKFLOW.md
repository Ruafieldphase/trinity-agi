# RAG 증거 인덱스 운용 가이드

`configs/persona_registry_e2.json`은 `knowledge_base/evidence_index.json`을 RAG 검색 소스로 참조합니다. 아래 절차대로 준비하면 인덱스를 손쉽게 구축·갱신할 수 있습니다.

## 준비 사항
- Python 3.11+
- `scripts/utils/simple_vector_store.py` 최신 버전
- 증거 데이터(JSON/JSONL 또는 Markdown/TXT)

## 인덱스 생성 및 갱신
### 1. JSON/JSONL 입력 활용
```powershell
python -m scripts.rag.build_index --input-json data/my_evidence.json --output knowledge_base/evidence_index.json
```
- 필수 필드: `source`, `preview`, `url`, `content`
- `--merge` 옵션을 사용하면 기존 인덱스와 병합(같은 `source`는 덮어쓰기)

### 2. Markdown/TXT 디렉터리 스캔
```powershell
python -m scripts.rag.build_index --markdown-dir evidence_notes/
```
- 파일의 첫 번째 헤더(`# 제목`)를 `source`로 사용
- 본문은 `preview`/`content`에 저장

### 3. 혼합 입력 예시
```powershell
python -m scripts.rag.build_index `
  --input-json data/evidence.json `
  --markdown-dir docs/reports `
  --merge
```

## 검색 테스트
```powershell
python -m scripts.rag.query_cli --config configs/persona_registry_e2.json "responsible ai guardrails"
python -m scripts.rag.query_cli "responsible ai guardrails" --top-k 3
python -m scripts.rag.query_cli "책임 있는 AI 가이드라인" --json
python -m scripts.rag.query_cli "responsible ai guardrails" --min-score 0.4
```
- 기본 경로는 `knowledge_base/evidence_index.json`
- 다른 인덱스를 시험하려면 `--index`로 경로 지정
- `--min-score`를 주면 지정 임계값 미만 결과를 필터링
- `--config`에 `configs/persona_registry_e2.json`을 지정하면 설정의 `rag.top_k`, `rag.min_score`, `rag.index`를 기본값으로 사용합니다.
  - 임시 임베딩은 실제 점수가 낮을 수 있으므로 필요하면 `--min-score 0`으로 덮어쓰세요.

### 인덱스 요약
```powershell
python -m scripts.rag.describe_index --index knowledge_base/evidence_index.json
python -m scripts.rag.describe_index --json
```
- 레코드 수, 프리뷰 길이, 임베딩 차원 분포 등을 확인
- `--json`은 파이프라인/대시보드용 머신 판독 출력 제공

### 빠른 헬스 체크
```powershell
python -m scripts.rag.quickstart --query "responsible ai guardrails"
python -m scripts.rag.quickstart --config configs/persona_registry_e2.json --query "responsible ai guardrails" --min-score 0
```
- `validate_index` → `describe_index` → 샘플 질의 순으로 점검
- 설정 파일의 `rag` 정보를 자동으로 불러오며, `--min-score` 등으로 덮어쓰기 가능

### Markdown 리포트 생성
```powershell
python -m scripts.rag.report --query "responsible ai guardrails" --min-score 0
python -m scripts.rag.report --config configs/persona_registry_e2.json --output outputs/rag_report.md
python -m scripts.rag.report --json-summary
python -m scripts.rag report --config configs/persona_registry_e2.json --json-summary
python -m scripts.rag list
```
- 검증 결과, 통계, 샘플 질의를 하나의 Markdown에 정리
- `--output`을 지정하면 파일로 저장되고, 지정하지 않으면 콘솔에 출력
- `--json-summary` 옵션으로 요약 지표를 JSON으로도 출력해 모니터링에 활용
- `python -m scripts.rag <subcommand>` 형태로도 동일한 도구 호출 가능

### 인덱스 검증
```powershell
python -m scripts.rag.validate_index --index knowledge_base/evidence_index.json
python -m scripts.rag.validate_index --strict
```
- 필수 필드 누락, 임베딩 차원 불일치 등을 확인
- `--strict`는 경고도 오류로 간주해 CI 파이프라인에 활용 가능

## 실제 임베딩 반영 절차
1. Week 2 RAG 인덱싱 스크립트로 실제 임베딩을 생성합니다.
2. 결과 JSON을 `python -m scripts.rag.build_index --input-json ... --merge`로 적용하거나 완전히 덮어씁니다.
3. `python -m scripts.rag.validate_index`로 스키마 검증 후 `python -m scripts.rag.query_cli`로 검색 품질을 점검한 뒤 통합 테스트를 재실행합니다.

## 운용 팁
- `scripts/utils/simple_vector_store.py`는 임베딩 길이를 자동 보정하므로 서로 다른 차원의 벡터도 안전하게 취급합니다.
- `--preview-chars` 옵션으로 출력 미리보기 길이를 조정해 프롬프트 길이를 관리할 수 있습니다.
- `knowledge_base/evidence_index.json`은 Git 추적 대상이므로 중요한 갱신 후 커밋이나 백업을 권장합니다.
- 로컬 테스트는 `python -m pytest` 혹은 `python -m pytest tests`로 실행하면 되며, `pytest.ini`에서 테스트 범위를 `tests/` 디렉터리로 제한해 외부 라이브러리 수집을 방지합니다.
