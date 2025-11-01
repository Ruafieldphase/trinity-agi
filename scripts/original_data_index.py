import json
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

ISO_FORMATS = (
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S",
)


def _parse_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ISO_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            continue
    # try from timestamp
    try:
        return datetime.fromtimestamp(float(value))
    except Exception:
        return None


def load_index(index_path: str = os.path.join("outputs", "original_data_index.json")) -> List[Dict[str, Any]]:
    if not os.path.exists(index_path):
        raise FileNotFoundError(
            f"Index file not found: {index_path}. Build it first (e.g., 'Original Data: Build Index')."
        )
    with open(index_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Normalize to list of entries
    if isinstance(data, dict) and "items" in data and isinstance(data["items"], list):
        items = data["items"]
    elif isinstance(data, list):
        items = data
    else:
        # Unknown shape, try to wrap as list
        items = [data]
    return items


def _get_field(entry: Dict[str, Any], *names: str, default: Any = None) -> Any:
    for n in names:
        if n in entry:
            return entry[n]
    return default


def _to_tags(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v]
    if isinstance(v, str):
        # split common separators
        parts = re.split(r"[,;\s]+", v.strip())
        return [p for p in parts if p]
    return [str(v)]


def _matches_tokens(hay: str, tokens: Sequence[str]) -> int:
    score = 0
    hay_l = hay.lower()
    for t in tokens:
        if t and t.lower() in hay_l:
            score += 1
    return score


def search_index(
    items: List[Dict[str, Any]],
    query: Optional[str] = None,
    tags: Optional[Sequence[str]] = None,
    exts: Optional[Sequence[str]] = None,
    since_days: Optional[int] = None,
    top: int = 20,
) -> List[Dict[str, Any]]:
    tokens: List[str] = []
    if query:
        # split by whitespace/commas
        tokens = [t for t in re.split(r"[,\s]+", query.strip()) if t]

    tag_set = set([t.lower() for t in (tags or []) if t])
    ext_set = set([e.lower().lstrip(".") for e in (exts or []) if e])

    now = datetime.utcnow()
    min_time: Optional[datetime] = None
    if since_days and since_days > 0:
        min_time = now - timedelta(days=since_days)

    results: List[Tuple[float, Dict[str, Any]]] = []

    for e in items:
        path = _get_field(e, "relative_path", "path", "file", default="") or ""
        name = _get_field(e, "name", default="") or ""
        keywords = _to_tags(_get_field(e, "keywords", "tags", default=[]))
        ext = (_get_field(e, "ext", default="") or "").lstrip(".")
        mtime_iso = _get_field(e, "mtime_iso", "last_modified", "modified", default=None)
        mtime_dt = _parse_time(mtime_iso)

        if min_time and mtime_dt and mtime_dt < min_time:
            continue

        # extension filter
        if ext_set and ext.lower() not in ext_set:
            continue

        # tags filter
        if tag_set and not (set([k.lower() for k in keywords]) & tag_set):
            continue

        # scoring
        text = " ".join([path, name, " ".join(keywords)])
        score = 0.0
        if tokens:
            score += _matches_tokens(text, tokens)
        # tag match bonus
        if tag_set:
            score += len(set([k.lower() for k in keywords]) & tag_set) * 2
        # ext match bonus
        if ext_set and ext.lower() in ext_set:
            score += 0.5
        # recency bonus
        if mtime_dt:
            age_days = max(0.0, (now - mtime_dt).total_seconds() / (3600 * 24))
            score += max(0.0, 3.0 - min(age_days, 30.0) * 0.1)  # up to +3

        # if no tokens/tags/ext provided, include all with small base score
        if score == 0.0 and not (tokens or tag_set or ext_set or min_time):
            score = 1.0

        results.append((score, e))

    # sort: score desc, mtime desc, path asc
    def sort_key(it: Tuple[float, Dict[str, Any]]):
        sc, e = it
        mt = _parse_time(_get_field(e, "mtime_iso", "last_modified", "modified", default=None))
        return (-sc, -(mt.timestamp() if mt else 0.0), str(_get_field(e, "relative_path", "path", "file", default="")))

    results.sort(key=sort_key)
    top_n = [e for _, e in results[: max(1, top)]]

    # attach safe fields for convenience
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    for e in top_n:
        rel = _get_field(e, "relative_path", "path", "file", default="") or ""
        if rel and not os.path.isabs(rel):
            abs_path = os.path.join(root, rel)
        else:
            abs_path = rel
        e.setdefault("absolute_path", abs_path)
        e.setdefault("ext", (_get_field(e, "ext", default="") or "").lstrip("."))
        e.setdefault("tags", _to_tags(_get_field(e, "tags", "keywords", default=[])))
    return top_n
