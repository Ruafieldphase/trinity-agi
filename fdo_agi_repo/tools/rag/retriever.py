from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
import re
import os
import json
import math
from .config_loader import get_rag_config


def _env_true(name: str) -> bool:
    val = os.environ.get(name)
    if not val:
        return False
    return str(val).strip().lower() in ("1", "true", "yes", "y", "on")


def _tokenize(text: str) -> List[str]:
    """간단 토크나이저: 한글/영문/숫자만 유지, 2자 이상 토큰, 불용어 제거"""
    if not text:
        return []
    text = text.lower()
    # 한글, 영문, 숫자 외는 공백으로 치환
    cleaned = re.sub(r"[^0-9a-z\uac00-\ud7a3]+", " ", text)
    raw_tokens = cleaned.split()
    stop = {
        # 한국어 일반 불용어 (간단 셋)
        "및", "그리고", "또는", "그러나", "하지만", "이는", "이", "그", "저", "등",
        # 영어 일반 불용어 (간단 셋)
        "and", "or", "but", "the", "a", "an", "of", "to", "in", "on", "for"
    }
    tokens = [t for t in raw_tokens if len(t) >= 2 and t not in stop]
    return tokens


def _apply_bqi_weights(
    score: float,
    meta: Dict[str, Any],
    bqi_coord: Optional[Dict[str, Any]] = None
) -> float:
    """
    BQI 좌표를 활용한 RAG 검색 가중치 적용
    
    Args:
        score: 기본 BM25 점수
        meta: 문서 메타데이터 (source, ts, event_type 등)
        bqi_coord: BQI 좌표 (priority, emotion, rhythm)
    
    Returns:
        float: 가중치 적용된 점수
    
    Strategy:
        - Priority 4 (긴급): 최근 문서 가중치 증가 (24시간 이내 1.5x)
        - Priority 1 (탐색): 다양성 증가 (시간 제약 완화)
        - Emotion 기반 필터링:
            - concern: 위험 분석, 문제 해결 관련 문서 우선
            - hope: 성공 사례, 긍정적 결과 관련 문서 우선
            - curiosity: 설명, 튜토리얼 관련 문서 우선
        - Rhythm 기반 범위:
            - integration: 교차 도메인 소스 혼합
            - reflection: 평가, 리뷰 문서 우선
            - exploration: 다양한 소스 탐색
    """
    if not bqi_coord:
        return score
    
    priority = bqi_coord.get("priority", 2)
    emotions = bqi_coord.get("emotion", [])
    rhythm = bqi_coord.get("rhythm", "exploration")
    
    weight = 1.0
    
    # Priority 기반 시간 가중치
    if priority == 4:  # 긴급
        # 최근 문서 강조 (24시간 이내 1.5x, 1시간 이내 2.0x)
        ts = meta.get("ts")
        if ts:
            try:
                import time
                now = time.time()
                age_hours = (now - float(ts)) / 3600.0
                if age_hours <= 1.0:
                    weight *= 2.0  # 1시간 이내
                elif age_hours <= 24.0:
                    weight *= 1.5  # 24시간 이내
            except Exception:
                pass
    
    elif priority == 1:  # 탐색
        # 다양성 증가: 오래된 문서도 고려 (시간 페널티 완화)
        ts = meta.get("ts")
        if ts:
            try:
                import time
                now = time.time()
                age_hours = (now - float(ts)) / 3600.0
                if age_hours > 168.0:  # 7일 이상
                    weight *= 1.2  # 오래된 문서 약간 가중치
            except Exception:
                pass
    
    # Emotion 기반 필터링
    event_type = meta.get("event_type", "")
    source = meta.get("source", "")
    
    if "concern" in emotions or "anxiety" in emotions:
        # 위험 분석, 문제 해결 관련
        if event_type in ["evidence_correction", "second_pass", "corrections_skipped"]:
            weight *= 1.3
        if "error" in str(meta.get("snippet", "")).lower():
            weight *= 1.2
    
    if "hope" in emotions or "gratitude" in emotions:
        # 성공 사례, 긍정적 결과
        if event_type in ["task_complete", "learning"]:
            weight *= 1.3
        if "success" in str(meta.get("snippet", "")).lower():
            weight *= 1.2
    
    if "curiosity" in emotions:
        # 설명, 튜토리얼 관련
        if event_type in ["meta_cognition", "rune"]:
            weight *= 1.2
    
    # Rhythm 기반 범위
    if rhythm == "integration":
        # 교차 도메인: coordinate와 ledger 균형
        if source == "coordinate":
            weight *= 1.15
    
    elif rhythm == "reflection":
        # 평가, 리뷰: eval, learning 이벤트 우선
        if event_type in ["eval", "learning", "second_pass"]:
            weight *= 1.25
    
    elif rhythm == "exploration":
        # 다양한 소스 탐색: 특별한 가중치 없음 (기본값 유지)
        pass
    
    return score * weight


