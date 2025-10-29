"""
Meta-Cognition System: 자기 능력 평가 및 위임 판단
AGI Phase 4 - "이 작업을 내가 잘 할 수 있나?"
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
import json
import os
from collections import defaultdict
# Optional Vertex AI dependency (lazy). This module must import without Vertex AI present for tests.
try:  # pragma: no cover - import guard
    from vertexai.generative_models import GenerativeModel as _VxGenerativeModel
except Exception:  # ImportError or any environment issues
    _VxGenerativeModel = None  # type: ignore

VALID_DOMAINS: List[str] = ["python", "ml", "data", "legal", "medical", "french", "general"]

FEW_SHOT_EXAMPLES: List[Dict[str, Any]] = [
    {
        "goal": "Write a command-line utility that parses JSON logs, groups them by error code, and outputs a summary table.",
        "steps": [
            "The goal mentions a command-line utility, parsing JSON logs, and producing a summary table. These are classic software engineering tasks.",
            "Among the available domains, 'python' is the most specific fit for building CLI tooling and handling JSON.",
            "Return python."
        ],
        "domain": "python",
    },
    {
        "goal": "Tune a gradient boosting model to predict customer churn using historical engagement metrics.",
        "steps": [
            "The nouns reference a gradient boosting model, customer churn, and metrics drawn from historical engagement data.",
            "Model tuning aligns most closely with the machine learning domain rather than general data work.",
            "Return ml."
        ],
        "domain": "ml",
    },
    {
        "goal": "Profile monthly revenue data to flag outliers and produce charts for executive review.",
        "steps": [
            "The task centers on revenue data, generating profiles, and delivering analytical charts.",
            "This is primarily a data analysis workflow, so 'data' is the tightest match.",
            "Return data."
        ],
        "domain": "data",
    },
    {
        "goal": "Summarize Korean data residency clauses required for a GDPR-compliant vendor contract.",
        "steps": [
            "Keywords include clauses, GDPR compliance, and vendor contracts, indicating a regulatory/legal context.",
            "The 'legal' domain addresses compliance analysis and contract considerations most directly.",
            "Return legal."
        ],
        "domain": "legal",
    },
    {
        "goal": "Explain how MRI and CT imaging differ when diagnosing soft-tissue injuries for athletes.",
        "steps": [
            "The question compares MRI and CT imaging in a clinical diagnosis scenario.",
            "This is a medical diagnostic discussion, therefore 'medical' is the best-fit domain.",
            "Return medical."
        ],
        "domain": "medical",
    },
    {
        "goal": "Translate a sales follow-up email into polite European French while keeping the technical terminology accurate.",
        "steps": [
            "The goal requests a French translation that preserves technical terminology.",
            "Foreign-language handling aligns with the language-specific 'french' domain.",
            "Return french."
        ],
        "domain": "french",
    },
]

def get_past_performance(
    persona: str,
    task_domain: Optional[str] = None,
    ledger_path: Optional[str] = None
) -> float:
    """
    특정 Persona의 과거 성공률 계산
    """
    if ledger_path is None:
        ledger_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "memory",
            "resonance_ledger.jsonl"
        )
    
    if not os.path.exists(ledger_path):
        return 0.5  # 데이터 없음 → 중립
    
    quality_scores = []
    task_domain_map: Dict[str, str] = {}
    
    try:
        with open(ledger_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        for line in lines:
            try:
                entry = json.loads(line.strip())
            except Exception:
                continue
            if entry.get("event") == "meta_cognition":
                tid = entry.get("task_id")
                dom = entry.get("domain")
                if tid and dom:
                    task_domain_map[tid] = dom

        for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    entry = json.loads(line)
                    if entry.get("event") == "eval":
                        eval_data = entry.get("eval", {})
                        quality = float(eval_data.get("quality", 0.0))
                        tid = entry.get("task_id")
                        if task_domain and tid:
                            dom = task_domain_map.get(tid)
                            if dom != task_domain:
                                continue
                        quality_scores.append(quality)
                except json.JSONDecodeError:
                    continue
    except Exception:
        return 0.5
    
    if not quality_scores:
        return 0.5
    
    avg_quality = sum(quality_scores) / len(quality_scores)
    return avg_quality

def check_tools_availability(
    task_goal: str,
    available_tools: List[str]
) -> float:
    """
    Task에 필요한 도구들이 사용 가능한지 확인
    """
    normalized_available = set(available_tools)
    web_disabled = str(os.environ.get("WEBSEARCH_DISABLE", "")).strip().lower() in ("1","true","yes","y","on")
    if web_disabled and "websearch" in normalized_available:
        normalized_available.remove("websearch")

    required_tools = set()
    goal_lower = task_goal.lower()
    
    tool_keywords = {
        "rag": ["검색", "찾기", "조회", "참고", "문서"],
        "websearch": ["웹", "인터넷", "온라인", "최신", "뉴스"],
        "fileio": ["파일", "저장", "읽기", "쓰기", "생성"],
        "codeexec": ["실행", "코드", "프로그램", "테스트", "계산"],
        "tabular": ["데이터", "테이블", "분석", "통계", "차트"]
    }
    
    for tool, keywords in tool_keywords.items():
        if any(keyword in goal_lower for keyword in keywords):
            required_tools.add(tool)
    
    if not required_tools:
        return 1.0
    
    if "websearch" in required_tools and "websearch" not in normalized_available:
        return 0.0

    available_count = sum(1 for tool in required_tools if tool in normalized_available)
    return available_count / len(required_tools)

def _get_task_domain_with_llm(task_goal: str) -> str:
    """
    Uses an LLM with Chain-of-Thought to classify the task goal.
    """
    try:
        few_shot_sections = []
        tq = '"""'
        for example in FEW_SHOT_EXAMPLES:
            reasoning = "\n".join(
                f"Step {idx + 1}: {step}"
                for idx, step in enumerate(example["steps"])
            )
            few_shot_sections.append(
                f"Example:\nGoal:\n{tq}{example['goal']}{tq}\n{reasoning}\nClassification: {example['domain']}\n"
            )

        few_shot_block = "\n".join(few_shot_sections)

        system_prompt = (
            "You are a task classification expert. Your job is to analyze a user's goal and classify it into a single, most appropriate domain from a given list. "
            "Think step-by-step."
        )
        prompt = f"""Here is the user's goal:
{tq}{task_goal}{tq}

Here is the list of valid domains:
[{', '.join(VALID_DOMAINS)}]

Step 1: Identify the key nouns, verbs, and concepts in the goal. What is the user asking to *do* and what are they asking to do it *to*?
Step 2: Based on the concepts from Step 1, determine which of the valid domains is the *most specific and relevant*. For example, if the goal involves 'Python' and 'data analysis', the 'python' domain is more specific. If it involves a foreign language, choose that language domain. If no specific domain fits well, default to 'general'.
Step 3: Respond with only the single, chosen domain name from the list.

Use the following solved examples as a guide. Mirror the structure of the reasoning and final answer:

{few_shot_block}

Classification:"""
        
        # Guard: if Vertex AI SDK or model isn't available, fall back
        if _VxGenerativeModel is None:
            raise ImportError("vertexai.generative_models not available")

        model = _VxGenerativeModel("gemini-1.5-flash-002")
        response = model.generate_content(f"{system_prompt}\n{prompt}")
        
        domain = response.text.strip().lower()
        for v_dom in VALID_DOMAINS:
            if v_dom in domain:
                return v_dom
        return "general"
    except Exception:
        goal_lower = task_goal.lower()
        if "python" in goal_lower: return "python"
        if "data" in goal_lower: return "data"
        if "law" in goal_lower or "legal" in goal_lower or "contract" in goal_lower: return "legal"
        if "medical" in goal_lower or "clinic" in goal_lower or "diagnos" in goal_lower: return "medical"
        if "french" in goal_lower or "français" in goal_lower: return "french"
        return "general"

