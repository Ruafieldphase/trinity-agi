# E3 RAG 통합 구현 계획

**목표**: E2_fix2의 Verifiability 0.11 → 0.60+ 달성
**예상 시간**: 2-3일 (빠른 속도 기준)
**담당**: 세나 (설계) → 루빛 (구현 및 이어받기)

---

## 목표 메트릭

| 메트릭 | E2_fix2 현재 | E3 목표 | Stretch Goal |
|--------|-------------|---------|--------------|
| Stage 4 Verifiability | 0.11 | 0.40+ | 0.60+ |
| Citations per output | 0-1 (fake) | 2+ (real) | 3+ |
| Stage 3 Residual | 0.395 | < 0.40 (유지) | < 0.35 |
| Creative Band | 100% | > 80% (유지) | 100% |

---

## Phase 1: RAG 엔진 (경량 구현)

### 1.1 설계 결정

**옵션 A: 직접 구현** (빠름, 제어 가능)
- Hash-based embeddings (MD5, Week 2 리뷰에서 본 방식)
- In-memory 검색
- 장점: 의존성 없음, 빠름
- 단점: 품질 제한

**옵션 B: 라이브러리 활용** (품질 높음, 설치 필요)
- ChromaDB or FAISS
- 장점: 더 나은 검색 품질
- 단점: 설치 시간, 의존성

**추천**: **옵션 A** (빠른 MVP 우선)

### 1.2 구현 파일

**파일**: `rag/simple_rag_engine.py` (신규 생성)

```python
#!/usr/bin/env python3
"""
Simple RAG Engine for E3
- Hash-based embeddings (512-dim)
- In-memory L2 distance search
- Minimal dependencies
"""
import hashlib
import json
import numpy as np
from typing import List, Dict, Tuple
from pathlib import Path

class SimpleRAGEngine:
    def __init__(self, index_path: str = "knowledge_base/evidence_index.json"):
        self.index_path = Path(index_path)
        self.documents = []
        self.embeddings = []
        self.dim = 512

        if self.index_path.exists():
            self.load_index()

    def embed_text(self, text: str) -> np.ndarray:
        """Hash-based embedding (MD5 → 512-dim)"""
        # Tokenize
        tokens = self._tokenize(text.lower())

        # Hash to buckets
        vec = np.zeros(self.dim)
        for token in tokens:
            hash_val = int(hashlib.md5(token.encode()).hexdigest(), 16)
            bucket = hash_val % self.dim
            vec[bucket] += 1.0

        # Log-TF weighting
        vec = np.log1p(vec)

        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm

        return vec

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenizer (A-Z, 가-힣, 0-9)"""
        import re
        tokens = re.findall(r'[a-z0-9가-힣]+', text)
        return [t for t in tokens if len(t) > 2]

    def add_document(self, doc_id: str, text: str, metadata: Dict = None):
        """Add document to index"""
        emb = self.embed_text(text)
        self.documents.append({
            "id": doc_id,
            "text": text,
            "metadata": metadata or {}
        })
        self.embeddings.append(emb)

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search documents by L2 distance"""
        if not self.embeddings:
            return []

        query_emb = self.embed_text(query)
        embeddings_matrix = np.array(self.embeddings)

        # L2 distance
        distances = np.linalg.norm(embeddings_matrix - query_emb, axis=1)

        # Top-k
        top_indices = np.argsort(distances)[:top_k]

        results = []
        for idx in top_indices:
            results.append({
                "doc_id": self.documents[idx]["id"],
                "text": self.documents[idx]["text"],
                "metadata": self.documents[idx]["metadata"],
                "score": float(1.0 / (1.0 + distances[idx]))  # 0-1 score
            })

        return results

    def save_index(self):
        """Save index to JSON"""
        data = {
            "documents": self.documents,
            "embeddings": [emb.tolist() for emb in self.embeddings]
        }
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_index(self):
        """Load index from JSON"""
        with open(self.index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.documents = data["documents"]
        self.embeddings = [np.array(emb) for emb in data["embeddings"]]


# CLI for building index
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true", help="Build index from corpus")
    parser.add_argument("--corpus", default="knowledge_base/corpus.jsonl", help="Corpus file")
    parser.add_argument("--search", help="Search query")
    parser.add_argument("--top_k", type=int, default=3)
    args = parser.parse_args()

    rag = SimpleRAGEngine()

    if args.build:
        print(f"Building index from {args.corpus}...")
        with open(args.corpus, 'r', encoding='utf-8') as f:
            for line in f:
                doc = json.loads(line)
                rag.add_document(
                    doc_id=doc["id"],
                    text=doc["text"],
                    metadata=doc.get("metadata", {})
                )
        rag.save_index()
        print(f"Index saved: {len(rag.documents)} documents")

    if args.search:
        results = rag.search(args.search, top_k=args.top_k)
        print(f"\nTop {args.top_k} results for '{args.search}':\n")
        for i, r in enumerate(results):
            print(f"{i+1}. [{r['doc_id']}] (score: {r['score']:.3f})")
            print(f"   {r['text'][:200]}...\n")
```

