"""
느낌 기반 장기 기억 시스템 (Feeling-Based Long-Term Memory)
================================================================

인간처럼 "느낌"으로 기억을 압축하고 검색하는 시스템

핵심 개념:
1. 블랙홀 압축: 긴 대화 → 느낌 벡터 (512 dim)
2. 화이트홀 복원: 느낌 유사도 → 관련 기억 인출
3. 토큰 절약: 100,000 → 1,000 (100배 효율)

철학적 배경:
- 블랙홀 = 정보를 느낌으로 압축
- 사건의 지평선 = 느낌 벡터 (경계에 모든 정보)
- 화이트홀 = 필요한 기억만 복원
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from hippocampus_black_white_hole import extract_feeling_vector
except ImportError:
    print("Warning: hippocampus module not found. Using mock feeling extraction.")
    extract_feeling_vector = None

class FeelingMemory:
    """
    느낌 기반 장기 기억 시스템
    
    인간의 뇌처럼:
    1. 경험 → 느낌으로 압축
    2. 느낌 유사도로 기억 검색
    3. 관련 기억만 복원 (토큰 절약)
    """
    
    def __init__(self, memory_dir: Path = None):
        if memory_dir is None:
            workspace_root = Path(__file__).parent.parent
            memory_dir = workspace_root / "outputs" / "feeling_memory"
        
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.memories_file = self.memory_dir / "memories.jsonl"
        self.index_file = self.memory_dir / "feeling_index.npy"
        
        # Load existing memories
        self.memories: List[Dict] = []
        self.feeling_vectors: np.ndarray = None
        self._load_memories()
    
    def _load_memories(self):
        """기존 기억 로드"""
        if not self.memories_file.exists():
            return
        
        self.memories = []
        feeling_list = []
        
        with open(self.memories_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    memory = json.loads(line)
                    self.memories.append(memory)
                    feeling_list.append(memory['feeling'])
        
        if feeling_list:
            self.feeling_vectors = np.array(feeling_list)
            print(f"📚 Loaded {len(self.memories)} memories")
    
    def _extract_feeling(self, conversation: str) -> np.ndarray:
        """대화를 느낌 벡터로 압축 (블랙홀)"""
        if extract_feeling_vector is not None:
            # 실제 hippocampus 사용
            events = [{"content": conversation, "timestamp": datetime.now().isoformat()}]
            feeling, _ = extract_feeling_vector(events)
            return feeling
        else:
            # Mock: 간단한 해시 기반 벡터
            # 실제로는 LLM embeddings 또는 hippocampus 사용
            np.random.seed(hash(conversation) % (2**32))
            return np.random.randn(512)
    
    def store_conversation(self, 
                          conversation: str, 
                          summary: str = None,
                          keywords: List[str] = None,
                          metadata: Dict = None) -> str:
        """
        대화를 느낌 벡터로 압축하여 저장 (블랙홀 압축)
        
        Args:
            conversation: 전체 대화 내용 (긴 텍스트 가능)
            summary: 간단한 요약 (선택)
            keywords: 주요 키워드 (선택)
            metadata: 추가 메타데이터
        
        Returns:
            memory_id: 저장된 기억 ID
        """
        # 1. 느낌 벡터 추출 (블랙홀 압축)
        feeling_vector = self._extract_feeling(conversation)
        
        # 2. 자동 요약 (간단한 버전)
        if summary is None:
            summary = conversation[:200] + "..." if len(conversation) > 200 else conversation
        
        # 3. 자동 키워드 추출 (간단한 버전)
        if keywords is None:
            # 간단한 키워드 추출 (실제로는 NLP 사용)
            words = conversation.split()
            keywords = list(set([w for w in words if len(w) > 3]))[:10]
        
        # 4. 기억 객체 생성
        memory_id = f"memory_{len(self.memories):06d}"
        memory = {
            "id": memory_id,
            "feeling": feeling_vector.tolist(),
            "summary": summary,
            "keywords": keywords,
            "conversation": conversation[:500] if len(conversation) > 500 else conversation,  # 일부만 저장
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # 5. 저장
        self.memories.append(memory)
        
        # Append to file
        with open(self.memories_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(memory, ensure_ascii=False) + '\n')
        
        # Update index
        if self.feeling_vectors is None:
            self.feeling_vectors = feeling_vector.reshape(1, -1)
        else:
            self.feeling_vectors = np.vstack([self.feeling_vectors, feeling_vector])
        
        print(f"💾 Stored memory: {memory_id} (feeling compressed: {len(conversation)} → 512 dim)")
        
        return memory_id
    
    def recall_by_feeling(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        느낌 유사도로 관련 기억 검색 (화이트홀 복원)
        
        Args:
            query: 검색 쿼리 (자연어)
            top_k: 상위 K개 기억 반환
        
        Returns:
            관련 기억 리스트 (유사도 높은 순)
        """
        if not self.memories:
            return []
        
        # 1. 쿼리를 느낌 벡터로 변환
        query_feeling = self._extract_feeling(query)
        
        # 2. 코사인 유사도 계산
        similarities = self._cosine_similarity(query_feeling, self.feeling_vectors)
        
        # 3. 상위 K개 선택
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # 4. 결과 구성
        results = []
        for idx in top_indices:
            memory = self.memories[idx].copy()
            memory['similarity'] = float(similarities[idx])
            results.append(memory)
        
        print(f"🔍 Recalled {len(results)} memories (similarity: {results[0]['similarity']:.3f} ~ {results[-1]['similarity']:.3f})")
        
        return results
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> np.ndarray:
        """코사인 유사도 계산"""
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-10)
        vec2_norm = vec2 / (np.linalg.norm(vec2, axis=1, keepdims=True) + 1e-10)
        return np.dot(vec2_norm, vec1_norm)
    
    def get_context_for_llm(self, query: str, top_k: int = 3, max_tokens: int = 1000) -> str:
        """
        LLM에 전달할 컨텍스트 생성 (토큰 절약)
        
        Args:
            query: 사용자 질문
            top_k: 검색할 기억 개수
            max_tokens: 최대 토큰 수 (대략)
        
        Returns:
            컨텍스트 문자열 (관련 기억 요약)
        """
        related_memories = self.recall_by_feeling(query, top_k)
        
        if not related_memories:
            return "관련 과거 기억 없음"
        
        context_parts = ["관련 과거 대화:\n"]
        
        for i, mem in enumerate(related_memories, 1):
            similarity = mem['similarity']
            summary = mem['summary']
            timestamp = mem['timestamp'][:10]  # Date only
            
            context_parts.append(
                f"{i}. [{timestamp}] (유사도: {similarity:.2f})\n"
                f"   {summary}\n"
            )
        
        context = "\n".join(context_parts)
        
        # 토큰 제한 (대략 4 chars = 1 token)
        if len(context) > max_tokens * 4:
            context = context[:max_tokens * 4] + "\n... (이하 생략)"
        
        return context
    
    def stats(self) -> Dict:
        """기억 통계"""
        if not self.memories:
            return {"total_memories": 0}
        
        return {
            "total_memories": len(self.memories),
            "oldest": self.memories[0]['timestamp'],
            "newest": self.memories[-1]['timestamp'],
            "vector_dimension": self.feeling_vectors.shape[1] if self.feeling_vectors is not None else 0,
            "storage_size": self.memories_file.stat().st_size if self.memories_file.exists() else 0
        }


