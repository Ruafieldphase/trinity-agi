"""
Simple Vector Store for Dense Retrieval
numpy 기반 벡터 저장 및 코사인 유사도 검색
"""
from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
import json
import os
import logging

import numpy as np

logger = logging.getLogger(__name__)


class SimpleVectorStore:
    """
    numpy 기반 간단한 벡터 저장소
    - 인메모리 벡터 저장 및 코사인 유사도 검색
    - JSON 직렬화 가능 (persist/load)
    """
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.vectors: np.ndarray = np.zeros((0, dimension), dtype=np.float32)
        self.metadata: List[Dict[str, Any]] = []
        self.doc_ids: List[str] = []
    
    def add(self, doc_id: str, vector: List[float], meta: Dict[str, Any]):
        """
        벡터와 메타데이터 추가
        Args:
            doc_id: 문서 고유 ID (중복 방지)
            vector: dimension 크기 리스트
            meta: 문서 메타데이터 (source, text, snippet 등)
        """
        # 중복 방지
        if doc_id in self.doc_ids:
            logger.debug(f"Document {doc_id} already exists, skipping")
            return
        
        vec = np.array(vector, dtype=np.float32)
        if vec.shape[0] != self.dimension:
            logger.warning(f"Vector dimension mismatch: {vec.shape[0]} != {self.dimension}")
            # 제로 패딩 또는 자르기
            if vec.shape[0] < self.dimension:
                vec = np.pad(vec, (0, self.dimension - vec.shape[0]), mode='constant')
            else:
                vec = vec[:self.dimension]
        
        # 정규화 (코사인 유사도 계산 최적화)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        
        self.vectors = np.vstack([self.vectors, vec.reshape(1, -1)])
        self.metadata.append(meta)
        self.doc_ids.append(doc_id)
    
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[float, Dict[str, Any]]]:
        """
        코사인 유사도 기반 검색
        Returns: [(similarity_score, metadata), ...] (내림차순)
        """
        if len(self.vectors) == 0:
            return []
        
        qvec = np.array(query_vector, dtype=np.float32)
        if qvec.shape[0] != self.dimension:
            if qvec.shape[0] < self.dimension:
                qvec = np.pad(qvec, (0, self.dimension - qvec.shape[0]), mode='constant')
            else:
                qvec = qvec[:self.dimension]
        
        # 정규화
        norm = np.linalg.norm(qvec)
        if norm > 0:
            qvec = qvec / norm
        
        # 코사인 유사도 (벡터가 이미 정규화됨)
        similarities = np.dot(self.vectors, qvec)
        
        # 상위 top_k 인덱스
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            sim = float(similarities[idx])
            meta = self.metadata[idx].copy()
            meta["doc_id"] = self.doc_ids[idx]
            results.append((sim, meta))
        
        return results
    
    def save(self, path: str):
        """JSON으로 저장 (벡터는 리스트로 변환)"""
        data = {
            "dimension": self.dimension,
            "doc_ids": self.doc_ids,
            "vectors": self.vectors.tolist(),
            "metadata": self.metadata,
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"VectorStore saved to {path} ({len(self.doc_ids)} docs)")
    
    @classmethod
    def load(cls, path: str) -> "SimpleVectorStore":
        """JSON에서 로드"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"VectorStore not found: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        store = cls(dimension=data["dimension"])
        store.doc_ids = data["doc_ids"]
        store.vectors = np.array(data["vectors"], dtype=np.float32)
        store.metadata = data["metadata"]
        
        logger.info(f"VectorStore loaded from {path} ({len(store.doc_ids)} docs)")
        return store
    
    def __len__(self) -> int:
        return len(self.doc_ids)


# 글로벌 인스턴스 (lazy load)
_vector_store: Optional[SimpleVectorStore] = None

def get_vector_store(store_path: str = "memory/vector_store.json") -> SimpleVectorStore:
    """
    싱글턴 VectorStore 접근자
    - 첫 호출 시 파일에서 로드 시도
    - 파일 없으면 빈 스토어 생성
    """
    global _vector_store
    if _vector_store is None:
        # 리포지토리 루트 기준 경로 보정
        try:
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
            full_path = os.path.join(repo_root, store_path)
        except Exception:
            full_path = store_path
        
        if os.path.exists(full_path):
            try:
                _vector_store = SimpleVectorStore.load(full_path)
            except Exception as e:
                logger.warning(f"Failed to load VectorStore: {e}, creating new one")
                _vector_store = SimpleVectorStore()
        else:
            logger.info(f"VectorStore not found at {full_path}, creating new one")
            _vector_store = SimpleVectorStore()
    
    return _vector_store