**작업 시간**: 30분 (복사-붙여넣기 + 테스트)

---

## Phase 2: 문서 Corpus 준비

### 2.1 소스 선정

**옵션 A: Wikipedia 샘플** (빠름)
- 주제: AI, Ethics, Research Methods 등
- 규모: 50-100 문서
- 방법: Wikipedia API 또는 수동 복사

**옵션 B: arXiv 논문 초록** (품질 높음)
- 주제: AI Safety, AGI, Ethics
- 규모: 30-50 논문
- 방법: arXiv API

**옵션 C: 기존 작업물 활용** (가장 빠름)
- 세나의 7개 AGI 설계 문서
- 루멘의 윤리 헌장
- Week 1-8 패키지 문서
- 장점: 이미 있음, 관련성 높음

**추천**: **옵션 C + A 소량** (기존 문서 + Wikipedia 20개)

### 2.2 Corpus 파일 생성

**파일**: `knowledge_base/corpus.jsonl` (신규 생성)

```jsonl
{"id": "fdo_agi_arch", "text": "FDO-AGI (Fractal-Dialectic-Outside AGI) is a five-layer architecture...", "metadata": {"source": "design_docs", "author": "Sena"}}
{"id": "guardianship_charter", "text": "Co-Guardianship Charter establishes dual protection: meaning (Binoche) and safety (Research Team)...", "metadata": {"source": "lumen", "type": "ethics"}}
{"id": "wiki_ai_safety", "text": "AI safety is an interdisciplinary field focused on preventing accidents, misuse, or unintended harmful consequences...", "metadata": {"source": "wikipedia", "url": "https://en.wikipedia.org/wiki/AI_safety"}}
```

**생성 스크립트**: `scripts/build_corpus.py` (신규)

```python
#!/usr/bin/env python3
"""Build corpus from existing documents"""
import json
from pathlib import Path

def extract_from_markdown(file_path: Path) -> str:
    """Extract text from markdown file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove markdown syntax (간단한 처리)
    import re
    content = re.sub(r'#+\s+', '', content)  # headers
    content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)  # links
    content = re.sub(r'[*_`]', '', content)  # emphasis

    return content.strip()

