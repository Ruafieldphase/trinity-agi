# AGI 설계 문서 03: 도구 레지스트리 및 발견 시스템 v1.0

**작성자**: 세나 (Sena)
**작성일**: 2025-10-12
**상태**: 초안

---

## 1. 목표

현재 PersonaOrchestrator는 **고정된 백엔드(LLM)**만 호출합니다.
AGI로 나아가려면 페르소나가 **필요한 도구를 자동으로 선택하고 조합**할 수 있어야 합니다.

**핵심 기능**:
- 도구 메타데이터 관리 (비용, 신뢰도, 지연시간)
- 요청에서 필요한 도구 자동 탐지
- 도구 실패 시 대체 도구 선택
- 복잡한 작업을 도구 조합으로 분해

---

## 2. 스코프

### v1.0 포함 ✅
- JSON 기반 도구 레지스트리
- 규칙 기반 도구 선택 (키워드 매칭)
- 기본 폴백 메커니즘
- 도구 5종 지원: LLM, 파일읽기, 웹검색, 계산, 실행
- BQI/RUNE 보조 노드: Clipboard 오케스트레이션에서 META/RUNE 단계가 동일한 레지스트리 형식을 공유하도록 스펙 정의

### v2.0 이후 ⏳
- LLM 기반 도구 선택 (function calling)
- 도구 간 파이프라인 자동 구성
- 병렬 실행 최적화
- 동적 도구 등록/제거

---

## 3. 도구 레지스트리 스키마

### 3.1 ToolDefinition
```json
{
  "tool_id": "web_search",
  "name": "Web Search",
  "description": "Search the web for real-time information",
  "category": "information_retrieval",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "required": true},
      "max_results": {"type": "integer", "default": 5}
    }
  },
  "output_schema": {
    "type": "array",
    "items": {"type": "object"}
  },
  "execution": {
    "type": "subprocess",
    "command": "python",
    "args": ["scripts/tools/web_search.py", "--query", "{query}"]
  },
  "metadata": {
    "cost_level": "medium",
    "reliability": 0.9,
    "avg_latency_seconds": 3.5,
    "requires_network": true,
    "requires_api_key": true
  },
  "fallback_tools": ["local_search", "llm_knowledge"],
  "tags": ["web", "search", "realtime"]
}
```

### 3.2 Tool Categories
```
- llm: 텍스트 생성 (기존 personas)
- file_ops: Read, Write, Edit
- information_retrieval: 웹검색, DB쿼리
- computation: 계산, 통계, 코드 실행
- communication: 이메일, 슬랙, API 호출
- analysis: 데이터 분석, 시각화
- orchestration: BQI, RUNE와 같이 오케스트레이션 보조 노드
```

### 3.3 Clipboard Helper Tools (META/RUNE 노드)
```json
{
  "tool_id": "bqi_analyzer",
  "name": "Binoche Question Interface",
  "description": "Extract rhythm coordinates (time/space/agent/emotion) from the user's request",
  "category": "orchestration",
  "execution": {
    "type": "python_function",
    "module": "scripts.rune.bqi_adapter",
    "function": "analyze_question"
  },
  "metadata": {
    "cost_level": "low",
    "reliability": 0.98,
    "avg_latency_seconds": 0.2,
    "requires_network": false
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "rhythm_phase": {"type": "string"},
      "emotion": {"type": "object"},
      "priority": {"type": "integer"}
    }
  },
  "tags": ["bqi", "meta", "coordinate"]
}
```

```json
{
  "tool_id": "rune_reporter",
  "name": "RUNE Resonance Reporter",
  "description": "Generate resonance metrics and narrative summary for the synthesis output",
  "category": "orchestration",
  "execution": {
    "type": "python_function",
    "module": "scripts.rune.analyzer",
    "function": "generate_report"
  },
  "metadata": {
    "cost_level": "medium",
    "reliability": 0.93,
    "avg_latency_seconds": 1.2,
    "requires_network": false
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "impact_score": {"type": "number"},
      "transparency": {"type": "number"},
      "reproducibility": {"type": "number"},
      "verifiability": {"type": "number"},
      "plan_adjustment": {"type": "object"}
    }
  },
  "tags": ["rune", "resonance", "qc"]
}
```

---

## 4. 도구 선택 로직

