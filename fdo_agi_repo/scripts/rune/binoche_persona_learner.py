#!/usr/bin/env python3
"""
Binoche_Observer Persona Learner (Phase 6)

비노체의 과거 작업 패턴을 학습하여 디지털 트윈 페르소나 구축:
- 의사결정 패턴 (승인/거절/수정 요청)
- 작업 선호도 (기술스택, 작업방식)
- 커뮤니케이션 스타일
- BQI별 반응 패턴

Usage:
    python binoche_persona_learner.py
    python binoche_persona_learner.py --out outputs/binoche_persona.json
"""

import sys
import os
import json
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Any, Callable
import numpy as np

# Add parent directories to path
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))

def load_ledger(ledger_path: Path) -> List[Dict[str, Any]]:
    """Load resonance ledger."""
    events = []
    if not ledger_path.exists():
        print(f"[Binoche_Observer] Ledger not found: {ledger_path}")
        return events
    
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    return events

def group_by_task(events: List[Dict]) -> Dict[str, List[Dict]]:
    """Group events by task_id."""
    tasks = defaultdict(list)
    for evt in events:
        task_id = evt.get('task_id', 'unknown')
        tasks[task_id].append(evt)
    return dict(tasks)

def extract_bqi_from_task(task_events: List[Dict]) -> Dict[str, Any] | None:
    """Extract BQI coordinate from task events."""
    for evt in task_events:
        if evt.get('event') == 'run_config' and 'bqi_coord' in evt:
            return evt['bqi_coord']
    return None

def extract_conversation_context(task_events: List[Dict]) -> Dict[str, Any]:
    """
    Extract conversation context from task events.
    Phase 6b: Conversation intelligence.
    """
    context = {
        "user_prompts": [],
        "notes": [],
        "raw_prompts": []
    }
    
    for evt in task_events:
        # Extract user prompts from BQI
        if evt.get('event') == 'run_config' and 'bqi_coord' in evt:
            bqi = evt['bqi_coord']
            if 'raw_prompt' in bqi:
                context["raw_prompts"].append(bqi['raw_prompt'])
        
        # Extract notes from eval
        if evt.get('event') == 'eval' and 'notes' in evt.get('eval', {}):
            notes = evt['eval']['notes']
            if notes and notes != "auto":
                context["notes"].append(notes)
    
    return context