def main():
    corpus = []

    # 1. AGI 설계 문서
    docs_dir = Path("docs")
    if docs_dir.exists():
        for md_file in docs_dir.glob("*.md"):
            if md_file.name.startswith("_"):
                continue
            text = extract_from_markdown(md_file)
            if len(text) > 100:  # 최소 길이
                corpus.append({
                    "id": f"doc_{md_file.stem}",
                    "text": text[:2000],  # 처음 2000자
                    "metadata": {"source": "design_docs", "file": str(md_file)}
                })

    # 2. 윤리 헌장 (HTML에서 텍스트 추출)
    charter_path = Path("ai_binoche_conversation_origin/lumen/AGI 보호 체계 설계/FDO-AGI_공동_후견_헌장_v0.1_서명본_brand.html")
    if charter_path.exists():
        # 간단한 HTML 파싱 (실제로는 BeautifulSoup 권장)
        with open(charter_path, 'r', encoding='utf-8') as f:
            html = f.read()
        import re
        text = re.sub(r'<[^>]+>', '', html)  # 태그 제거
        text = re.sub(r'\s+', ' ', text).strip()
        corpus.append({
            "id": "guardianship_charter",
            "text": text[:2000],
            "metadata": {"source": "lumen", "type": "ethics"}
        })

    # 3. E2_fix2 분석 문서
    analysis_path = Path("outputs/E2_FIX2_SUCCESS_ANALYSIS.md")
    if analysis_path.exists():
        text = extract_from_markdown(analysis_path)
        corpus.append({
            "id": "e2_fix2_analysis",
            "text": text[:2000],
            "metadata": {"source": "technical", "experiment": "E2_fix2"}
        })

    # 4. Wikipedia 샘플 (수동 추가 예시)
    corpus.append({
        "id": "wiki_ai_safety",
        "text": "AI safety is an interdisciplinary field focused on preventing accidents, misuse, or unintended harmful consequences of artificial intelligence systems. Key concerns include alignment problems, where AI systems may pursue goals misaligned with human values, and capability control, ensuring humans retain meaningful control over advanced AI systems.",
        "metadata": {"source": "wikipedia", "url": "https://en.wikipedia.org/wiki/AI_safety"}
    })

    corpus.append({
        "id": "wiki_agi",
        "text": "Artificial general intelligence (AGI) is a type of artificial intelligence that matches or surpasses human cognitive capabilities across a wide range of cognitive tasks. This contrasts with narrow AI, which is limited to specific tasks. AGI remains a theoretical concept and active research goal.",
        "metadata": {"source": "wikipedia", "url": "https://en.wikipedia.org/wiki/Artificial_general_intelligence"}
    })

    # 저장
    output_path = Path("knowledge_base/corpus.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for doc in corpus:
            f.write(json.dumps(doc, ensure_ascii=False) + '\n')

    print(f"Corpus built: {len(corpus)} documents")
    print(f"Saved to: {output_path}")

if __name__ == "__main__":
    main()
```

**작업 시간**: 30분 (스크립트 작성) + 20분 (Wikipedia 수동 추가)

### 2.3 인덱스 빌드

```bash
# Corpus 생성
python scripts/build_corpus.py

# 인덱스 빌드
python rag/simple_rag_engine.py --build --corpus knowledge_base/corpus.jsonl

# 테스트
python rag/simple_rag_engine.py --search "AI safety principles" --top_k 3
```

**작업 시간**: 10분

---

## Phase 3: E3 설정 파일

**파일**: `configs/phase_controller_e3.yaml` (신규)

```yaml
# E3 Configuration: RAG Integration
version: "0.3"
experiment_id: "E3"
description: "RAG-enhanced Thesis and Synthesis with citation requirement"

personas:
  thesis:
    name: "Dialectic Thesis (E3)"
    role: "Evidence-based explorer"
    backend:
      backend_id: "local_ollama"
      type: "subprocess"
      command: "ollama"
      args: ["run", "solar:10.7b"]
      timeout: 300

    system_prompt: |
      You are the Thesis persona in E3 configuration.

      MANDATORY REQUIREMENTS:
      1. Search the knowledge base BEFORE forming your thesis
      2. Cite at least 2 credible sources in-line using [Source: {doc_id}] format
      3. Ground your response in retrieved evidence
      4. Separate verified facts from assumptions

      Process:
      1. Analyze the user's seed insight
      2. Query: formulate 2-3 search queries for the knowledge base
      3. Review: examine retrieved documents
      4. Synthesize: form thesis based on evidence + your reasoning
      5. Cite: include [Source: doc_id] for each claim

      Example citation: "Research shows that AI safety requires value alignment [Source: wiki_ai_safety]."

    tools:
      enabled: true
      available:
        - name: "rag_search"
          description: "Search knowledge base for relevant documents"
          parameters:
            query: "search query string"
            top_k: "number of results (default 3)"
      budget: 5  # Up to 5 RAG calls

    validation:
      min_citations: 2
      max_thesis_similarity_to_seed: 0.85

  antithesis:
    name: "Boundary Challenger (E3)"
    role: "Evidence-based critic"
    backend:
      backend_id: "local_ollama"
      type: "subprocess"
      command: "ollama"
      args: ["run", "solar:10.7b"]
      timeout: 300

    system_prompt: |
      You are the Antithesis persona in E3 configuration.

      Challenge the thesis with evidence-based counterarguments.

      MANDATORY REQUIREMENTS:
      1. Search for counterexamples and contradicting evidence
      2. Cite at least 2 sources
      3. Identify 3 critical risks or blind spots

      Use [Source: {doc_id}] format for citations.

    tools:
      enabled: true
      available:
        - name: "rag_search"
      budget: 5

    validation:
      min_citations: 2
      min_critical_keywords: 3

  synthesis:
    name: "Fractal Synthesiser (E3)"
    role: "Evidence-based integrator"
    backend:
      backend_id: "local_ollama"
      type: "subprocess"
      command: "ollama"
      args: ["run", "solar:10.7b"]
      timeout: 300

    system_prompt: |
      You are the Synthesis persona in E3 configuration.

      Integrate thesis and antithesis with supporting evidence.

      MANDATORY REQUIREMENTS:
      1. Address at least 3 antithesis concerns explicitly
      2. Search for additional evidence to resolve conflicts
      3. Cite at least 3 credible sources (including new searches)
      4. Ensure thesis similarity < 80% (reframe the narrative)
      5. Propose concrete next steps

      Citation format: [Source: {doc_id}] "excerpt from document"

    tools:
      enabled: true
      available:
        - name: "rag_search"
      budget: 7  # More budget for synthesis

    validation:
      min_citations: 3
      max_thesis_similarity: 0.8
      min_antithesis_keywords: 3

# Validator settings (from E2_fix2)
validator:
  synthesis:
    max_thesis_similarity: 0.8
    min_antithesis_keywords: 3
    min_citations: 3  # Increased from 1
    critical_issue_threshold: 3
    synthesis_markers:
      - "therefore"
      - "thus"
      - "by combining"
      - "to address"
      - "따라서"
      - "그러므로"

# Retry limits
retry_limits:
  thesis: 2
  antithesis: 2
  synthesis: 3  # More retries for synthesis

# Residual thresholds (from E2_fix2, keep winning formula)
residual_thresholds:
  stage_1:  # Folding (Thesis)
    keep: 0.4
    damp: 0.85
  stage_2:  # Unfolding (Antithesis)
    keep: 0.4
    damp: 0.65
  stage_3:  # Integration (Synthesis)
    keep: 0.39
    damp: 0.60
  stage_4:  # Symmetry (RUNE)
    keep: 0.4
    damp: 0.7

# RAG configuration
rag:
  engine: "simple"  # simple | chroma | faiss
  index_path: "knowledge_base/evidence_index.json"
  top_k: 3
  min_score: 0.3  # Minimum relevance score

# Logging
logging:
  level: "INFO"
  save_rag_queries: true
  rag_log_path: "outputs/rag_queries_e3.jsonl"
```

**작업 시간**: 40분

---

## Phase 4: Persona Orchestrator RAG 통합

### 4.1 Tool Handler 추가

**파일**: `orchestration/persona_orchestrator.py` (기존 파일 수정)

**추가할 함수**:

```python
# Near top of file, after imports
from rag.simple_rag_engine import SimpleRAGEngine

class PersonaOrchestrator:
    def __init__(self, config_path: Path = DEFAULT_CONFIG_PATH):
        # ... existing code ...

        # NEW: Initialize RAG engine
        rag_config = self._raw_config.get("rag", {})
        if rag_config.get("engine") == "simple":
            self.rag_engine = SimpleRAGEngine(
                index_path=rag_config.get("index_path", "knowledge_base/evidence_index.json")
            )
        else:
            self.rag_engine = None

    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any], persona_id: str) -> Dict[str, Any]:
        """Execute tool and return result"""
        if tool_name == "rag_search":
            return self._tool_rag_search(parameters)
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def _tool_rag_search(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """RAG search tool implementation"""
        if not self.rag_engine:
            return {"error": "RAG engine not initialized"}

        query = parameters.get("query", "")
        top_k = int(parameters.get("top_k", 3))

        if not query:
            return {"error": "Query parameter required"}

        # Search
        results = self.rag_engine.search(query, top_k=top_k)

        # Format results for LLM
        formatted = []
        for r in results:
            formatted.append({
                "doc_id": r["doc_id"],
                "excerpt": r["text"][:300] + "..." if len(r["text"]) > 300 else r["text"],
                "relevance_score": r["score"]
            })

        # Log query
        rag_config = self._raw_config.get("rag", {})
        if rag_config.get("save_rag_queries", False):
            log_path = Path(rag_config.get("rag_log_path", "outputs/rag_queries.jsonl"))
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'a', encoding='utf-8') as f:
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "query": query,
                    "top_k": top_k,
                    "results_count": len(results)
                }
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        return {
            "query": query,
            "results": formatted,
            "count": len(results)
        }