def _extract_ledger_text(event: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Ledger 이벤트에서 텍스트 추출. 필드별 가중치를 위해 각 필드를 반복.
    summary와 goal은 2회, reasoning은 1.5회 반복하여 가중치 효과.
    """
    parts = []
    # 중요 필드 (2x 가중치)
    goal = str(event.get("goal", ""))
    summary = str(event.get("summary", ""))
    if goal:
        parts.extend([goal, goal])
    if summary:
        parts.extend([summary, summary])
    
    # 중간 중요도 필드 (1.5x 가중치)
    reasoning = str(event.get("reasoning", ""))
    if reasoning:
        parts.extend([reasoning, reasoning[:len(reasoning)//2]])  # 1.5배 근사
    
    # 일반 필드 (1x)
    parts.append(str(event.get("recommendations", [])))
    
    text = " ".join(parts)
    meta = {
        "source": "resonance_ledger",
        "event_type": event.get("event", "unknown"),
        "task_id": event.get("task_id", "unknown"),
        "ts": event.get("ts")
    }
    return text, meta


def _extract_coord_text(entry: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    좌표 파일에서 텍스트 추출.
    task 구조에서 goal을 추출하되, 메타데이터로 표시.
    """
    text = json.dumps(entry, ensure_ascii=False)
    
    # task_start 이벤트인 경우 goal 추출
    goal_text = ""
    if entry.get("event") == "task_start" and "task" in entry:
        goal_text = str(entry["task"].get("goal", ""))

    # coord_id 보정: id 없을 경우 task_id로 대체 (task.task_id > entry.task_id > unknown)
    coord_id = entry.get("id")
    if not coord_id:
        task_dict = entry.get("task") if isinstance(entry.get("task"), dict) else None
        coord_id = (task_dict.get("task_id") if task_dict and task_dict.get("task_id") else entry.get("task_id"))
    coord_id = coord_id or "unknown"
    
    meta = {
        "source": "coordinate",
        "coord_id": coord_id,
        "is_task_start": entry.get("event") == "task_start",
        "goal": goal_text,
        "type": entry.get("type", ""),  # rune_validation, routing 등
        "ts": entry.get("ts")
    }
    return text, meta


def _build_docs(path: str, is_ledger: bool) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    if not os.path.exists(path):
        return docs
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                text, meta = (_extract_ledger_text(obj) if is_ledger else _extract_coord_text(obj))
                # 빈 텍스트는 스킵
                tokens = _tokenize(text)
                if not tokens:
                    continue
                docs.append({
                    "tokens": tokens,
                    "text": text,
                    "meta": meta,
                })
    except Exception:
        # 실패 시 빈 목록 반환
        return []
    return docs


def _bm25_score(query_tokens: List[str], doc_tokens: List[str], df: Dict[str, int], N: int, avgdl: float,
                k1: float = 1.2, b: float = 0.75, source_boost: float = 1.0) -> float:
    if not query_tokens or not doc_tokens or N <= 0:
        return 0.0
    # 문서 토큰 빈도
    tf: Dict[str, int] = {}
    for t in doc_tokens:
        tf[t] = tf.get(t, 0) + 1
    dl = len(doc_tokens)

    score = 0.0
    for q in set(query_tokens):
        df_q = df.get(q, 0)
        if df_q == 0:
            continue
        # BM25 idf (Okapi variant)
        idf = math.log((N - df_q + 0.5) / (df_q + 0.5) + 1.0)
        tf_q = tf.get(q, 0)
        if tf_q == 0:
            continue
        denom = tf_q + k1 * (1 - b + b * (dl / (avgdl or 1.0)))
        score += idf * (tf_q * (k1 + 1)) / denom
    
    # 소스별 가중치 적용
    return score * source_boost


def _make_snippet(text: str, query_tokens: List[str], max_len: int = 200) -> str:
    if not text:
        return ""
    try:
        lower = text.lower()
        pos = -1
        for q in query_tokens:
            i = lower.find(q)
            if i != -1:
                pos = i if pos == -1 else min(pos, i)
        if pos == -1:
            return text[:max_len]
        start = max(0, pos - 60)
        end = min(len(text), pos + max_len - 60)
        return text[start:end]
    except Exception:
        return text[:max_len]


def _jaccard_similarity(a_tokens: List[str], b_tokens: List[str]) -> float:
    """Jaccard 유사도 (0~1). 두 토큰 집합의 교집합/합집합."""
    if not a_tokens or not b_tokens:
        return 0.0
    a = set(a_tokens)
    b = set(b_tokens)
    union = a | b
    if not union:
        return 0.0
    inter = a & b
    return len(inter) / len(union)


def rag_query(query: str, top_k: int = 8, include_types: Optional[List[str]] = None,
              fallback_on_empty: bool = True,
              fallback_include_types: Optional[List[str]] = None,
              ledger_path: str = "memory/resonance_ledger.jsonl",
              coord_path: str = "memory/coordinate.jsonl",
              bqi_coord: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    BM25 기반 RAG 검색 (BQI 좌표 가중치 지원)
    
    Args:
        query: 검색 쿼리
        top_k: 반환할 최대 문서 수
        include_types: 포함할 이벤트 타입 필터
        fallback_on_empty: 빈 결과 시 폴백 활성화
        fallback_include_types: 폴백 시 사용할 타입 필터
        ledger_path: Ledger JSONL 경로
        coord_path: Coordinate JSONL 경로
        bqi_coord: BQI 좌표 (priority, emotion, rhythm) - Phase 3 추가
    
    Returns:
        Dict[str, Any]: {"ok": bool, "hits": List[...], ...}
    """
    # 환경 변수로 비활성화 가능
    if _env_true("RAG_DISABLE"):
        return {"ok": True, "hits": []}

    q_tokens = _tokenize(query)
    if not q_tokens:
        return {"ok": True, "hits": []}

    # 문서 경로 보정: 상대 경로는 리포지토리 루트를 기준으로 해석
    try:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    except Exception:
        repo_root = os.getcwd()

    def _resolve(p: str) -> str:
        if not p:
            return p
        return p if os.path.isabs(p) else os.path.join(repo_root, p)

    ledger_path_resolved = _resolve(ledger_path)
    coord_path_resolved = _resolve(coord_path)

    # 문서 수집
    ledger_docs = _build_docs(ledger_path_resolved, is_ledger=True)
    coord_docs = _build_docs(coord_path_resolved, is_ledger=False)

    docs = ledger_docs + coord_docs
    if not docs:
        return {"ok": True, "hits": []}

    # 구성값 로드 (BM25 파라미터 및 추후 확장 대비)
    cfg = get_rag_config()
    bm25_cfg = (cfg.get("bm25") or {})
    k1 = float(bm25_cfg.get("k1", 1.2))
    b = float(bm25_cfg.get("b", 0.75))
    weights = cfg.get("weights") or {}
    w_ledger = weights.get("ledger", {})
    w_coord = weights.get("coordinate", {})
    recency_cfg = cfg.get("recency") or {}
    recency_enabled = bool(recency_cfg.get("enabled", True))
    half_life_hours = float(recency_cfg.get("half_life_hours", 24.0))
    mmr_cfg = cfg.get("mmr") or {}
    mmr_enabled = bool(mmr_cfg.get("enabled", True))
    mmr_lambda = float(mmr_cfg.get("lambda", 0.7))

    def _filter_docs_by_types(in_docs: List[Dict[str, Any]], types: Optional[List[str]]) -> List[Dict[str, Any]]:
        """
        include_types 필터를 적용. 
        - coordinate: meta.type 와 task_start 이벤트를 모두 고려 (task_start 매칭 지원)
        - ledger: meta.event_type 사용
        여러 태그 중 하나라도 허용 집합에 있으면 통과.
        """
        if types is None:
            return in_docs
        out: List[Dict[str, Any]] = []
        allow = set(t for t in types if t)
        for d in in_docs:
            meta = d.get("meta", {})
            tags: set[str] = set()
            if meta.get("source") == "coordinate":
                d_type = meta.get("type")
                if d_type:
                    tags.add(str(d_type))
                if meta.get("is_task_start"):
                    tags.add("task_start")
            else:
                ev = meta.get("event_type")
                if ev:
                    tags.add(str(ev))
            if tags & allow:
                out.append(d)
        return out

    used_fallback = False
    initial_total_found = 0

    def _score_with_docs(work_docs: List[Dict[str, Any]]) -> Tuple[List[Tuple[float, Dict[str, Any], List[str]]], int, float]:
        N = len(work_docs)
        if N == 0:
            return [], 0, 0.0
        # DF 및 평균 길이 계산
        df: Dict[str, int] = {}
        total_len = 0
        for d in work_docs:
            total_len += len(d["tokens"])
            seen = set()
            for t in d["tokens"]:
                if t in seen:
                    continue
                seen.add(t)
                df[t] = df.get(t, 0) + 1
        avgdl = total_len / max(1, N)

        # 점수 계산 (소스 및 이벤트 타입별 가중치 적용)
        scored_local: List[Tuple[float, Dict[str, Any], List[str]]] = []
        query_lower = query.lower()
        for d in work_docs:
            # 기본 소스 가중치
            if d["meta"]["source"] == "resonance_ledger":
                # Ledger는 이벤트 타입에 따라 가중치 조정
                event_type = d["meta"].get("event_type", "")
                source_boost = float(w_ledger.get(event_type, w_ledger.get("default", 0.5)))
            else:
                # Coordinate는 타입별 가중치
                entry_type = d["meta"].get("type", "")
                is_task_start = d["meta"].get("is_task_start", False)
                if is_task_start:
                    # task_start 자체 가중치 키 지원
                    source_boost = float(w_coord.get("task_start", w_coord.get("default", 1.0)))
                else:
                    source_boost = float(w_coord.get(entry_type, w_coord.get("default", 1.0)))

            score = _bm25_score(q_tokens, d["tokens"], df, N, avgdl, k1=k1, b=b, source_boost=source_boost)
            if score <= 0:
                continue

            # Exact match & Near-match penalty for task_start.goal
            if d["meta"].get("is_task_start") and d["meta"].get("goal"):
                goal_lower = d["meta"]["goal"].lower()
                if goal_lower == query_lower:
                    score *= 0.05  # 95% 페널티 (완전 동일)
                else:
                    sim = _jaccard_similarity(q_tokens, _tokenize(goal_lower))
                    if sim >= 0.8:
                        score *= 0.2  # 강한 페널티
                    elif sim >= 0.6:
                        score *= 0.5  # 중간 페널티

            # Recency decay (if timestamp available)
            if recency_enabled:
                ts = d["meta"].get("ts")
                try:
                    if ts:
                        import time
                        now = time.time()
                        age_hours = max(0.0, (now - float(ts)) / 3600.0)
                        if half_life_hours > 0:
                            decay = 0.5 ** (age_hours / half_life_hours)
                            score *= decay
                except Exception:
                    pass

                # BQI 가중치 적용 (Phase 3)
                if bqi_coord:
                    score = _apply_bqi_weights(score, d["meta"], bqi_coord)

            meta = d["meta"].copy()
            meta["relevance"] = float(score)
            meta["snippet"] = _make_snippet(d["text"], q_tokens)
            scored_local.append((score, meta, d["tokens"]))

        return scored_local, N, avgdl

    # 1차: include_types 적용 스코어링
    work_docs = _filter_docs_by_types(docs, include_types)
    scored, N_used, _ = _score_with_docs(work_docs)
    initial_total_found = len(scored)

    # 폴백: 히트 없을 때 더 넓게 검색
    if fallback_on_empty and include_types is not None and len(scored) == 0:
        # 2단계: 지정된 폴백 타입 우선
        fb_types = fallback_include_types if fallback_include_types else None
        fb_docs = _filter_docs_by_types(docs, fb_types)
        scored, N_used, _ = _score_with_docs(fb_docs)
        used_fallback = True

    if not scored:
        return {
            "ok": True,
            "hits": [],
            "total_found": 0,
            "used_fallback": used_fallback,
            "initial_total_found": initial_total_found,
        }

    # 상위 정렬 및 결과 정규화 (상대적 점수로 0~1 스케일링)
    scored.sort(key=lambda x: x[0], reverse=True)
    # MMR diversification
    selected: List[Tuple[float, Dict[str, Any], List[str]]] = []
    if mmr_enabled and len(scored) > 1:
        # Greedy selection
        while scored and len(selected) < max(1, top_k):
            if not selected:
                selected.append(scored.pop(0))
                continue
            best_idx = 0
            best_obj = None
            best_value = -1e9
            for i, (s, m, toks) in enumerate(scored):
                # Diversity: 1 - max Jaccard to selected
                max_sim = 0.0
                for (_, __, stoks) in selected:
                    sim = _jaccard_similarity(list(set(toks)), list(set(stoks)))
                    if sim > max_sim:
                        max_sim = sim
                value = mmr_lambda * s + (1 - mmr_lambda) * (1.0 - max_sim)
                if value > best_value:
                    best_value = value
                    best_idx = i
                    best_obj = (s, m, toks)
            if best_obj is not None:
                selected.append(best_obj)
                scored.pop(best_idx)
            else:
                break
        top = selected
    else:
        top = scored[:max(1, top_k)]

    max_score = top[0][0] if top else 1.0

    hits: List[Dict[str, Any]] = []
    for score, meta, _tokens in top:
        rel = score / (max_score or 1.0)
        out: Dict[str, Any] = {
            "id": None,
            "source": meta.get("source"),
            "relevance": round(rel, 4),
            "snippet": meta.get("snippet", ""),
        }
        if meta.get("source") == "resonance_ledger":
            out["id"] = f"ledger_{meta.get('task_id', 'unknown')}_{meta.get('event_type', 'unknown')}"
            out["event_type"] = meta.get("event_type")
            out["task_id"] = meta.get("task_id")
        elif meta.get("source") == "coordinate":
            out["id"] = f"coord_{meta.get('coord_id', 'unknown')}"
        else:
            out["id"] = "doc"
        hits.append(out)

    return {
        "ok": True,
        "hits": hits,
        "total_found": len(scored),
        "used_fallback": used_fallback,
        "initial_total_found": initial_total_found,
    }
