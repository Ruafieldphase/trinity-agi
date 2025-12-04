"""
Embedding Service for Dense Retrieval
Vertex AI text-embedding-004 우선 사용, 폴백으로 해시 기반 임베딩
"""
from __future__ import annotations
from typing import List, Optional
import hashlib
import os
import logging

logger = logging.getLogger(__name__)

# Vertex AI 임포트 시도
try:
    import vertexai
    from vertexai.language_models import TextEmbeddingModel
    VERTEXAI_AVAILABLE = True
except ImportError:
    VERTEXAI_AVAILABLE = False
    logger.warning("Vertex AI SDK not available, falling back to hash-based embeddings")


class EmbeddingService:
    """
    텍스트를 벡터로 변환하는 서비스
    - Vertex AI text-embedding-004 (768-dim) 우선 사용
    - 실패 시 해시 기반 임베딩 (128-dim) 폴백
    """
    
    def __init__(self, model_name: str = "text-embedding-004", dimension: int = 768):
        self.model_name = model_name
        self.dimension = dimension
        self._model: Optional[TextEmbeddingModel] = None
        self._initialized = False
        
    def embed(self, text: str) -> List[float]:
        """
        텍스트를 벡터로 변환
        Returns: dimension-크기 리스트
        """
        if not text or not text.strip():
            return [0.0] * self.dimension
        
        # Vertex AI 시도
        if VERTEXAI_AVAILABLE and not self._initialized:
            try:
                self._initialize_vertex_ai()
            except Exception as e:
                logger.warning(f"Vertex AI initialization failed: {e}")
                self._initialized = True  # 재시도 방지
        
        if self._model is not None:
            try:
                response = self._model.get_embeddings([text])
                if response and len(response) > 0:
                    embedding = response[0].values
                    # 차원 맞추기 (768 미만이면 제로 패딩, 초과면 자르기)
                    if len(embedding) < self.dimension:
                        embedding = list(embedding) + [0.0] * (self.dimension - len(embedding))
                    elif len(embedding) > self.dimension:
                        embedding = list(embedding[:self.dimension])
                    return embedding
            except Exception as e:
                logger.warning(f"Vertex AI embedding failed: {e}, falling back to hash")
        
        # 폴백: 해시 기반 임베딩
        return self._hash_embedding(text)
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        배치 임베딩 (메모리 효율 고려)
        """
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            for text in batch:
                results.append(self.embed(text))
        return results
    
    def _initialize_vertex_ai(self):
        """Vertex AI 모델 초기화"""
        if not VERTEXAI_AVAILABLE:
            return
        
        project_id = os.getenv("VERTEX_PROJECT_ID", "")
        location = os.getenv("VERTEX_LOCATION", "us-central1")
        
        if project_id:
            vertexai.init(project=project_id, location=location)
            self._model = TextEmbeddingModel.from_pretrained(self.model_name)
            self._initialized = True
            logger.info(f"Vertex AI embedding model initialized: {self.model_name}")
        else:
            logger.warning("VERTEX_PROJECT_ID not set, skipping Vertex AI init")
            self._initialized = True
    
    def _hash_embedding(self, text: str) -> List[float]:
        """
        해시 기반 임베딩 폴백 (128-dim)
        - 단순하지만 일관된 벡터 생성
        - 실제 semantic 유사도는 없지만 BM25와 조합 시 안전한 폴백
        """
        # SHA256 해시를 16개 블록으로 나눠 128-dim 벡터 생성
        h = hashlib.sha256(text.encode("utf-8")).digest()
        # 32바이트를 4개씩 묶어 8개 float으로 변환 후 반복
        floats = []
        for i in range(0, 32, 4):
            chunk = int.from_bytes(h[i:i+4], byteorder="big")
            normalized = (chunk / (2**32 - 1)) * 2.0 - 1.0  # -1~1 정규화
            floats.append(normalized)
        
        # 8개를 16번 반복 = 128-dim, 768-dim까지 제로 패딩
        base = floats * 16  # 128
        if len(base) < self.dimension:
            base = base + [0.0] * (self.dimension - len(base))
        return base[:self.dimension]


# 싱글턴 인스턴스
_embedding_service: Optional[EmbeddingService] = None

def get_embedding_service() -> EmbeddingService:
    """싱글턴 EmbeddingService 접근자"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