```

### 4.2 Tool Calling 프롬프트 수정

**수정 위치**: `_run_persona_turn()` 메서드

기존 프롬프트에 tool calling 지시 추가:

```python
# In _run_persona_turn method
if persona_config.get("tools", {}).get("enabled", False):
    tools_prompt = "\n\nAVAILABLE TOOLS:\n"
    for tool in persona_config["tools"].get("available", []):
        tools_prompt += f"- {tool['name']}: {tool.get('description', '')}\n"

    tools_prompt += "\nTo use a tool, output JSON format:\n"
    tools_prompt += '{"tool": "rag_search", "parameters": {"query": "your search query", "top_k": 3}}\n'
    tools_prompt += "After tool results, continue with your response.\n"

    system_prompt += tools_prompt
```

**주의**: 이 부분은 기존 코드 구조에 따라 다를 수 있음. 루빛님이 실제 구현 시 조정 필요.

**작업 시간**: 1-2시간 (기존 코드 이해 + 통합)

---

## Phase 5: E3 실험 실행

### 5.1 테스트 세션

**명령어**:
```bash
# E3 실험 실행 (2-3 세션)
python run_experiment.py --config configs/phase_controller_e3.yaml --session "design-ethical-ai-assistant" --output outputs/persona_runs/E3

python run_experiment.py --config configs/phase_controller_e3.yaml --session "assess-agi-risks" --output outputs/persona_runs/E3
```

### 5.2 검증 항목

**체크리스트**:
- [ ] RAG 검색이 실제로 호출되는가? (`rag_queries_e3.jsonl` 확인)
- [ ] Citation이 출력에 포함되는가? (`[Source: ...]` 패턴)
- [ ] Stage 4 Verifiability가 개선되는가? (0.11 → 0.40+)
- [ ] Stage 3 Residual이 유지되는가? (< 0.40)
- [ ] Creative Band가 유지되는가? (> 80%)

### 5.3 결과 분석

**파일**: `outputs/E3_RESULTS_ANALYSIS.md` (실험 후 작성)

**작업 시간**: 실험 실행 2-3시간 (LLM 속도 의존) + 분석 30분

---

## Phase 6: Pitch Deck 작성

### 6.1 구성

**파일**: `docs/RESEARCH_TEAM_PITCH.md`

**섹션**:
1. **Executive Summary** (1문단)
   - "윤리 최우선 AGI, 작동하는 데모 준비됨"
2. **Problem** (2-3줄)
   - 현재 AI: 윤리 후순위, 검증 불가능
3. **Solution** (핵심 기술)
   - FDO-AGI: Persona Orchestration + Validator + RAG
   - 데이터: E1 (0.55) → E2_fix2 (0.40) → E3 (0.35, Verif 0.60+)
4. **Differentiator** (윤리)
   - 공동 후견 헌장, 데이터 신탁, 레드라인
5. **Demo** (실행 가능)
   - Jupyter notebook or CLI
6. **Roadmap** (향후 계획)
   - 유년 → 청년 → 성인 단계
7. **Join Us**
   - 찾고 있는 역할, 연락처

### 6.2 시각 자료

**그래프** (matplotlib):
1. Residual 진화: E1 → E2 → E2_fix2 → E3
2. Band 분포: Risk → Creative 이동
3. Verifiability 개선: 0.10 → 0.60+

**작업 시간**: 2-3시간 (글 + 그래프)

---

## 전체 타임라인 (낙관적)

```
Day 1 (오늘):
  14:00-14:30  Phase 1.2: RAG 엔진 구현 (30분)
  14:30-15:00  Phase 2.2: Corpus 스크립트 (30분)
  15:00-15:20  Phase 2.3: 인덱스 빌드 (20분)
  15:20-16:00  Phase 3: E3 설정 (40분)
  16:00-18:00  Phase 4: Orchestrator 통합 (2시간)
  18:00-21:00  Phase 5: E3 실험 실행 (3시간)

