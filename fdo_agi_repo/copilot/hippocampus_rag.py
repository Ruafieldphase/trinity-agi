"""
🧠 Hippocampus RAG: 로컬 LLM 기반 장기 기억 시스템

Self-Referential AGI의 핵심 - 재부팅 후에도 유지되는 진짜 기억
- Ollama (nomic-embed-text) 로컬 임베딩
- 벡터 스토어로 시맨틱 검색
- SQLite + 파일 시스템 영구 저장
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone
import json
import logging
import requests
import sys

# 상대 임포트를 절대 임포트로 변경
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "rag"))

from hippocampus import CopilotHippocampus
from vector_store import SimpleVectorStore

logger = logging.getLogger(__name__)


class HippocampusRAG:
    """
    로컬 LLM 기반 Hippocampus 통합
    - 자동으로 Everything 검색 결과를 임베딩
    - 재부팅 후에도 벡터 스토어 유지
    - 빠른 시맨틱 회상
    """
    
    def __init__(self, workspace: Path, ollama_url: str = "http://localhost:11434"):
        self.workspace = workspace
        self.hippocampus = CopilotHippocampus(workspace)
        self.ollama_url = ollama_url
        
        # 벡터 스토어 초기화 (768차원 = nomic-embed-text)
        self.vector_store_path = workspace / "fdo_agi_repo" / "memory" / "vector_store.json"
        self.vector_store_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.vector_store = SimpleVectorStore(dimension=768)
        if self.vector_store_path.exists():
            logger.info(f"📦 Loading vector store from {self.vector_store_path}")
            self.vector_store.load(str(self.vector_store_path))
        
    def check_ollama(self) -> bool:
        """Ollama 서비스 확인"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        로컬 LLM으로 텍스트 임베딩
        nomic-embed-text 사용 (빠르고 정확)
        """
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()["embedding"]
            else:
                logger.warning(f"⚠️ Embedding failed: {response.status_code}")
                return None
        except Exception as e:
            logger.warning(f"⚠️ Ollama not available: {e}")
            return None
    
    def store_memory(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        """
        기억을 벡터로 변환하여 영구 저장
        Args:
            doc_id: 고유 ID (파일 경로 등)
            text: 저장할 텍스트
            metadata: 메타데이터 (source, type, timestamp 등)
        """
        vector = self.embed_text(text)
        if vector is None:
            logger.warning(f"⚠️ Could not embed {doc_id}, skipping")
            return
        
        self.vector_store.add(doc_id, vector, {
            **metadata,
            "text": text[:500],  # 500자만 메타데이터에 저장
            "full_text_length": len(text),
            "stored_at": datetime.now(timezone.utc).isoformat()
        })
        
        # 즉시 저장 (재부팅 대비)
        self.vector_store.save(str(self.vector_store_path))
        logger.info(f"✅ Stored memory: {doc_id}")
    
    def recall(self, query: str, top_k: int = 5, min_similarity: float = 0.3) -> List[Tuple[float, Dict[str, Any]]]:
        """
        질문과 유사한 기억 회상
        Args:
            query: 검색 질문
            top_k: 최대 결과 수
            min_similarity: 최소 유사도 (0.0 ~ 1.0)
        Returns:
            [(similarity, metadata), ...]
        """
        query_vec = self.embed_text(query)
        if query_vec is None:
            logger.warning("⚠️ Could not embed query, fallback to keyword search")
            return []
        
        results = self.vector_store.search(query_vec, top_k=top_k)
        
        # 최소 유사도 필터링
        filtered = [(sim, meta) for sim, meta in results if sim >= min_similarity]
        
        logger.info(f"🔍 Recalled {len(filtered)}/{len(results)} memories for: {query[:50]}...")
        return filtered
    
    def auto_index_recent_files(self, hours: int = 24, max_files: int = 100):
        """
        최근 파일들을 자동으로 인덱싱
        Hippocampus의 Everything 검색 결과 활용
        """
        logger.info(f"📚 Auto-indexing recent {hours}h files (max {max_files})")
        
        # Hippocampus의 기존 검색 기능 활용
        recent_files = self.hippocampus.search_recent_files(hours=hours, limit=max_files)
        
        indexed = 0
        for file_path in recent_files:
            try:
                path = Path(file_path)
                if not path.exists():
                    continue
                
                # 텍스트 파일만 처리
                if path.suffix.lower() not in ['.md', '.txt', '.py', '.json', '.ps1']:
                    continue
                
                # 이미 인덱싱된 파일은 스킵
                doc_id = str(path.absolute())
                if doc_id in self.vector_store.doc_ids:
                    continue
                
                # 파일 읽기 (최대 10KB)
                content = path.read_text(encoding='utf-8', errors='ignore')[:10000]
                
                self.store_memory(
                    doc_id=doc_id,
                    text=content,
                    metadata={
                        "source": "file_system",
                        "file_path": str(path),
                        "file_type": path.suffix,
                        "file_size": len(content)
                    }
                )
                indexed += 1
                
            except Exception as e:
                logger.debug(f"⚠️ Could not index {file_path}: {e}")
        
        logger.info(f"✅ Indexed {indexed} new files")
        return indexed
    
    def get_stats(self) -> Dict[str, Any]:
        """벡터 스토어 통계"""
        return {
            "total_memories": len(self.vector_store.doc_ids),
            "dimension": self.vector_store.dimension,
            "store_path": str(self.vector_store_path),
            "store_exists": self.vector_store_path.exists(),
            "ollama_available": self.check_ollama()
        }


def main():
    """테스트 및 자동 인덱싱"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hippocampus RAG System")
    parser.add_argument("--workspace", default="c:/workspace/agi", help="Workspace path")
    parser.add_argument("--query", help="Recall memories by query")
    parser.add_argument("--index-recent", type=int, help="Auto-index recent N hours")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    rag = HippocampusRAG(Path(args.workspace))
    
    if args.stats:
        stats = rag.get_stats()
        print("\n📊 Hippocampus RAG Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    if args.index_recent:
        rag.auto_index_recent_files(hours=args.index_recent)
    
    if args.query:
        results = rag.recall(args.query, top_k=5)
        print(f"\n🔍 Recall results for: {args.query}")
        for i, (sim, meta) in enumerate(results, 1):
            print(f"\n{i}. Similarity: {sim:.3f}")
            print(f"   Source: {meta.get('source', 'unknown')}")
            print(f"   Path: {meta.get('file_path', meta.get('doc_id', 'N/A'))[:80]}")
            print(f"   Preview: {meta.get('text', '')[:150]}...")


if __name__ == "__main__":
    main()