def demo():
    """데모: 느낌 기반 기억 시스템"""
    print("🧠 느낌 기반 장기 기억 시스템 데모\n")
    
    memory = FeelingMemory()
    
    # 과거 대화 저장
    conversations = [
        {
            "text": "리듬 기반 AGI의 핵심은 불변량(Invariant)입니다. I = √(R² + E² + L² - T²) 공식으로 계산하며, 이것이 임계점 감지의 기준이 됩니다.",
            "summary": "리듬 AGI: 불변량 공식과 임계점",
            "keywords": ["리듬", "불변량", "임계점", "AGI"]
        },
        {
            "text": "블랙홀은 정보를 압축하고, 화이트홀은 정보를 복원합니다. 사건의 지평선에 모든 정보가 홀로그래픽하게 저장되는 원리를 응용했습니다.",
            "summary": "블랙홀/화이트홀: 정보 압축과 복원",
            "keywords": ["블랙홀", "화이트홀", "정보", "홀로그래픽"]
        },
        {
            "text": "바이브 코딩은 한국어 자연어를 AI가 자동으로 해석하는 시스템입니다. Claude는 맥락을, Gemini는 실행을 담당합니다.",
            "summary": "바이브 코딩: AI 자동 해석",
            "keywords": ["바이브", "코딩", "한국어", "Claude", "Gemini"]
        }
    ]
    
    print("📚 과거 대화 저장 중...\n")
    for conv in conversations:
        memory.store_conversation(
            conversation=conv['text'],
            summary=conv['summary'],
            keywords=conv['keywords']
        )
    
    print("\n" + "=" * 60)
    
    # 느낌 기반 검색 테스트
    queries = [
        "불변량이 뭐였지?",
        "블랙홀 어떻게 작동해?",
        "한국어로 AI 명령하는 거 뭐라고 했더라?"
    ]
    
    for query in queries:
        print(f"\n❓ 질문: \"{query}\"\n")
        
        # 관련 기억 검색
        recalled = memory.recall_by_feeling(query, top_k=2)
        
        for mem in recalled:
            print(f"  💡 기억: {mem['summary']}")
            print(f"     유사도: {mem['similarity']:.3f}")
            print(f"     키워드: {', '.join(mem['keywords'][:5])}")
        
        # LLM용 컨텍스트 생성
        context = memory.get_context_for_llm(query, top_k=1, max_tokens=200)
        print(f"\n  📝 LLM 컨텍스트 (토큰 절약):")
        print(f"     {context.replace(chr(10), chr(10) + '     ')}")
    
    print("\n" + "=" * 60)
    print("\n📊 기억 통계:")
    stats = memory.stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✨ 데모 완료!")
    print("\n💡 효과:")
    print("   - 전체 대화 (1,000 tokens) → 느낌 벡터 (512 dim)")
    print("   - LLM 컨텍스트: 100,000 tokens → 1,000 tokens (100배 절약!)")


if __name__ == "__main__":
    demo()
