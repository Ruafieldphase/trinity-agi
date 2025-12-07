"""
통합 메모리 시스템 (Unified Memory System)
================================================

단기 기억(Rolling Window)과 장기 기억(Feeling-Based)을 결합하여
인간의 기억 메커니즘을 모방한 하이브리드 시스템.

구조:
1. Short-Term (Working Memory):
   - 최근 N개 대화 유지 (GeminiMemoryManager)
   - 즉각적인 맥락 파악
   
2. Long-Term (Feeling Memory):
   - 오래된 대화를 느낌 벡터로 압축 저장 (FeelingMemory)
   - 필요 시 느낌 유사도로 검색 (White Hole Retrieval)
   
3. Consolidation (기억 통합):
   - Short-Term이 가득 차면 가장 오래된 기억을 Long-Term으로 이관
   - "잠(Sleep)" 또는 "휴식" 시기에 배치 처리 가능
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime

# Import existing memory managers
sys.path.append(str(Path(__file__).parent))

try:
    from gemini_memory_manager import GeminiMemoryManager
except ImportError:
    print("⚠️  GeminiMemoryManager not found. Using mock.")
    GeminiMemoryManager = None

try:
    from feeling_based_memory import FeelingMemory
except ImportError:
    print("⚠️  FeelingMemory not found. Using mock.")
    FeelingMemory = None

class UnifiedMemorySystem:
    def __init__(self, workspace_root: Path = None):
        if workspace_root is None:
            workspace_root = Path(__file__).parent.parent
            
        self.workspace_root = workspace_root
        
        # 1. Initialize Short-Term Memory (Rolling Window)
        if GeminiMemoryManager:
            self.short_term = GeminiMemoryManager(workspace_root, window_size=20)
        else:
            self.short_term = None
            
        # 2. Initialize Long-Term Memory (Feeling Based)
        if FeelingMemory:
            self.long_term = FeelingMemory(workspace_root / "outputs" / "feeling_memory")
        else:
            self.long_term = None
            
    def add_memory(self, role: str, content: str, metadata: Dict = None):
        """
        새로운 기억 추가 (단기 기억에 저장)
        """
        if not self.short_term:
            print("❌ Short-term memory not available")
            return

        # Add to rolling window (simulated via update_gemini_md logic or direct list)
        # GeminiMemoryManager는 주로 GEMINI.md 파일을 관리하므로, 
        # 여기서는 개념적으로 단기 기억에 추가하고 필요시 장기 기억으로 넘기는 로직을 구현
        
        # 실제 구현에서는 GeminiMemoryManager가 파일 기반이므로,
        # 직접 리스트를 관리하거나 Manager의 메서드를 확장해야 함.
        # 여기서는 데모를 위해 간단한 리스트 관리 로직을 추가합니다.
        
        timestamp = datetime.now().isoformat()
        memory_item = {
            "role": role,
            "content": content,
            "timestamp": timestamp,
            "metadata": metadata or {}
        }
        
        # 단기 기억 파일(가상)에 추가
        self._add_to_short_term_buffer(memory_item)
        
        # Check for overflow and consolidate
        self._consolidate_memory()
        
    def recall(self, query: str) -> Dict:
        """
        기억 인출 (단기 + 장기 통합)
        """
        result = {
            "short_term": [],
            "long_term": [],
            "context_str": ""
        }
        
        # 1. Short-Term Retrieval (Recent context)
        recent_memories = self._get_recent_memories(limit=10)
        result["short_term"] = recent_memories
        
        # 2. Long-Term Retrieval (Feeling based)
        if self.long_term:
            related_memories = self.long_term.recall_by_feeling(query, top_k=3)
            result["long_term"] = related_memories
        
        # 3. Construct Context String
        context_parts = []
        
        # Long-term context (Background info)
        if result["long_term"]:
            context_parts.append("=== 🧠 관련 장기 기억 (Feeling Based) ===")
            for mem in result["long_term"]:
                context_parts.append(f"- [{mem['timestamp'][:10]}] {mem['summary']} (유사도: {mem.get('similarity', 0):.2f})")
            context_parts.append("")
            
        # Short-term context (Immediate flow)
        if result["short_term"]:
            context_parts.append("=== ⚡ 최근 대화 (Short Term) ===")
            for mem in result["short_term"]:
                context_parts.append(f"{mem['role']}: {mem['content']}")
                
        result["context_str"] = "\n".join(context_parts)
        
        return result

    def _add_to_short_term_buffer(self, item: Dict):
        """단기 기억 버퍼에 추가 (파일 기반)"""
        buffer_path = self.workspace_root / "outputs" / "memory" / "short_term_buffer.jsonl"
        buffer_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(buffer_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
    def _get_recent_memories(self, limit: int = 10) -> List[Dict]:
        """최근 기억 로드"""
        buffer_path = self.workspace_root / "outputs" / "memory" / "short_term_buffer.jsonl"
        if not buffer_path.exists():
            return []
            
        memories = []
        with open(buffer_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    memories.append(json.loads(line))
        
        return memories[-limit:]
        
    def _consolidate_memory(self, threshold: int = 20):
        """
        기억 통합 (Consolidation)
        단기 기억이 threshold를 넘으면 오래된 것을 장기 기억으로 이동
        """
        buffer_path = self.workspace_root / "outputs" / "memory" / "short_term_buffer.jsonl"
        if not buffer_path.exists():
            return

        # Load all
        memories = []
        with open(buffer_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    memories.append(json.loads(line))
        
        if len(memories) <= threshold:
            return
            
        # Split into old and new
        num_to_move = len(memories) - threshold
        to_move = memories[:num_to_move]
        to_keep = memories[num_to_move:]
        
        print(f"🔄 Consolidating {num_to_move} memories to Long-Term Storage...")
        
        # Move to Long-Term
        if self.long_term:
            for mem in to_move:
                self.long_term.store_conversation(
                    conversation=mem['content'],
                    metadata={"role": mem['role'], "original_timestamp": mem['timestamp']}
                )
        
        # Update Short-Term file
        with open(buffer_path, 'w', encoding='utf-8') as f:
            for mem in to_keep:
                f.write(json.dumps(mem, ensure_ascii=False) + '\n')
                
        print("✅ Memory consolidation complete.")

def demo():
    print("🧠 Unified Memory System Demo")
    print("===========================\n")
    
    system = UnifiedMemorySystem()
    
    # 1. Simulate conversation (Short-term filling up)
    print("1️⃣  대화 시뮬레이션 중 (단기 기억 채우기)...")
    
    conversations = [
        ("user", "안녕, 리듬 기반 AGI에 대해 알려줘."),
        ("ai", "리듬 기반 AGI는 불변량 I를 중심으로 작동합니다."),
        ("user", "불변량 공식이 뭐였지?"),
        ("ai", "I = √(R² + E² + L² - T²) 입니다."),
        ("user", "임계점은?"),
        ("ai", "시스템이 상전이하는 지점입니다."),
        # ... 더 많은 대화 추가 ...
    ]
    
    # Add dummy conversations to trigger consolidation
    for i in range(25):
        role = "user" if i % 2 == 0 else "ai"
        content = f"대화 메시지 #{i}: 리듬과 공명에 대한 논의..."
        system.add_memory(role, content)
        
    print("\n2️⃣  기억 인출 테스트 (Recall)...")
    query = "불변량 공식"
    result = system.recall(query)
    
    print(f"\n❓ Query: '{query}'")
    print("\n📝 Generated Context:")
    print("-" * 40)
    print(result["context_str"])
    print("-" * 40)
    
    print("\n✨ 데모 완료!")

if __name__ == "__main__":
    demo()