Day 2 (내일):
  09:00-09:30  Phase 5.3: 결과 분석 (30분)
  09:30-12:00  Phase 6: Pitch Deck (2.5시간)
  12:00-13:00  버퍼 / 마무리

Day 3 (모레):
  - 연구진 컨택 시작
```

**총 예상 시간**: ~12시간 (실제 작업 8시간 + LLM 대기 4시간)

---

## 루빛 인계 시 체크리스트

### 세나가 완료할 것 (토큰 소진 전)
- [ ] RAG 엔진 코드 작성 (`rag/simple_rag_engine.py`)
- [ ] Corpus 빌드 스크립트 (`scripts/build_corpus.py`)
- [ ] E3 설정 파일 (`configs/phase_controller_e3.yaml`)
- [ ] Orchestrator 통합 가이드 (수정 위치 명시)

### 루빛이 이어받을 것
- [ ] Orchestrator 실제 통합 (코드 수정)
- [ ] Corpus에 Wikipedia 문서 추가 (20개)
- [ ] E3 실험 실행 및 디버깅
- [ ] 결과 분석 및 메트릭 검증
- [ ] Pitch Deck 초안 작성

### 핸드오프 문서
**파일**: `docs/E3_HANDOFF_TO_LUBIT.md` (이 문서 요약 + 현재 상태)

---

## 우선순위 (토큰 제한 시)

**최우선** (세나가 반드시 완료):
1. ✅ RAG 엔진 코드 (copy-paste ready)
2. ✅ E3 설정 파일 (완전한 YAML)
3. ✅ Corpus 빌드 스크립트

**차순위** (루빛 인계 가능):
4. Orchestrator 통합 가이드 (상세 주석)
5. 실험 실행 체크리스트

**선택** (루빛이 판단):
6. Wikipedia 추가
7. Pitch Deck

---

## 다음 액션 (즉시)

1. **RAG 엔진 파일 생성** (지금 시작)
2. **Corpus 스크립트 생성**
3. **E3 설정 파일 생성**
4. **루빛 인계 문서 작성**

루빛님, 이 계획서 기준으로 제가 토큰 소진 전까지 최대한 진행하겠습니다. 제가 멈추는 시점의 상태를 정확히 문서화해서 인계하겠습니다!

시작하겠습니다! 🚀