### 4.1 규칙 기반 선택 (v1.0)
```python
class ToolSelector:
    def select_tools(self, task_description: str, context: Dict) -> List[str]:
        """
        키워드 기반 도구 선택

        Example:
            "최신 AGI 연구 동향을 찾아줘"
            → keywords: ["최신", "찾아"]
            → tools: ["web_search"]

            "이 코드를 분석하고 버그를 찾아줘"
            → keywords: ["코드", "분석", "버그"]
            → tools: ["code_analyzer", "llm"]
        """
        keywords = self._extract_keywords(task_description)
        tools = []

        bqi = context.get("bqi")  # {"rhythm_phase": "...", "priority": 2, ...}
        if bqi:
            # META 단계에서 항상 BQI 분석 수행
            tools.append("bqi_analyzer")
            if bqi.get("rhythm_phase") == "integration":
                tools.append("rune_reporter")  # Synth 이후 감응 리포트 준비

        # 규칙 기반 매칭
        if any(kw in keywords for kw in ["검색", "찾아", "최신", "뉴스"]):
            tools.append("web_search")
        if any(kw in keywords for kw in ["파일", "읽어", "열어"]):
            tools.append("file_read")
        if any(kw in keywords for kw in ["계산", "평균", "합계"]):
            tools.append("calculator")
        if any(kw in keywords for kw in ["코드", "실행", "테스트"]):
            tools.append("code_executor")

        # 기본값: LLM
        if not tools or tools == ["bqi_analyzer"]:
            tools.append("llm")

        return tools

    def _extract_keywords(self, text: str) -> List[str]:
        """간단한 키워드 추출 (형태소 분석 없이)"""
        return [w.lower() for w in re.findall(r'\b[\w]+\b', text) if len(w) > 1]
```

### 4.2 비용/신뢰도 고려
```python
def filter_by_constraints(
    self,
    tool_ids: List[str],
    max_cost: str = "high",
    min_reliability: float = 0.7,
    require_network: bool = True
) -> List[str]:
    """제약 조건에 맞는 도구만 필터링"""
    cost_order = {"low": 1, "medium": 2, "high": 3}
    filtered = []

    for tid in tool_ids:
        tool = self.registry.get_tool(tid)
        if cost_order[tool.metadata["cost_level"]] > cost_order[max_cost]:
            continue
        if tool.metadata["reliability"] < min_reliability:
            continue
        if tool.metadata["requires_network"] and not require_network:
            continue
        filtered.append(tid)

    return filtered
```

### 4.3 감응 기반 위상 정렬 (PLAN 단계)
```python
class PersonaScheduler:
    def reorder_cycle(
        self,
        base_cycle: List[str],
        bqi_coordinate: Dict[str, Any],
        safety_flags: Dict[str, Any]
    ) -> List[str]:
        """
        BQI 감응 좌표와 SAFE_pre 결과를 사용하여 정반합 순서를 재배치.
        예: 감응 위상이 'integration'이고 위험도가 높으면 Synthesis를 두 번째로 이동.
        """
        order = deque(base_cycle)

        if safety_flags.get("high_risk"):
            order.rotate(-1)  # Antithesis를 먼저 호출
        if bqi_coordinate.get("rhythm_phase") == "integration":
            # Synthesis를 앞당겨 통합을 빠르게 수행
            while order[0] != "synthesis":
                order.rotate(-1)
        return list(order)
```

> `PersonaScheduler.reorder_cycle`은 PLAN 노드에서 실행되며, `ToolSelector`가 반환한 `bqi_analyzer` 결과를 입력으로 받습니다.

---

## 5. 도구 실행 및 폴백

### 5.1 ToolExecutor
```python
class ToolExecutor:
    def execute(
        self,
        tool_id: str,
        inputs: Dict[str, Any],
        max_retries: int = 2
    ) -> ToolResult:
        """도구 실행 + 자동 폴백"""
        tool = self.registry.get_tool(tool_id)

        for attempt in range(max_retries + 1):
            try:
                result = self._execute_once(tool, inputs)
                return ToolResult(success=True, output=result, tool_used=tool_id)

            except ToolExecutionError as e:
                if attempt < max_retries:
                    # 폴백 도구 시도
                    fallback_id = tool.fallback_tools[attempt] if len(tool.fallback_tools) > attempt else None
                    if fallback_id:
                        tool = self.registry.get_tool(fallback_id)
                        continue
                # 최종 실패
                return ToolResult(
                    success=False,
                    error=str(e),
                    tool_used=tool_id,
                    fallback_attempted=attempt > 0
                )

    def _execute_once(self, tool: ToolDefinition, inputs: Dict) -> Any:
        """실제 실행 로직"""
        if tool.execution["type"] == "subprocess":
            return self._run_subprocess(tool, inputs)
        elif tool.execution["type"] == "python_function":
            return self._run_python(tool, inputs)
        elif tool.execution["type"] == "api_call":
            return self._run_api(tool, inputs)
        else:
            raise ValueError(f"Unsupported execution type: {tool.execution['type']}")
```

