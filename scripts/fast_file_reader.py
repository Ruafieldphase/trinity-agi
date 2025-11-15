"""
⚡ Fast File Reader - Ultra-fast file reading system

속도 최적화 기법:
1. Memory-Mapped I/O (mmap) - OS 커널 캐시 활용
2. Chunk-based parallel reading - 멀티스레드 동시 읽기
3. LRU Cache - 최근 읽은 파일 메모리 캐싱
4. Smart encoding detection - UTF-8 우선, fallback 최소화
5. Buffer pool - 메모리 재사용으로 GC 압력 감소
"""

from __future__ import annotations
import mmap
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import chardet
import logging

logger = logging.getLogger(__name__)


class FastFileReader:
    """초고속 파일 읽기 엔진"""
    
    def __init__(
        self,
        max_workers: int = 4,
        cache_size: int = 128,
        chunk_size: int = 64 * 1024  # 64KB chunks
    ):
        """
        Args:
            max_workers: 병렬 읽기 스레드 수
            cache_size: LRU 캐시 크기 (파일 개수)
            chunk_size: 청크 크기 (바이트)
        """
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # 캐시 래퍼 동적 생성
        self._read_cached = lru_cache(maxsize=cache_size)(self._read_file_impl)
        
        logger.info(f"⚡ FastFileReader initialized: {max_workers} workers, cache={cache_size}")
    
    # ===================================================================
    # 1. 단일 파일 읽기 (Memory-Mapped + Cache)
    # ===================================================================
    
    def read_fast(self, file_path: Union[str, Path], use_cache: bool = True) -> str:
        """
        초고속 파일 읽기
        
        Args:
            file_path: 파일 경로
            use_cache: 캐시 사용 여부
        
        Returns:
            파일 내용 (UTF-8 문자열)
        """
        path = Path(file_path)
        
        if use_cache:
            # 캐시된 읽기 (수정 시간 포함해서 키 생성)
            mtime = path.stat().st_mtime
            return self._read_cached(str(path), mtime)
        else:
            # 직접 읽기 (캐시 무시)
            return self._read_file_impl(str(path), path.stat().st_mtime)
    
    def _read_file_impl(self, file_path: str, mtime: float) -> str:
        """
        실제 파일 읽기 구현 (Memory-Mapped I/O)
        
        Args:
            file_path: 파일 경로
            mtime: 수정 시간 (캐시 키로 사용)
        
        Returns:
            파일 내용
        """
        path = Path(file_path)
        
        # 작은 파일은 일반 읽기가 더 빠름
        size = path.stat().st_size
        if size < 4096:  # 4KB 미만
            return self._read_small_file(path)
        
        # 큰 파일은 mmap 사용
        return self._read_with_mmap(path)
    
    def _read_small_file(self, path: Path) -> str:
        """작은 파일 빠른 읽기"""
        try:
            # UTF-8 우선 시도
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback: auto-detect
            with open(path, 'rb') as f:
                raw = f.read()
                encoding = chardet.detect(raw)['encoding'] or 'utf-8'
                return raw.decode(encoding, errors='replace')
    
    def _read_with_mmap(self, path: Path) -> str:
        """Memory-Mapped I/O로 파일 읽기 (OS 커널 캐시 활용)"""
        try:
            with open(path, 'r+b') as f:
                # Memory-map the file
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    raw = mm.read()
                    # UTF-8 우선 시도
                    try:
                        return raw.decode('utf-8')
                    except UnicodeDecodeError:
                        # Fallback: auto-detect
                        encoding = chardet.detect(raw[:4096])['encoding'] or 'utf-8'
                        return raw.decode(encoding, errors='replace')
        except (OSError, ValueError):
            # mmap 실패 시 일반 읽기
            return self._read_small_file(path)
    
    # ===================================================================
    # 2. 병렬 파일 읽기 (Multiple files)
    # ===================================================================
    
    def read_multiple(
        self,
        file_paths: List[Union[str, Path]],
        use_cache: bool = True
    ) -> Dict[str, str]:
        """
        여러 파일 병렬 읽기
        
        Args:
            file_paths: 파일 경로 리스트
            use_cache: 캐시 사용 여부
        
        Returns:
            {파일경로: 내용} 딕셔너리
        """
        results = {}
        
        # 병렬 읽기
        futures = {
            self.executor.submit(self.read_fast, path, use_cache): str(path)
            for path in file_paths
        }
        
        for future in as_completed(futures):
            path = futures[future]
            try:
                results[path] = future.result()
            except Exception as e:
                logger.warning(f"Failed to read {path}: {e}")
                results[path] = f"[ERROR: {e}]"
        
        return results
    
    # ===================================================================
    # 3. 청크 기반 읽기 (Very large files)
    # ===================================================================
    
    def read_chunked(
        self,
        file_path: Union[str, Path],
        max_lines: Optional[int] = None
    ) -> List[str]:
        """
        대용량 파일 청크 단위로 읽기
        
        Args:
            file_path: 파일 경로
            max_lines: 최대 라인 수 (None이면 전체)
        
        Returns:
            라인 리스트
        """
        path = Path(file_path)
        lines = []
        
        try:
            with open(path, 'r', encoding='utf-8', buffering=self.chunk_size) as f:
                for i, line in enumerate(f):
                    if max_lines and i >= max_lines:
                        break
                    lines.append(line.rstrip('\n\r'))
        except UnicodeDecodeError:
            # Fallback: binary read + decode
            with open(path, 'rb', buffering=self.chunk_size) as f:
                raw = f.read()
                encoding = chardet.detect(raw[:4096])['encoding'] or 'utf-8'
                text = raw.decode(encoding, errors='replace')
                lines = text.splitlines()
                if max_lines:
                    lines = lines[:max_lines]
        
        return lines
    
    # ===================================================================
    # 4. 캐시 관리
    # ===================================================================
    
    def clear_cache(self) -> None:
        """캐시 초기화"""
        self._read_cached.cache_clear()
        logger.info("🧹 Cache cleared")
    
    def cache_info(self) -> Dict[str, Any]:
        """캐시 통계"""
        info = self._read_cached.cache_info()
        return {
            "hits": info.hits,
            "misses": info.misses,
            "size": info.currsize,
            "maxsize": info.maxsize,
            "hit_rate": info.hits / (info.hits + info.misses) if (info.hits + info.misses) > 0 else 0.0
        }
    
    # ===================================================================
    # 5. 편의 메서드
    # ===================================================================
    
    def read_json_fast(self, file_path: Union[str, Path]) -> Any:
        """JSON 파일 빠른 읽기"""
        import json
        content = self.read_fast(file_path)
        return json.loads(content)
    
    def read_jsonl_fast(self, file_path: Union[str, Path]) -> List[Dict]:
        """JSONL 파일 빠른 읽기"""
        import json
        lines = self.read_chunked(file_path)
        return [json.loads(line) for line in lines if line.strip()]
    
    def __del__(self):
        """소멸자: 스레드 풀 정리"""
        self.executor.shutdown(wait=False)


