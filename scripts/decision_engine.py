#!/usr/bin/env python3
"""
Decision Engine - Phase 5.1
Autonomous action decision with confidence scoring

Purpose: Determine what action to take and how confident we are
Goal: Enable autonomous execution while maintaining safety
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from context_bridge import ContextBridge
from context_embedding import ContextEmbedding


@dataclass
class Decision:
    """A decision with confidence score"""
    action: str  # Action ID from whitelist
    confidence: float  # 0.0 - 1.0
    reason: str  # Why this decision
    params: Dict  # Parameters for the action
    similar_contexts: List[str] = None  # Similar past contexts
    
    def __post_init__(self):
        if self.similar_contexts is None:
            self.similar_contexts = []


class DecisionEngine:
    """
    Determines what action to take based on input and context
    
    Core Logic:
    1. High similarity to past → High confidence
    2. Alpha crisis → Emergency action
    3. Unfamiliar → Low confidence (request approval)
    """
    
    def __init__(self, whitelist_path: str = None):
        self.whitelist_path = whitelist_path or Path.home() / "agi" / "config" / "execution_whitelist.json"
        self.whitelist = self._load_whitelist()
        
        # Core components
        self.context_bridge = ContextBridge()
        self.embedder = ContextEmbedding()
        
        # Load or create action history
        self.action_history_path = Path.home() / "agi" / "outputs" / "action_history.jsonl"
        self.action_counts = self._load_action_counts()
    
    def _load_whitelist(self) -> Dict:
        """Load execution whitelist"""
        if not self.whitelist_path.exists():
            print(f"⚠️ Whitelist not found: {self.whitelist_path}")
            return {"allowed_actions": [], "forbidden_actions": []}
        
        with open(self.whitelist_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_action_counts(self) -> Dict:
        """Load action history for rate limiting"""
        counts = {}
        if not self.action_history_path.exists():
            return counts
        
        now = datetime.now(timezone.utc)
        
        with open(self.action_history_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    # Only count last hour
                    timestamp = datetime.fromisoformat(entry["timestamp"])
                    if (now - timestamp).total_seconds() < 3600:
                        action_id = entry["action"]
                        counts[action_id] = counts.get(action_id, 0) + 1
        
        return counts
    
    def decide(self, input_text: str, layer: str = "sian", 
               alpha_state: Dict = None) -> Decision:
        """
        Main decision function
        
        Args:
            input_text: User input (e.g., Slack message)
            layer: Which layer is requesting (sian, lumen, etc.)
            alpha_state: Current Alpha state (optional)
            
        Returns:
            Decision with action and confidence
        """
        print(f"\n🤔 Decision Engine: Analyzing input...")
        print(f"   Input: {input_text[:80]}...")
        print(f"   Layer: {layer}")
        
        # 1. Search for similar past contexts
        similar = self._find_similar_contexts(input_text, layer)
        
        # 2. Check Alpha state for emergency
        if alpha_state and alpha_state.get("state") == "INTERVENTION":
            return self._emergency_decision(alpha_state)
        
        # 3. Pattern matching for common queries
        pattern_decision = self._match_patterns(input_text)
        if pattern_decision:
            return pattern_decision
        
        # 4. Context-based decision
        if similar:
            return self._context_based_decision(input_text, similar)
        
        # 5. Default: Low confidence
        return Decision(
            action="request_approval",
            confidence=0.5,
            reason="새로운 유형의 요청 - 승인 필요",
            params={"input": input_text, "layer": layer}
        )
    
    def _find_similar_contexts(self, text: str, layer: str) -> List:
        """Find similar past contexts"""
        print(f"   🔍 Searching for similar contexts...")
        
        # Try semantic search first
        try:
            query_emb = self.embedder.embed(text)
            # Search in same layer
            layer_contexts = self.context_bridge.search_by_layer(layer, limit=50)
            
            if layer_contexts:
                # Compute similarities
                results = []
                for ctx in layer_contexts:
                    ctx_emb = self.embedder.embed(ctx.content)
                    similarity = self.embedder.cosine_similarity(query_emb, ctx_emb)
                    results.append((ctx, similarity))
                
                # Sort by similarity
                results.sort(key=lambda x: x[1], reverse=True)
                
                print(f"   ✓ Found {len(results)} contexts")
                if results:
                    print(f"   Top similarity: {results[0][1]:.3f}")
                
                return results[:5]  # Top 5
        except Exception as e:
            print(f"   ⚠️ Embedding search failed: {e}")
        
        # Fallback: Tag-based search
        tags = self._extract_tags(text)
        if tags:
            return [(ctx, 0.5) for ctx in self.context_bridge.search_by_tags(tags, limit=5)]
        
        return []
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract likely tags from text"""
        keywords = ["alpha", "background", "lumen", "rhythm", "status", "위기", "개입", "상태"]
        text_lower = text.lower()
        return [kw for kw in keywords if kw in text_lower]
    
    def _match_patterns(self, text: str) -> Optional[Decision]:
        """Match common patterns"""
        text_lower = text.lower()
        
        # Pattern: Status check
        if any(word in text_lower for word in ["상태", "status", "어때", "확인"]):
            if any(word in text_lower for word in ["alpha", "알파"]):
                return Decision(
                    action="run_diagnostic",
                    confidence=0.95,
                    reason="Alpha 상태 확인 - 일반적인 패턴",
                    params={"component": "alpha"}
                )
        
        # Pattern: Context save
        if any(word in text_lower for word in ["기억", "저장", "remember"]):
            return Decision(
                action="save_context",
                confidence=0.9,
                reason="맥락 저장 요청 - 안전한 작업",
                params={"content": text}
            )
        
        return None
    
    def _context_based_decision(self, text: str, similar: List[Tuple]) -> Decision:
        """Make decision based on similar contexts"""
        top_ctx, top_sim = similar[0]
        
        print(f"   📊 Top match: {top_sim:.3f} - {top_ctx.content[:60]}...")
        
        # Very high similarity → High confidence
        if top_sim > 0.95:
            return Decision(
                action="respond_to_slack",
                confidence=0.95,
                reason=f"거의 동일한 과거 사례 (유사도 {top_sim:.2f})",
                params={"text": text},
                similar_contexts=[top_ctx.id]
            )
        
        # High similarity → Medium-high confidence
        elif top_sim > 0.85:
            return Decision(
                action="respond_to_slack",
                confidence=0.85,
                reason=f"유사한 과거 사례 (유사도 {top_sim:.2f})",
                params={"text": text},
                similar_contexts=[ctx.id for ctx, _ in similar[:3]]
            )
        
        # Medium similarity → Request approval
        else:
            return Decision(
                action="request_approval",
                confidence=0.6,
                reason=f"부분적으로 유사 (유사도 {top_sim:.2f}) - 승인 필요",
                params={"text": text},
                similar_contexts=[ctx.id for ctx, _ in similar[:3]]
            )
    
    def _emergency_decision(self, alpha_state: Dict) -> Decision:
        """Emergency decision during Alpha intervention"""
        return Decision(
            action="execute_emergency_protocol",
            confidence=0.9,
            reason="Alpha INTERVENTION 상태 - 긴급 대응",
            params={
                "protocol_type": alpha_state.get("anomaly", "UNKNOWN"),
                "drift_score": alpha_state.get("drift_score", 0)
            }
        )
    
    def is_allowed(self, decision: Decision) -> Tuple[bool, str]:
        """
        Check if decision is allowed by whitelist
        
        Returns:
            (allowed: bool, reason: str)
        """
        # 1. Check if action exists in whitelist
        allowed_actions = {a["id"]: a for a in self.whitelist.get("allowed_actions", [])}
        
        if decision.action not in allowed_actions:
            return False, f"Action '{decision.action}' not in whitelist"
        
        action_def = allowed_actions[decision.action]
        
        # 2. Check confidence threshold
        required_conf = action_def.get("requires_confidence", 0.9)
        if decision.confidence < required_conf:
            return False, f"Confidence {decision.confidence:.2f} < required {required_conf}"
        
        # 3. Check rate limit
        max_freq = action_def.get("max_frequency", "unlimited")
        if max_freq != "unlimited":
            count, period = max_freq.split("/")
            current_count = self.action_counts.get(decision.action, 0)
            if current_count >= int(count):
                return False, f"Rate limit exceeded: {current_count}/{count} per {period}"
        
        return True, "Allowed"
    
    def log_action(self, decision: Decision, result: str):
        """Log executed action"""
        self.action_history_path.parent.mkdir(parents=True, exist_ok=True)
        
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": decision.action,
            "confidence": decision.confidence,
            "reason": decision.reason,
            "result": result
        }
        
        with open(self.action_history_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def main():
    """Test the Decision Engine"""
    engine = DecisionEngine()
    
    print("=" * 60)
    print("🧠 Decision Engine Test")
    print("=" * 60)
    
    # Test cases
    test_inputs = [
        ("Alpha 상태가 어때?", "sian"),
        ("지금 시스템 상태 확인해줘", "lumen"),
        ("이 대화 기억해줘", "sian"),
        ("완전히 새로운 요청입니다", "sian")
    ]
    
    for text, layer in test_inputs:
        print(f"\n{'='*60}")
        print(f"Input: {text}")
        print(f"Layer: {layer}")
        
        decision = engine.decide(text, layer)
        
        print(f"\n✨ Decision:")
        print(f"   Action: {decision.action}")
        print(f"   Confidence: {decision.confidence:.2f}")
        print(f"   Reason: {decision.reason}")
        
        allowed, reason = engine.is_allowed(decision)
        print(f"\n🔒 Whitelist Check: {allowed}")
        print(f"   Reason: {reason}")


if __name__ == "__main__":
    main()
