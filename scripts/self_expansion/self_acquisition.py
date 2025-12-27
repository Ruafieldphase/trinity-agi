from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import json
import glob


@dataclass
class AcquisitionResult:
    source: str
    payload: Any
    meta: Dict[str, Any] = field(default_factory=dict)


class SelfAcquisition:
    """
    Self-Acquisition (자기 획득) 스켈레톤
    - 다양한 소스(웹/파일/로그/시뮬/센서)를 플러그인으로 연결
    - 무작위·히트맵 기반 탐색으로 새로운 '점'을 수집
    - 결과는 상위 파이프라인이 압축/통합하도록 반환
    """

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.sources: List[Callable[[], AcquisitionResult]] = []

    def register_source(self, fetch_fn: Callable[[], AcquisitionResult]) -> None:
        self.sources.append(fetch_fn)

    def _sample_source(self) -> Optional[Callable[[], AcquisitionResult]]:
        if not self.sources:
            return None
        return random.choice(self.sources)

    def acquire_once(self) -> Optional[AcquisitionResult]:
        fn = self._sample_source()
        if not fn:
            return None
        try:
            return fn()
        except Exception:
            return None

    def acquire_batch(self, batch_size: int = 3, max_time: float = 5.0) -> List[AcquisitionResult]:
        results: List[AcquisitionResult] = []
        start = time.time()
        while len(results) < batch_size and (time.time() - start) < max_time:
            res = self.acquire_once()
            if res:
                results.append(res)
        return results

    # ------------------------------------------------------------------
    # Built-in fetchers (로컬 안전 소스)
    # ------------------------------------------------------------------
    def register_file_sampler(self, pattern: str, limit_bytes: int = 2048) -> None:
        """
        pattern 예시: 'outputs/*.json' 또는 'logs/**/*.log'
        """

        def _fetch() -> AcquisitionResult:
            matches = glob.glob(pattern)
            if not matches:
                raise FileNotFoundError(f"No files for pattern {pattern}")
            path = Path(random.choice(matches))
            data: Any
            if path.suffix.lower() == ".json":
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    data = path.read_text(encoding="utf-8")[:limit_bytes]
            else:
                data = path.read_text(encoding="utf-8")[:limit_bytes]
            meta = {"file": str(path), "size": path.stat().st_size, "pattern": pattern}
            return AcquisitionResult(source="file_sampler", payload=data, meta=meta)

        self.register_source(_fetch)

    def register_recent_log_tail(self, log_dir: Path, suffix: str = ".log", tail_bytes: int = 2048) -> None:
        """
        가장 최근 수정된 로그 파일에서 tail을 읽는다.
        """
        log_dir = log_dir.expanduser()

        def _fetch() -> AcquisitionResult:
            candidates = sorted(log_dir.glob(f"**/*{suffix}"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not candidates:
                raise FileNotFoundError(f"No logs in {log_dir}")
            path = candidates[0]
            data = path.read_bytes()[-tail_bytes:].decode(errors="replace")
            meta = {"log": str(path), "tail_bytes": tail_bytes}
            return AcquisitionResult(source="log_tail", payload=data, meta=meta)

        self.register_source(_fetch)

    # ------------------------------------------------------------------
    # Lua conversation sampler (로컬 파일 기반 감응 입력)
    # ------------------------------------------------------------------
    def register_lua_conversation_sampler(
        self,
        root_dir: Path,
        pattern: str = "*.md",
        recent_n: int = 10,
        preview_chars: int = 1200,
    ) -> None:
        """
        루아/대화 기록 파일들에서 최근 수정된 파일을 샘플링한다.
        - 외부 네트워크 없이, 워크스페이스 내부 파일만 사용한다.
        - 결과는 meta에 파일/mtime/키워드(간단 감응)를 포함한다.
        """
        root_dir = root_dir.expanduser()

        patterns = [
            "프렉탈", "접힘", "펼침", "공명", "리듬", "비선형",
            "의식", "무의식", "배경자아", "차원", "확장", "수축",
            "감응", "대칭", "비대칭", "패턴", "위상", "경계",
            "Self-Acquisition", "Self-Compression", "Self-Tooling",
            "heartbeat", "sync", "bridge", "trigger",
        ]

        def extract_key_concepts(text: str) -> list[str]:
            found: list[str] = []
            for p in patterns:
                if p.lower() in text.lower():
                    found.append(p)
            return found

        def _fetch() -> AcquisitionResult:
            candidates = sorted(root_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
            if not candidates:
                raise FileNotFoundError(f"No lua conversation files in {root_dir}")
            pick = random.choice(candidates[: max(1, recent_n)])
            content = pick.read_text(encoding="utf-8", errors="replace")
            preview = content[:preview_chars]
            meta = {
                "file": str(pick),
                "mtime": pick.stat().st_mtime,
                "size": pick.stat().st_size,
                "concepts": extract_key_concepts(preview)[:20],
                "pattern": pattern,
                "recent_n": recent_n,
            }
            payload = {"preview": preview}
            return AcquisitionResult(source="lua_conversation", payload=payload, meta=meta)

        self.register_source(_fetch)