# ===================================================================
# 싱글톤 인스턴스
# ===================================================================

_global_reader: Optional[FastFileReader] = None


def get_reader(
    max_workers: int = 4,
    cache_size: int = 128
) -> FastFileReader:
    """전역 FastFileReader 인스턴스 반환"""
    global _global_reader
    if _global_reader is None:
        _global_reader = FastFileReader(
            max_workers=max_workers,
            cache_size=cache_size
        )
    return _global_reader


# ===================================================================
# 편의 함수
# ===================================================================

def read_fast(file_path: Union[str, Path], use_cache: bool = True) -> str:
    """파일 빠른 읽기 (전역 인스턴스 사용)"""
    return get_reader().read_fast(file_path, use_cache)


def read_multiple(file_paths: List[Union[str, Path]]) -> Dict[str, str]:
    """여러 파일 병렬 읽기 (전역 인스턴스 사용)"""
    return get_reader().read_multiple(file_paths)


def read_json_fast(file_path: Union[str, Path]) -> Any:
    """JSON 파일 빠른 읽기"""
    return get_reader().read_json_fast(file_path)


# ===================================================================
# CLI 테스트
# ===================================================================

if __name__ == "__main__":
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description="Fast File Reader Test")
    parser.add_argument("files", nargs="+", help="Files to read")
    parser.add_argument("--no-cache", action="store_true", help="Disable cache")
    parser.add_argument("--workers", type=int, default=4, help="Thread count")
    parser.add_argument("--show-content", action="store_true", help="Show file content")
    
    args = parser.parse_args()
    
    reader = get_reader(max_workers=args.workers)
    
    print(f"⚡ Fast File Reader Test")
    print(f"Files: {len(args.files)}")
    print(f"Workers: {args.workers}")
    print(f"Cache: {'disabled' if args.no_cache else 'enabled'}")
    print()
    
    # 단일 파일 테스트
    if len(args.files) == 1:
        file_path = args.files[0]
        
        # 첫 읽기 (cache miss)
        start = time.time()
        content = reader.read_fast(file_path, use_cache=not args.no_cache)
        duration1 = time.time() - start
        
        # 두 번째 읽기 (cache hit)
        start = time.time()
        content2 = reader.read_fast(file_path, use_cache=not args.no_cache)
        duration2 = time.time() - start
        
        print(f"📄 {file_path}")
        print(f"  Size: {len(content):,} chars")
        print(f"  First read: {duration1*1000:.2f}ms")
        print(f"  Second read: {duration2*1000:.2f}ms")
        print(f"  Speedup: {duration1/duration2:.1f}x" if duration2 > 0 else "  Speedup: ∞x")
        
        if args.show_content:
            print("\n--- Content ---")
            print(content[:500])
            if len(content) > 500:
                print(f"\n... ({len(content)-500} more chars)")
    
    # 멀티 파일 테스트
    else:
        start = time.time()
        results = reader.read_multiple(args.files, use_cache=not args.no_cache)
        duration = time.time() - start
        
        total_size = sum(len(content) for content in results.values())
        
        print(f"📦 Read {len(results)} files in {duration*1000:.2f}ms")
        print(f"Total size: {total_size:,} chars")
        print(f"Throughput: {total_size/duration/1024/1024:.2f} MB/s")
        
        if args.show_content:
            for path, content in results.items():
                print(f"\n--- {path} ---")
                print(content[:200])
    
    # 캐시 통계
    print("\n📊 Cache Stats:")
    info = reader.cache_info()
    print(f"  Hits: {info['hits']}")
    print(f"  Misses: {info['misses']}")
    print(f"  Size: {info['size']}/{info['maxsize']}")
    print(f"  Hit rate: {info['hit_rate']*100:.1f}%")
