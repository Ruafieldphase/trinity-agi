#!/usr/bin/env python3
"""
요약 텍스트 임베딩 서비스

환경에 Vertex AI SDK가 설치돼 있다면 `text-embedding-004` 모델을 우선 사용하고,
그렇지 않은 경우 간단한 해시 임베딩으로 대체한다. 해시 임베딩은 외부 의존성이
없어 로컬·오프라인 환경에서도 동작하도록 하기 위한 안전 장치다.
"""

from __future__ import annotations

import hashlib
import logging
import math
import os
from functools import lru_cache
from typing import Iterable, List, Optional

logger = logging.getLogger(__name__)

try:  # Vertex AI SDK는 선택 사항
    from vertexai.language_models import TextEmbeddingModel  # type: ignore
except Exception:  # pragma: no cover - SDK가 없는 환경 대비
    TextEmbeddingModel = None  # type: ignore


class EmbeddingService:
    """요약 텍스트 임베딩을 생성하는 서비스"""

    def __init__(
        self,
        model_name: str | None = None,
        fallback_dims: int = 384,
    ):
        # 환경변수에서 모델명 우선 읽기
        self.model_name = model_name or os.getenv("EMBEDDINGS_MODEL") or "text-embedding-004"
        self.fallback_dims = fallback_dims
        self._model = None

    # ------------------------------
    # 공개 API
    # ------------------------------
    def embed(self, text: str) -> List[float]:
        """
        주어진 텍스트에 대한 임베딩 벡터를 반환한다.
        Vertex AI 임베딩 모델이 사용 가능하면 해당 결과를, 그렇지 않으면
        간단한 해시 임베딩을 사용한다.
        """
        text = (text or "").strip()
        if not text:
            return []

        model = self._load_model()
        if model:
            try:
                response = model.get_embeddings([text])
                if response:
                    vector = list(response[0].values)
                    if vector:
                        return vector
            except Exception as exc:  # pragma: no cover - 네트워크/SDK 오류
                logger.warning(
                    "Vertex 임베딩 호출 실패, 해시 임베딩으로 대체합니다: %s", exc
                )

        return self._hash_embedding(text)

    def cosine_similarity(self, lhs: Iterable[float], rhs: Iterable[float]) -> float:
        """두 벡터의 코사인 유사도를 계산한다."""
        lhs_list = list(lhs)
        rhs_list = list(rhs)
        if not lhs_list or not rhs_list:
            return 0.0

        length = min(len(lhs_list), len(rhs_list))
        dot = sum(lhs_list[i] * rhs_list[i] for i in range(length))
        lhs_norm = math.sqrt(sum(v * v for v in lhs_list[:length]))
        rhs_norm = math.sqrt(sum(v * v for v in rhs_list[:length]))

        if lhs_norm == 0 or rhs_norm == 0:
            return 0.0
        return float(dot / (lhs_norm * rhs_norm))

    # ------------------------------
    # 내부 유틸리티
    # ------------------------------
    def _load_model(self):
        """Vertex 임베딩 모델을 로드한다."""
        if TextEmbeddingModel is None:
            return None
        if self._model is None:
            try:
                self._model = TextEmbeddingModel.from_pretrained(self.model_name)
            except Exception as exc:  # pragma: no cover - SDK/네트워크 오류
                logger.warning("Vertex 임베딩 모델 로드 실패: %s", exc)
                self._model = None
        return self._model

    def _hash_embedding(self, text: str) -> List[float]:
        """의존성 없는 해시 임베딩 (SimHash 유사 접근)"""
        dims = self.fallback_dims
        vector = [0.0] * dims
        for token in self._tokenize(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % dims
            vector[index] += 1.0

        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    def _tokenize(self, text: str) -> List[str]:
        """아주 단순한 토크나이저 (공백/구두점 기준 분리)"""
        tokens: List[str] = []
        current = []
        for ch in text.lower():
            if ch.isalnum():
                current.append(ch)
            else:
                if current:
                    tokens.append("".join(current))
                    current = []
        if current:
            tokens.append("".join(current))
        return tokens


_EMBEDDING_SERVICE: Optional[EmbeddingService] = None


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """싱글턴 EmbeddingService 접근자"""
    global _EMBEDDING_SERVICE
    if _EMBEDDING_SERVICE is None:
        _EMBEDDING_SERVICE = EmbeddingService()
    return _EMBEDDING_SERVICE


def reset_embedding_service():
    """테스트 등을 위한 EmbeddingService 리셋"""
    global _EMBEDDING_SERVICE
    _EMBEDDING_SERVICE = None
    get_embedding_service.cache_clear()  # type: ignore[attr-defined]