class MetaCognitionSystem:
    """
    AGI 자기 능력 평가 시스템
    """
    
    def __init__(self, ledger_path: Optional[str] = None):
        self.ledger_path = ledger_path
    
    def evaluate_self_capability(
        self,
        task_goal: str,
        persona: str,
        available_tools: List[str]
    ) -> Dict[str, Any]:
        """
        자기 능력 평가
        """
        # 1. 도메인 추론 (LLM CoT 사용으로 변경)
        domain = _get_task_domain_with_llm(task_goal)
        
        # 2. 과거 성공률 조회
        past_performance = get_past_performance(
            persona=persona,
            task_domain=domain,
            ledger_path=self.ledger_path
        )
        
        # 3. 도구 가용성 확인
        tools_availability = check_tools_availability(
            task_goal=task_goal,
            available_tools=available_tools
        )
        
        # 4. 종합 confidence 계산
        confidence = (
            past_performance * 0.6 +
            tools_availability * 0.4
        )
        
        # 5. 위임 판단 (threshold: 0.4)
        should_delegate = confidence < 0.4
        
        # 6. 이유 설명
        reason = self._explain_decision(
            confidence, past_performance, tools_availability, should_delegate
        )
        
        return {
            "confidence": confidence,
            "past_performance": past_performance,
            "tools_availability": tools_availability,
            "domain": domain,
            "should_delegate": should_delegate,
            "reason": reason
        }
    
    def _explain_decision(
        self,
        confidence: float,
        past_performance: float,
        tools_availability: float,
        should_delegate: bool
    ) -> str:
        """의사결정 이유 설명"""
        if should_delegate:
            reasons = []
            if past_performance < 0.5:
                reasons.append(f"과거 성공률 낮음({past_performance:.2f})")
            if tools_availability < 0.5:
                reasons.append(f"필요 도구 부족({tools_availability:.2f})")
            return f"위임 권장: {', '.join(reasons)}"
        else:
            return f"수행 가능 (confidence: {confidence:.2f})"
    
    def should_delegate(self, confidence: float, threshold: float = 0.4) -> bool:
        """
        다른 Persona에게 위임해야 하는가?
        """
        return confidence < threshold

def select_best_persona_for_task(
    task_goal: str,
    available_tools: List[str],
    ledger_path: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Task에 가장 적합한 Persona 선택
    """
    system = MetaCognitionSystem(ledger_path)
    personas = ["thesis", "antithesis", "synthesis"]
    
    evaluations = {}
    for persona in personas:
        eval_result = system.evaluate_self_capability(
            task_goal=task_goal,
            persona=persona,
            available_tools=available_tools
        )
        evaluations[persona] = eval_result
    
    best_persona = max(evaluations.items(), key=lambda x: x[1]["confidence"])[0]
    
    return best_persona, evaluations

# Backward-compat: exported helper expected by tests/integrations
def infer_task_domain(task_goal: str) -> str:
    """
    Infer a coarse task domain label from a free-form goal string.
    This is a thin wrapper over the internal LLM-backed classifier with
    heuristic fallback, returning one of VALID_DOMAINS.
    """
    dom = _get_task_domain_with_llm(task_goal)
    if dom in VALID_DOMAINS:
        return dom
    return "general"