def analyze_decision_patterns(tasks: Dict[str, List[Dict]]) -> Dict[str, Any]:
    """
    Analyze user decision patterns from task outcomes.
    
    Approval signals:
    - High quality (>0.8)
    - No second pass
    - High confidence
    
    Rejection signals:
    - Second pass triggered
    - Low quality (<0.6)
    - Low confidence
    
    Phase 6e: Load user goals from coordinate.jsonl for BQI generation
    """
    patterns = {
        "approve": [],
        "revise": [],
        "reject": []
    }
    
    # Phase 6e: Load user goals from coordinate.jsonl first
    task_goals = {}  # task_id -> goal text
    repo_root = Path(__file__).resolve().parents[2]
    coord_path = repo_root / "memory" / "coordinate.jsonl"
    if coord_path.exists():
        try:
            with open(coord_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        coord_event = json.loads(line)
                        if coord_event.get('event') == 'task_start':
                            task_data = coord_event.get('task', {})
                            # coordinate.jsonl uses nested 'task.task_id'
                            task_id = task_data.get('task_id')
                            goal = task_data.get('goal')
                            if task_id and goal:
                                task_goals[task_id] = goal
                    except json.JSONDecodeError:
                        continue
            print(f"[Binoche_Observer] Loaded {len(task_goals)} user goals for BQI generation")
        except Exception as e:
            print(f"[Binoche_Observer] Warning: Could not load coordinate.jsonl: {e}")
    
    # Phase 6e: Import analyse_question once at function start
    analyse_question = None
    try:
        # Try local import first (same directory)
        sys.path.insert(0, str(Path(__file__).parent))
        from bqi_adapter import analyse_question as aq_func
        analyse_question = aq_func
        print(f"[Binoche_Observer] BQI adapter loaded successfully")
    except ImportError as e:
        print(f"[Binoche_Observer] Warning: Could not import analyse_question: {e}")
        print(f"[Binoche_Observer] Will use static BQI defaults (Phase 6b fallback)")
    
    for task_id, events in tasks.items():
        bqi = extract_bqi_from_task(events)
        # Phase 6b: Learn even without BQI (infer from conversation)
        context = extract_conversation_context(events)
        if not bqi:
            # Phase 6e: Priority 1 - Use user goal from coordinate.jsonl
            prompt_text = task_goals.get(task_id, '')
            
            # Priority 2 - Fallback to raw_prompts from BQI
            if not prompt_text:
                prompt_text = context.get('raw_prompts', [''])[0] if context.get('raw_prompts') else ''
            
            # Debug: Track BQI generation (first 5 only)
            if len(patterns["approve"]) + len(patterns["revise"]) + len(patterns["reject"]) < 5 and prompt_text:
                print(f"[DEBUG] Generating BQI for task {task_id[:8]}: '{prompt_text[:60]}...'")
            
            if prompt_text and analyse_question is not None:
                bqi_coord = analyse_question(prompt_text)
                bqi = bqi_coord.to_dict()
                if len(patterns["approve"]) + len(patterns["revise"]) + len(patterns["reject"]) < 5:
                    print(f"[DEBUG]   → p{bqi['priority']}_e:{bqi['emotion']}_r:{bqi['rhythm_phase']}")
            else:
                # Fallback to Phase 6b static defaults only if no text available
                bqi = {
                    "priority": 2,
                    "emotion": {"keywords": ["neutral"]},
                    "rhythm_phase": "unknown",
                    "raw_prompt": "unknown"
                }
                if len(patterns["approve"]) + len(patterns["revise"]) + len(patterns["reject"]) < 5:
                    print(f"[DEBUG]   → Static fallback (no analyse_question)")
        
        # Phase 6b: Extract conversation context (moved up)
        
        # Extract quality signals + Phase 6j: Ensemble data
        quality = None
        confidence = None
        had_second_pass = False
        ensemble_decision = None
        ensemble_confidence = None
        ensemble_reason = None
        bqi_confidence = None
        
        for evt in events:
            if evt.get('event') == 'eval':
                quality = evt.get('quality')
                confidence = evt.get('confidence')
            elif evt.get('event') == 'second_pass':
                had_second_pass = True
            # Phase 6j: Extract ensemble data from binoche_decision
            elif evt.get('event') == 'binoche_decision':
                ensemble_decision = evt.get('ensemble_decision')
                ensemble_confidence = evt.get('ensemble_confidence')
                ensemble_reason = evt.get('ensemble_reason')
                bqi_confidence = evt.get('confidence')  # BQI confidence
        
        if quality is None:
            continue
        
        # Classify decision (relaxed thresholds to learn from existing data)
        # Phase 6b: Will add conversation context analysis
        # Phase 6j: Add ensemble data
        if quality >= 0.7 and not had_second_pass:
            # High quality without revision = approve
            patterns["approve"].append({
                "bqi": bqi,
                "quality": quality,
                "confidence": confidence,
                "task_id": task_id,
                "context": context,  # Phase 6b: conversation context
                # Phase 6j: Ensemble data
                "ensemble_decision": ensemble_decision,
                "ensemble_confidence": ensemble_confidence,
                "ensemble_reason": ensemble_reason,
                "bqi_confidence": bqi_confidence
            })
        elif had_second_pass or (0.4 <= quality < 0.7):
            # Needed revision or medium quality = revise
            patterns["revise"].append({
                "bqi": bqi,
                "quality": quality,
                "confidence": confidence,
                "task_id": task_id,
                "context": context,
                # Phase 6j: Ensemble data
                "ensemble_decision": ensemble_decision,
                "ensemble_confidence": ensemble_confidence,
                "ensemble_reason": ensemble_reason,
                "bqi_confidence": bqi_confidence
            })
        elif quality < 0.4:
            # Low quality = reject
            patterns["reject"].append({
                "bqi": bqi,
                "quality": quality,
                "confidence": confidence,
                "task_id": task_id,
                "context": context,
                # Phase 6j: Ensemble data
                "ensemble_decision": ensemble_decision,
                "ensemble_confidence": ensemble_confidence,
                "ensemble_reason": ensemble_reason,
                "bqi_confidence": bqi_confidence
            })
    
    return patterns

def analyze_conversation_patterns(patterns: Dict[str, List], coordinate_path: str = "memory/coordinate.jsonl") -> Dict[str, Any]:
    """
    Phase 6c: Extract insights from conversation context.
    
    Analyzes:
    - Keywords that correlate with decisions
    - Communication style patterns
    - Intent detection from raw prompts AND coordinate goals
    
    Data sources:
    1. Primary: coordinate.jsonl task goals (user's actual requests)
    2. Fallback: BQI raw_prompts and eval notes from decision context
    """
    keyword_stats = defaultdict(lambda: {"approve": 0, "revise": 0, "reject": 0, "total": 0})
    
    # Load user goals from coordinate log
    task_goals = {}  # task_id -> goal text
    # Coordinate path is relative to repo root (two levels up from scripts/rune)
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    coord_full_path = os.path.join(repo_root, coordinate_path)
    if os.path.exists(coord_full_path):
        try:
            with open(coord_full_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        coord_event = json.loads(line)
                        if coord_event.get("event") == "task_start":
                            task = coord_event.get("task", {})
                            task_id = task.get("task_id")
                            goal = task.get("goal", "")
                            if task_id and goal:
                                task_goals[task_id] = goal
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"[Warning] Could not load coordinate log: {e}")
    
    # Keywords to look for
    urgency_keywords = ["urgent", "asap", "immediately", "now", "quickly", "빨리", "긴급"]
    caution_keywords = ["careful", "check", "verify", "test", "안전", "확인", "검증"]
    quality_keywords = ["good", "excellent", "perfect", "clean", "좋", "완벽"]
    concern_keywords = ["risk", "danger", "problem", "issue", "위험", "문제"]
    
    all_keywords = {
        "urgency": urgency_keywords,
        "caution": caution_keywords,
        "quality": quality_keywords,
        "concern": concern_keywords
    }
    
    for decision_type, cases in patterns.items():
        for case in cases:
            # Get task goal from coordinate log
            task_id = case.get("task_id")
            goal_text = task_goals.get(task_id, "")
            
            # Fallback to context from ledger
            context = case.get("context", {})
            raw_prompts = context.get("raw_prompts", [])
            notes = context.get("notes", [])
            
            # Combine all text sources
            all_text = " ".join([goal_text] + raw_prompts + notes).lower()
            
            # Check for keywords
            for category, keywords in all_keywords.items():
                for keyword in keywords:
                    if keyword in all_text:
                        keyword_stats[category][decision_type] += 1
                        keyword_stats[category]["total"] += 1
                        break  # Count once per category per case
    
    # Calculate correlations
    keyword_correlations = {}
    for category, counts in keyword_stats.items():
        total = counts["total"]
        if total > 0:
            keyword_correlations[category] = {
                "approve_prob": counts["approve"] / total,
                "revise_prob": counts["revise"] / total,
                "reject_prob": counts["reject"] / total,
                "samples": total
            }
    
    return {
        "keyword_correlations": keyword_correlations,
        "total_analyzed": sum(len(cases) for cases in patterns.values()),
        "goals_loaded": len(task_goals)
    }

def calculate_decision_entropy(patterns: Dict[str, List]) -> Dict[str, Any]:
    """
    Phase 6d: Calculate Shannon entropy of decision distribution.
    
    H(D) = -Σ p(d) log₂ p(d)
    
    Higher entropy = more unpredictable decisions
    Lower entropy = more consistent decision pattern
    
    Returns:
        entropy: Shannon entropy in bits
        max_entropy: Maximum possible entropy (log₂(3) ≈ 1.585 for 3 decisions)
        normalized: Entropy normalized to [0, 1] range
    """
    total = sum(len(cases) for cases in patterns.values())
    if total == 0:
        return {"entropy": 0.0, "max_entropy": 0.0, "normalized": 0.0}
    
    # Calculate probabilities
    probs = {
        decision: len(cases) / total
        for decision, cases in patterns.items()
        if len(cases) > 0
    }
    
    # Shannon entropy: H(D) = -Σ p(d) log₂ p(d)
    entropy = 0.0
    for p in probs.values():
        if p > 0:
            entropy -= p * np.log2(p)
    
    # Maximum entropy for 3 decisions
    max_entropy = np.log2(3)
    normalized = entropy / max_entropy if max_entropy > 0 else 0.0
    
    return {
        "entropy": round(entropy, 4),
        "max_entropy": round(max_entropy, 4),
        "normalized": round(normalized, 4),
        "interpretation": "low" if normalized < 0.5 else "medium" if normalized < 0.8 else "high"
    }

def calculate_mutual_information(patterns: Dict[str, List], 
                                   feature_extractor: Callable) -> Dict[str, Any]:
    """
    Phase 6d: Calculate mutual information between features and decisions.
    
    I(X; D) = H(D) - H(D|X)
    
    Measures how much knowing feature X reduces uncertainty about decision D.
    
    Args:
        patterns: Decision patterns (approve/revise/reject)
        feature_extractor: Function that extracts feature from case dict
            Example: lambda case: case.get("bqi_pattern")
    
    Returns:
        mutual_info: I(X; D) in bits
        decision_entropy: H(D)
        conditional_entropy: H(D|X)
        reduction_percent: Uncertainty reduction percentage
    """
    # Calculate unconditional decision entropy H(D)
    entropy_info = calculate_decision_entropy(patterns)
    h_decision = entropy_info["entropy"]
    
    if h_decision == 0:
        return {
            "mutual_info": 0.0,
            "decision_entropy": 0.0,
            "conditional_entropy": 0.0,
            "reduction_percent": 0.0,
            "interpretation": "none"
        }
    
    # Group cases by feature value
    feature_groups = defaultdict(lambda: {"approve": [], "revise": [], "reject": []})
    total_cases = 0
    
    for decision, cases in patterns.items():
        for case in cases:
            feature_val = feature_extractor(case)
            if feature_val is not None:
                feature_groups[feature_val][decision].append(case)
                total_cases += 1
    
    if total_cases == 0:
        return {
            "mutual_info": 0.0,
            "decision_entropy": h_decision,
            "conditional_entropy": h_decision,
            "reduction_percent": 0.0,
            "interpretation": "none"
        }
    
    # Calculate conditional entropy H(D|X) = Σ p(x) H(D|X=x)
    h_conditional = 0.0
    for feature_val, decisions in feature_groups.items():
        # Probability of this feature value
        feature_total = sum(len(cases) for cases in decisions.values())
        p_feature = feature_total / total_cases
        
        # Entropy of decisions given this feature value
        h_d_given_x = calculate_decision_entropy(decisions)["entropy"]
        
        h_conditional += p_feature * h_d_given_x
    
    # Mutual information I(X; D) = H(D) - H(D|X)
    mutual_info = h_decision - h_conditional
    reduction_percent = (mutual_info / h_decision * 100) if h_decision > 0 else 0.0
    
    return {
        "mutual_info": round(mutual_info, 4),
        "decision_entropy": round(h_decision, 4),
        "conditional_entropy": round(h_conditional, 4),
        "reduction_percent": round(reduction_percent, 2),
        "interpretation": "weak" if reduction_percent < 20 else "moderate" if reduction_percent < 50 else "strong"
    }

def analyze_information_theory(patterns: Dict[str, List]) -> Dict[str, Any]:
    """
    Phase 6d: Comprehensive information-theoretic analysis.
    
    Analyzes decision predictability using:
    - Shannon entropy: Overall decision uncertainty
    - Mutual information: How much features reduce uncertainty
    """
    # Overall decision entropy
    decision_entropy = calculate_decision_entropy(patterns)
    
    # BQI pattern extractor (Phase 6f fix: build pattern key from bqi fields)
    def extract_bqi_pattern(case):
        bqi = case.get("bqi")
        if not bqi:
            return None
        
        priority = bqi.get("priority", 1)
        rhythm = bqi.get("rhythm_phase", "unknown")
        emotions = bqi.get("emotion", {"keywords": ["neutral"]})
        
        # Handle emotion dict structure (Phase 6e fix)
        if isinstance(emotions, dict):
            emotion_keywords = emotions.get("keywords", ["neutral"])
        else:
            emotion_keywords = emotions if isinstance(emotions, list) else ["neutral"]
        
        emotion_str = "keywords" if emotion_keywords != ["neutral"] else "neutral"
        
        return f"p{priority}_e:{emotion_str}_r:{rhythm}"
    
    # Mutual information between BQI pattern and decisions
    bqi_mutual_info = calculate_mutual_information(
        patterns,
        extract_bqi_pattern
    )
    
    # Mutual information between quality and decisions
    quality_mutual_info = calculate_mutual_information(
        patterns,
        lambda case: "high" if case.get("quality", 0) >= 0.8 else "medium" if case.get("quality", 0) >= 0.5 else "low"
    )
    
    # Phase 6j: Mutual information between ensemble confidence and decisions
    ensemble_mutual_info = calculate_mutual_information(
        patterns,
        lambda case: (
            "high" if (case.get("ensemble_confidence") or 0) >= 0.8
            else "medium" if (case.get("ensemble_confidence") or 0) >= 0.5
            else "low" if case.get("ensemble_confidence") is not None
            else None
        )
    )
    
    return {
        "decision_entropy": decision_entropy,
        "bqi_predictive_power": bqi_mutual_info,
        "quality_predictive_power": quality_mutual_info,
        "ensemble_predictive_power": ensemble_mutual_info,  # Phase 6j: New!
        "summary": {
            "decision_consistency": decision_entropy["interpretation"],
            "bqi_usefulness": bqi_mutual_info["interpretation"],
            "quality_usefulness": quality_mutual_info["interpretation"],
            "ensemble_usefulness": ensemble_mutual_info["interpretation"]  # Phase 6j: New!
        }
    }

def analyze_bqi_decision_correlation(patterns: Dict[str, List]) -> Dict[str, Any]:
    """
    Analyze correlation between BQI and decision patterns.
    
    Returns probability of approve/revise/reject for each BQI pattern.
    """
    bqi_stats = defaultdict(lambda: {"approve": 0, "revise": 0, "reject": 0, "total": 0})
    
    for decision_type, cases in patterns.items():
        for case in cases:
            bqi = case["bqi"]
            priority = bqi.get("priority", 2)
            emotions = bqi.get("emotion", {})
            # Phase 6e: Fix rhythm key - BQI uses 'rhythm_phase', not 'rhythm'
            rhythm = bqi.get("rhythm_phase", "unknown")
            
            # Create pattern key
            # Phase 6e: Handle emotion as dict with 'keywords' key
            emotion_keywords = emotions.get("keywords", ["neutral"]) if isinstance(emotions, dict) else emotions
            emotion_str = "keywords" if emotion_keywords and emotion_keywords != ["neutral"] else "neutral"
            pattern_key = f"p{priority}_e:{emotion_str}_r:{rhythm}"
            
            bqi_stats[pattern_key][decision_type] += 1
            bqi_stats[pattern_key]["total"] += 1
    
    # Calculate probabilities
    bqi_probabilities = {}
    for pattern, counts in bqi_stats.items():
        total = counts["total"]
        if total > 0:
            bqi_probabilities[pattern] = {
                "approve_prob": counts["approve"] / total,
                "revise_prob": counts["revise"] / total,
                "reject_prob": counts["reject"] / total,
                "sample_count": total
            }
    
    return bqi_probabilities

def analyze_tech_preferences(events: List[Dict]) -> Dict[str, Any]:
    """
    Analyze technology stack and tool preferences.
    
    Inferred from:
    - File paths in task descriptions
    - Tool usage patterns
    - Error patterns
    """
    tech_stack = Counter()
    tools_used = Counter()
    
    for evt in events:
        # Extract from tool_call events
        if evt.get('event') == 'tool_call':
            tool_name = evt.get('tool_name', '')
            tools_used[tool_name] += 1
        
        # Infer from task descriptions and file paths
        task_desc = evt.get('task', '') or evt.get('goal', '')
        if task_desc:
            task_lower = task_desc.lower()
            
            # Programming languages
            if 'python' in task_lower or '.py' in task_lower:
                tech_stack['Python'] += 1
            if 'powershell' in task_lower or '.ps1' in task_lower:
                tech_stack['PowerShell'] += 1
            if 'javascript' in task_lower or '.js' in task_lower or 'node' in task_lower:
                tech_stack['JavaScript'] += 1
            if 'typescript' in task_lower or '.ts' in task_lower:
                tech_stack['TypeScript'] += 1
            
            # Frameworks
            if 'fastapi' in task_lower or 'uvicorn' in task_lower:
                tech_stack['FastAPI'] += 1
            if 'flask' in task_lower:
                tech_stack['Flask'] += 1
            if 'pytest' in task_lower:
                tech_stack['pytest'] += 1
            
            # Tools
            if 'docker' in task_lower:
                tech_stack['Docker'] += 1
            if 'git' in task_lower:
                tech_stack['Git'] += 1
            if 'gcp' in task_lower or 'google cloud' in task_lower:
                tech_stack['GCP'] += 1
    
    return {
        "tech_stack": dict(tech_stack.most_common(10)),
        "tools_used": dict(tools_used.most_common(10))
    }

def analyze_work_style(patterns: Dict[str, List], tasks: Dict) -> Dict[str, Any]:
    """
    Analyze work style preferences.
    
    Preferences:
    - Documentation-first vs Code-first
    - TDD vs Implementation-first
    - Verbose vs Concise
    """
    style = {
        "quality_threshold": 0.0,
        "prefers_documentation": False,
        "prefers_tdd": False,
        "communication_style": "balanced"
    }
    
    # Calculate quality threshold from approved tasks
    approved_qualities = [case["quality"] for case in patterns["approve"]]
    if approved_qualities:
        style["quality_threshold"] = np.mean(approved_qualities)
    
    # TODO: Analyze documentation/TDD patterns from conversation history
    # (requires conversation_memory integration)
    
    return style

def generate_persona_rules(
    decision_patterns: Dict,
    bqi_probabilities: Dict,
    tech_preferences: Dict,
    work_style: Dict,
    conversation_insights: Dict | None = None  # Phase 6c
) -> List[Dict[str, Any]]:
    """
    Generate actionable rules for Binoche_Observer Persona.
    
    Phase 6c: Includes conversation-based rules.
    
    Rules format:
    {
        "condition": "BQI pattern or context",
        "action": "approve/revise/reject/ask_user",
        "confidence": float,
        "reasoning": "explanation"
    }
    """
    rules = []
    
    # Rule 1: Auto-approve high-confidence BQI patterns
    for pattern, probs in bqi_probabilities.items():
        if probs["approve_prob"] >= 0.8 and probs["sample_count"] >= 3:
            rules.append({
                "condition": f"BQI matches '{pattern}'",
                "action": "approve",
                "confidence": probs["approve_prob"],
                "reasoning": f"과거 {probs['sample_count']}건 중 {probs['approve_prob']*100:.0f}% 승인"
            })
    
    # Rule 2: Request revision for low-confidence patterns
    for pattern, probs in bqi_probabilities.items():
        if probs["revise_prob"] >= 0.6 and probs["sample_count"] >= 3:
            rules.append({
                "condition": f"BQI matches '{pattern}'",
                "action": "revise",
                "confidence": probs["revise_prob"],
                "reasoning": f"과거 {probs['sample_count']}건 중 {probs['revise_prob']*100:.0f}% 수정 요청"
            })
    
    # Phase 6c: Conversation-based rules
    if conversation_insights:
        keyword_corr = conversation_insights.get("keyword_correlations", {})
        
        # Rule: Urgency keywords → higher approval
        if "urgency" in keyword_corr:
            urgency_stats = keyword_corr["urgency"]
            if urgency_stats["approve_prob"] >= 0.7 and urgency_stats["samples"] >= 3:
                rules.append({
                    "condition": "conversation contains urgency keywords",
                    "action": "approve_quickly",
                    "confidence": urgency_stats["approve_prob"],
                    "reasoning": f"긴급 키워드 포함 시 {urgency_stats['approve_prob']*100:.0f}% 승인 (samples: {urgency_stats['samples']})"
                })
        
        # Rule: Concern keywords → careful review
        if "concern" in keyword_corr:
            concern_stats = keyword_corr["concern"]
            if concern_stats.get("reject_prob", 0) >= 0.5 or concern_stats.get("revise_prob", 0) >= 0.5:
                rules.append({
                    "condition": "conversation contains concern keywords",
                    "action": "careful_review",
                    "confidence": max(concern_stats.get("reject_prob", 0), concern_stats.get("revise_prob", 0)),
                    "reasoning": f"위험/문제 키워드 포함 시 신중한 검토 필요"
                })
    
    # Rule 3: Reject very low quality
    rules.append({
        "condition": "quality < 0.5",
        "action": "reject",
        "confidence": 0.9,
        "reasoning": "품질이 최소 기준 미달"
    })
    
    # Rule 4: Ask user for uncertain cases
    rules.append({
        "condition": "confidence < 0.6",
        "action": "ask_user",
        "confidence": 1.0,
        "reasoning": "과거 사례 불충분, 실제 비노체 확인 필요"
    })
    
    return rules

def main():
    parser = argparse.ArgumentParser(description="Learn Binoche_Observer persona patterns")
    parser.add_argument(
        '--ledger',
        type=Path,
        default=Path('memory/resonance_ledger.jsonl'),
        help='Path to resonance ledger'
    )
    parser.add_argument(
        '--out',
        type=Path,
        default=Path('outputs/binoche_persona.json'),
        help='Output JSON path'
    )
    args = parser.parse_args()
    
    # Resolve paths relative to repo root
    ledger_path = repo_root / args.ledger
    out_path = repo_root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("[Binoche_Observer] Loading resonance ledger...")
    events = load_ledger(ledger_path)
    print(f"[Binoche_Observer] Loaded {len(events)} events")
    
    if len(events) == 0:
        print("[Binoche_Observer] No events found. Exiting.")
        return
    
    print("[Binoche_Observer] Grouping events by task...")
    tasks = group_by_task(events)
    print(f"[Binoche_Observer] Analyzed {len(tasks)} tasks")
    
    print("[Binoche_Observer] Analyzing decision patterns...")
    decision_patterns = analyze_decision_patterns(tasks)
    print(f"[Binoche_Observer] Decision Patterns:")
    print(f"  - Approve: {len(decision_patterns['approve'])} cases")
    print(f"  - Revise:  {len(decision_patterns['revise'])} cases")
    print(f"  - Reject:  {len(decision_patterns['reject'])} cases")
    
    total_decisions = sum(len(v) for v in decision_patterns.values())
    if total_decisions > 0:
        print(f"[Binoche_Observer] Distribution:")
        print(f"  - Approve: {len(decision_patterns['approve'])/total_decisions*100:.1f}%")
        print(f"  - Revise:  {len(decision_patterns['revise'])/total_decisions*100:.1f}%")
        print(f"  - Reject:  {len(decision_patterns['reject'])/total_decisions*100:.1f}%")
    
    print("[Binoche_Observer] Analyzing BQI-decision correlation...")
    bqi_probabilities = analyze_bqi_decision_correlation(decision_patterns)
    print(f"[Binoche_Observer] Found {len(bqi_probabilities)} BQI patterns")
    
    # Phase 6c: Conversation pattern analysis
    print("[Binoche_Observer] Analyzing conversation patterns...")
    conversation_insights = analyze_conversation_patterns(decision_patterns)
    keyword_corr = conversation_insights.get("keyword_correlations", {})
    goals_loaded = conversation_insights.get("goals_loaded", 0)
    print(f"[Binoche_Observer] Loaded {goals_loaded} user goals from coordinate.jsonl")
    print(f"[Binoche_Observer] Conversation Insights:")
    for category, stats in keyword_corr.items():
        print(f"  - {category}: approve={stats['approve_prob']:.2f}, samples={stats['samples']}")
    
    # Phase 6d: Information theory analysis
    print("[Binoche_Observer] Analyzing decision predictability (Information Theory)...")
    info_theory = analyze_information_theory(decision_patterns)
    
    decision_entropy = info_theory["decision_entropy"]
    print(f"[Binoche_Observer] Decision Entropy: {decision_entropy['entropy']:.4f} bits")
    print(f"  - Normalized: {decision_entropy['normalized']:.2%} of maximum")
    print(f"  - Consistency: {decision_entropy['interpretation']}")
    
    bqi_power = info_theory["bqi_predictive_power"]
    print(f"[Binoche_Observer] BQI Predictive Power:")
    print(f"  - Mutual Info: {bqi_power['mutual_info']:.4f} bits")
    print(f"  - Reduces uncertainty by {bqi_power['reduction_percent']:.1f}%")
    print(f"  - Usefulness: {bqi_power['interpretation']}")
    
    quality_power = info_theory["quality_predictive_power"]
    print(f"[Binoche_Observer] Quality Score Predictive Power:")
    print(f"  - Mutual Info: {quality_power['mutual_info']:.4f} bits")
    print(f"  - Reduces uncertainty by {quality_power['reduction_percent']:.1f}%")
    print(f"  - Usefulness: {quality_power['interpretation']}")
    
    # Phase 6j: Ensemble predictive power
    ensemble_power = info_theory["ensemble_predictive_power"]
    print(f"[Binoche_Observer] Ensemble (BQI+Quality) Predictive Power:")
    print(f"  - Mutual Info: {ensemble_power['mutual_info']:.4f} bits")
    print(f"  - Reduces uncertainty by {ensemble_power['reduction_percent']:.1f}%")
    print(f"  - Usefulness: {ensemble_power['interpretation']}")
    print(f"  - Improvement over BQI: +{ensemble_power['reduction_percent'] - bqi_power['reduction_percent']:.1f}%")
    
    # Show top patterns
    sorted_patterns = sorted(
        bqi_probabilities.items(),
        key=lambda x: x[1]["sample_count"],
        reverse=True
    )[:5]
    
    if sorted_patterns:
        print(f"[Binoche_Observer] Top BQI Patterns:")
        for pattern, stats in sorted_patterns:
            print(f"  {pattern}: approve={stats['approve_prob']:.2f}, samples={stats['sample_count']}")
    
    print("[Binoche_Observer] Analyzing tech preferences...")
    tech_preferences = analyze_tech_preferences(events)
    print(f"[Binoche_Observer] Tech Stack:")
    for tech, count in list(tech_preferences["tech_stack"].items())[:5]:
        print(f"  - {tech}: {count} mentions")
    
    print("[Binoche_Observer] Analyzing work style...")
    work_style = analyze_work_style(decision_patterns, tasks)
    print(f"[Binoche_Observer] Work Style:")
    print(f"  - Quality Threshold: {work_style['quality_threshold']:.2f}")
    
    print("[Binoche_Observer] Generating persona rules...")
    persona_rules = generate_persona_rules(
        decision_patterns,
        bqi_probabilities,
        tech_preferences,
        work_style,
        conversation_insights  # Phase 6c
    )
    print(f"[Binoche_Observer] Generated {len(persona_rules)} rules")
    
    # Build final persona model
    persona = {
        "version": "1.2.0",  # Phase 6d: Information theory
        "created_at": datetime.now().isoformat(),
        "stats": {
            "total_tasks": len(tasks),
            "total_decisions": total_decisions,
            "approve_rate": len(decision_patterns["approve"]) / total_decisions if total_decisions > 0 else 0,
            "revise_rate": len(decision_patterns["revise"]) / total_decisions if total_decisions > 0 else 0,
            "reject_rate": len(decision_patterns["reject"]) / total_decisions if total_decisions > 0 else 0
        },
        "decision_patterns": {
            k: [{"bqi": c["bqi"], "quality": c["quality"], "confidence": c.get("confidence")} 
                for c in v[:10]]  # Sample first 10
            for k, v in decision_patterns.items()
        },
        "bqi_probabilities": bqi_probabilities,
        "conversation_insights": conversation_insights,  # Phase 6c
        "information_theory": info_theory,  # Phase 6d: New field
        "tech_preferences": tech_preferences,
        "work_style": work_style,
        "rules": persona_rules
    }
    
    # Save
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(persona, f, indent=2, ensure_ascii=False)
    
    print(f"[Binoche_Observer] Persona model saved to: {out_path}")
    print(f"[Binoche_Observer] Model summary:")
    print(f"  - Tasks analyzed: {len(tasks)}")
    print(f"  - BQI patterns: {len(bqi_probabilities)}")
    print(f"  - Decision rules: {len(persona_rules)}")
    print(f"  - Top tech: {list(tech_preferences['tech_stack'].keys())[:3]}")

if __name__ == "__main__":
    main()