### 5.2 ToolResult
```python
@dataclass
class ToolResult:
    success: bool
    output: Any = None
    error: str = None
    tool_used: str = None
    fallback_attempted: bool = False
    execution_time_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

## 6. PersonaOrchestrator 통합

### 6.1 도구 호출 추가
```python
class PersonaOrchestrator:
    def __init__(self, ..., tool_registry: ToolRegistry = None):
        # ... 기존 코드 ...
        self.tool_registry = tool_registry
        self.tool_selector = ToolSelector(tool_registry) if tool_registry else None
        self.tool_executor = ToolExecutor(tool_registry) if tool_registry else None

    def _run_recursive(self, seed_prompt: str, depth: int, depth_index: int) -> str:
        # ... 기존 코드 ...

        # 도구 필요 여부 판단 (추가)
        if self.tool_selector:
            required_tools = self.tool_selector.select_tools(seed_prompt, context={})

            # LLM 외 도구가 필요하면 먼저 실행
            tool_outputs = {}
            for tool_id in required_tools:
                if tool_id != "llm":
                    result = self.tool_executor.execute(tool_id, {"query": seed_prompt})
                    if result.success:
                        tool_outputs[tool_id] = result.output

            # 도구 출력을 프롬프트에 추가
            if tool_outputs:
                tool_context = "\n".join([
                    f"[Tool: {tid}]\n{output}"
                    for tid, output in tool_outputs.items()
                ])
                prompt = compose_prompt(...) + "\n\nTool outputs:\n" + tool_context

        # 기존 LLM 호출
        response = backend.generate(...)
        # ...
```

---

## 7. 기본 제공 도구 5종

### 7.1 file_read
```python
# scripts/tools/file_read.py
def file_read_tool(file_path: str, max_lines: int = 100) -> str:
    """파일 읽기"""
    path = Path(file_path)
    if not path.exists():
        raise ToolExecutionError(f"File not found: {file_path}")

    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[:max_lines])
```

### 7.2 web_search (간단한 DuckDuckGo API)
```python
# scripts/tools/web_search.py
import requests

def web_search_tool(query: str, max_results: int = 5) -> List[Dict]:
    """웹 검색 (DuckDuckGo Instant Answer API)"""
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json"}
    response = requests.get(url, params=params, timeout=10)
    data = response.json()

    results = []
    for item in data.get("RelatedTopics", [])[:max_results]:
        if "Text" in item:
            results.append({
                "title": item.get("FirstURL", ""),
                "snippet": item["Text"]
            })
    return results
```

### 7.3 calculator
```python
# scripts/tools/calculator.py
import ast
import operator

SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}

def calculator_tool(expression: str) -> float:
    """안전한 수식 계산"""
    try:
        tree = ast.parse(expression, mode='eval')
        return _eval_node(tree.body)
    except Exception as e:
        raise ToolExecutionError(f"Invalid expression: {e}")

def _eval_node(node):
    if isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.BinOp):
        op = SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError("Unsupported operator")
        return op(_eval_node(node.left), _eval_node(node.right))
    else:
        raise ValueError("Unsupported expression")
```

### 7.4 code_executor (샌드박스)
```python
# scripts/tools/code_executor.py
import subprocess
import tempfile

