"""
Hybrid RAG Query: BM25 + Dense Embedding with Reciprocal Rank Fusion
"""
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
import logging
import os

from .retriever import rag_query as bm25_rag_query
from .embedding_service import get_embedding_service
from .vector_store import get_vector_store
from .config_loader import get_rag_config

logger = logging.getLogger(__name__)


def _env_true(name: str) -> bool:
    """환경 변수가 true로 설정되어 있는지 확인"""
    return str(os.environ.get(name, "")).strip().lower() in ("1", "true", "yes", "y", "on")


def reciprocal_rank_fusion(
    bm25_hits: List[Tuple[str, float]],
    dense_hits: List[Tuple[str, float]],
    k: int = 60,
) -> List[Tuple[str, float]]:
    """
    Reciprocal Rank Fusion (RRF)
    - 두 검색 결과를 순위 기반으로 병합
    - k: RRF 파라미터 (보통 60)
    
    Args:
        bm25_hits: [(doc_id, bm25_score), ...]
        dense_hits: [(doc_id, dense_score), ...]
    
    Returns:
        [(doc_id, rrf_score), ...] (내림차순 정렬)
    """
    rrf_scores: Dict[str, float] = {}
    
    # BM25 순위 기반 점수
    for rank, (doc_id, _) in enumerate(bm25_hits, start=1):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank))
    
    # Dense 순위 기반 점수
    for rank, (doc_id, _) in enumerate(dense_hits, start=1):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank))
    
    # 내림차순 정렬
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_items


def hybrid_rag_query(
    query: str,
    top_k: int = 8,
    include_types: Optional[List[str]] = None,
    fallback_on_empty: bool = True,
    fallback_include_types: Optional[List[str]] = None,
    ledger_path: str = "memory/resonance_ledger.jsonl",
    coord_path: str = "memory/coordinate.jsonl",
    vector_store_path: str = "memory/vector_store.json",
    enable_dense: bool = True,
) -> Dict[str, Any]:
    """
    Hybrid RAG Query (BM25 + Dense Embedding)
    
    Args:
        query: 검색 쿼리
        top_k: 반환할 결과 수
        include_types: 타입 필터 (BM25에만 적용)
        fallback_on_empty: 빈 결과 시 폴백
        fallback_include_types: 폴백 타입
        ledger_path: Ledger 경로
        coord_path: Coordinate 경로
        vector_store_path: VectorStore 경로
        enable_dense: Dense retrieval 활성화 (False면 BM25만)
    
    Returns:
        {"ok": bool, "hits": [...], "bm25_hits": int, "dense_hits": int, "used_hybrid": bool}
    """
    # RAG_DISABLE 환경 변수 체크 (테스트 시 완전 비활성화)
    if _env_true("RAG_DISABLE"):
        return {"ok": True, "hits": [], "total_found": 0, "bm25_hits": 0, "dense_hits": 0, "used_hybrid": False}
    
    # 1. BM25 검색 (기존 로직)
    bm25_result = bm25_rag_query(
        query=query,
        top_k=top_k * 2,  # RRF를 위해 더 많이 가져옴
        include_types=include_types,
        fallback_on_empty=fallback_on_empty,
        fallback_include_types=fallback_include_types,
        ledger_path=ledger_path,
        coord_path=coord_path,
    )
    
    bm25_hits_data = bm25_result.get("hits", [])
    bm25_hits_ids = [(hit["id"], hit["relevance"]) for hit in bm25_hits_data]
    
    # 2. Dense Embedding 검색
    dense_hits_ids = []
    if enable_dense:
        try:
            emb_service = get_embedding_service()
            vector_store = get_vector_store(vector_store_path)
            
            if len(vector_store) > 0:
                query_embedding = emb_service.embed(query)
                dense_results = vector_store.search(query_embedding, top_k=top_k * 2)
                
                # (similarity, metadata) -> (doc_id, score)
                dense_hits_ids = [(meta["doc_id"], sim) for sim, meta in dense_results]
            else:
                logger.debug("VectorStore is empty, skipping dense retrieval")
        except Exception as e:
            logger.warning(f"Dense retrieval failed: {e}, falling back to BM25 only")
    
    # 3. RRF 병합
    if dense_hits_ids:
        rrf_scores = reciprocal_rank_fusion(bm25_hits_ids, dense_hits_ids)
        merged_doc_ids = [doc_id for doc_id, _ in rrf_scores[:top_k]]
        used_hybrid = True
    else:
        # Dense 실패 시 BM25만 사용
        merged_doc_ids = [doc_id for doc_id, _ in bm25_hits_ids[:top_k]]
        used_hybrid = False
    
    # 4. 메타데이터 병합 (BM25 hits에서 추출, vectorstore에서 보완)
    hits = []
    bm25_hits_map = {hit["id"]: hit for hit in bm25_hits_data}
    
    for doc_id in merged_doc_ids:
        if doc_id in bm25_hits_map:
            hits.append(bm25_hits_map[doc_id])
        else:
            # VectorStore에서 가져온 doc_id (BM25에 없음)
            # vector_store metadata에서 정보 복원
            try:
                vector_store = get_vector_store(vector_store_path)
                idx = vector_store.doc_ids.index(doc_id)
                meta = vector_store.metadata[idx]
                
                hits.append({
                    "id": doc_id,
                    "source": meta.get("source", "codebase"),
                    "relevance": 0.5,  # 기본 relevance (RRF 점수는 별도 저장 안함)
                    "snippet": meta.get("text", "")[:200],
                    "file_path": meta.get("file_path", ""),
                })
            except Exception as e:
                logger.warning(f"Failed to retrieve metadata for {doc_id}: {e}")
    
    return {
        "ok": True,
        "hits": hits,
        "total_found": len(hits),
        "bm25_hits": len(bm25_hits_ids),
        "dense_hits": len(dense_hits_ids),
        "used_hybrid": used_hybrid,
    }