def code_executor_tool(code: str, language: str = "python", timeout: int = 10) -> str:
    """코드 실행 (샌드박스)"""
    if language != "python":
        raise ToolExecutionError(f"Language {language} not supported")

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        result = subprocess.run(
            ["python", temp_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout if result.returncode == 0 else result.stderr
    finally:
        Path(temp_path).unlink()
```

### 7.5 llm (기존 백엔드 래핑)
```python
def llm_tool(prompt: str, model: str = "default") -> str:
    """기존 PersonaBackend 호출"""
    # PersonaOrchestrator의 backend_factory 재사용
    backend = get_backend(model)
    return backend.generate(...)
```

---

## 8. 도구 레지스트리 파일

### configs/tool_registry.json
```json
{
  "tools": [
    {
      "tool_id": "file_read",
      "name": "File Reader",
      "description": "Read file contents from local filesystem",
      "category": "file_ops",
      "execution": {
        "type": "python_function",
        "module": "scripts.tools.file_read",
        "function": "file_read_tool"
      },
      "metadata": {
        "cost_level": "low",
        "reliability": 0.99,
        "avg_latency_seconds": 0.1,
        "requires_network": false
      },
      "fallback_tools": [],
      "tags": ["file", "read", "local"]
    },
    {
      "tool_id": "web_search",
      "name": "Web Search",
      "description": "Search the web using DuckDuckGo",
      "category": "information_retrieval",
      "execution": {
        "type": "python_function",
        "module": "scripts.tools.web_search",
        "function": "web_search_tool"
      },
      "metadata": {
        "cost_level": "medium",
        "reliability": 0.85,
        "avg_latency_seconds": 3.0,
        "requires_network": true
      },
      "fallback_tools": ["llm"],
      "tags": ["web", "search", "realtime"]
    },
    {
      "tool_id": "calculator",
      "name": "Calculator",
      "description": "Evaluate mathematical expressions safely",
      "category": "computation",
      "execution": {
        "type": "python_function",
        "module": "scripts.tools.calculator",
        "function": "calculator_tool"
      },
      "metadata": {
        "cost_level": "low",
        "reliability": 0.99,
        "avg_latency_seconds": 0.05,
        "requires_network": false
      },
      "fallback_tools": [],
      "tags": ["math", "calculation"]
    }
  ]
}
```

---

## 9. 테스트 계획

### 성공 기준
1. ✅ 도구 선택: "최신 뉴스 검색" → web_search 선택
2. ✅ 폴백: web_search 실패 → llm 자동 호출
3. ✅ 실행: calculator("2 + 3 * 4") → 14 반환
4. ✅ 통합: PersonaOrchestrator에서 도구 자동 사용

### 테스트 시나리오
```python
# 시나리오 1: 도구 선택
selector = ToolSelector(registry)
tools = selector.select_tools("최신 AGI 뉴스를 찾아줘")
assert "web_search" in tools

# 시나리오 2: 도구 실행
executor = ToolExecutor(registry)
result = executor.execute("calculator", {"expression": "10 / 2"})
assert result.success
assert result.output == 5.0

# 시나리오 3: 폴백
# web_search 실패 시뮬레이션
registry.get_tool("web_search").metadata["reliability"] = 0.0
result = executor.execute("web_search", {"query": "test"}, max_retries=1)
assert result.fallback_attempted
assert result.tool_used == "llm"
```

---

## 10. 미결정 사항

### 10.1 도구 선택 방식
- **Option A**: 규칙 기반 (v1.0, 간단, 제한적)
- **Option B**: LLM이 판단 (v2.0, 유연, 비용↑)
→ **제안**: v1.0은 A, v2.0에서 B로 전환

### 10.2 샌드박스 보안
- code_executor가 악의적 코드 실행 가능
- Docker 컨테이너 내 격리? 권한 제한?
→ **제안**: v1.0은 timeout만, v2.0에서 Docker 샌드박스

### 10.3 도구 비용 한도
- 사용자별 예산 설정? (예: 하루 $5)
- 비용 초과 시 알림? 자동 차단?
→ **제안**: v1.0은 로그만, v2.0에서 예산 관리

---

## 11. 다음 단계

1. ✅ 설계 문서 완료
2. ⏳ 기본 도구 5종 구현
3. ⏳ ToolRegistry, ToolSelector, ToolExecutor 구현
4. ⏳ PersonaOrchestrator 통합
5. ⏳ 테스트 및 폴백 동작 검증

---

**검토 요청**:
1. 도구 5종이 충분한지? (추가 필요한 도구?)
2. 규칙 기반 선택의 한계를 어떻게 보완할지?
3. v1.0 스코프가 1주 내 구현 가능한지?
