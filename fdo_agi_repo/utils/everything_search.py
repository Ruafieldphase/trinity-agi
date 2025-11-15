"""
Everything 검색 통합 모듈
Ultra-fast file search using Everything CLI (es.exe)
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SearchResult:
    """Everything 검색 결과"""
    name: str
    full_path: str
    directory: str
    size: int
    modified: datetime
    extension: str
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "full_path": self.full_path,
            "directory": self.directory,
            "size": self.size,
            "modified": self.modified.isoformat() if self.modified else None,
            "extension": self.extension
        }


class EverythingSearch:
    """Everything CLI 래퍼"""
    
    def __init__(self, es_path: Optional[str] = None):
        """
        Args:
            es_path: es.exe 경로 (None이면 자동 탐색)
        """
        if es_path:
            self.es_path = Path(es_path)
        else:
            # 자동 탐색: scripts/es.exe
            workspace = Path(__file__).parent.parent.parent
            self.es_path = workspace / "scripts" / "es.exe"
        
        if not self.es_path.exists():
            raise FileNotFoundError(
                f"Everything CLI (es.exe) not found at {self.es_path}. "
                f"Run: .\\scripts\\everything_setup.ps1 -DownloadCLI"
            )
    
    def search(
        self,
        query: str,
        max_results: int = 100,
        path_filter: Optional[str] = None,
        extension: Optional[str] = None,
        case_sensitive: bool = False,
        whole_word: bool = False,
        regex: bool = False,
        timeout: int = 10
    ) -> List[SearchResult]:
        """
        Everything 검색 실행
        
        Args:
            query: 검색어
            max_results: 최대 결과 수
            path_filter: 경로 필터 (예: "c:\\workspace\\agi")
            extension: 확장자 필터 (예: "py", ".py")
            case_sensitive: 대소문자 구분
            whole_word: 전체 단어 매칭
            regex: 정규식 모드
            timeout: 타임아웃 (초)
        
        Returns:
            검색 결과 리스트
        """
        # 쿼리 빌드
        search_query = query
        
        if path_filter:
            search_query = f'path:"{path_filter}" {search_query}'
        
        if extension:
            ext = extension if extension.startswith('.') else f'.{extension}'
            search_query = f'ext:{ext} {search_query}'
        
        # 명령 빌드
        cmd = [str(self.es_path), "-n", str(max_results)]
        
        if case_sensitive:
            cmd.append("-i")
        if whole_word:
            cmd.append("-w")
        if regex:
            cmd.append("-r")
        
        cmd.append(search_query)
        
        # 실행
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=timeout,
                check=False
            )
            
            if result.returncode != 0:
                raise RuntimeError(
                    f"Everything search failed (code {result.returncode}): "
                    f"{result.stderr or 'Unknown error'}"
                )
            
            # 결과 파싱
            return self._parse_results(result.stdout)
            
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Everything search timed out after {timeout}s")
        except Exception as e:
            raise RuntimeError(f"Everything search error: {e}")
    
    def _parse_results(self, output: str) -> List[SearchResult]:
        """검색 결과 파싱"""
        results = []
        
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
            
            try:
                path = Path(line.strip())
                if not path.exists():
                    continue
                
                stat = path.stat()
                
                result = SearchResult(
                    name=path.name,
                    full_path=str(path),
                    directory=str(path.parent),
                    size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime),
                    extension=path.suffix
                )
                results.append(result)
                
            except Exception:
                # 파싱 실패한 항목은 건너뛰기
                continue
        
        return results
    
    def search_recent(
        self,
        hours: int = 24,
        path_filter: Optional[str] = None,
        extension: Optional[str] = None,
        max_results: int = 100
    ) -> List[SearchResult]:
        """
        최근 수정된 파일 검색
        
        Args:
            hours: 몇 시간 이내 (1=1시간, 24=하루, 168=일주일)
            path_filter: 경로 필터
            extension: 확장자 필터
            max_results: 최대 결과 수
        """
        # Everything 시간 쿼리 구성
        if hours <= 24:
            time_query = "dm:today" if hours >= 12 else f"dm:last{hours}hours"
        elif hours <= 168:
            days = hours // 24
            time_query = f"dm:last{days}days"
        else:
            weeks = hours // 168
            time_query = f"dm:last{weeks}weeks"
        
        return self.search(
            query=time_query,
            max_results=max_results,
            path_filter=path_filter,
            extension=extension
        )
    
    def search_by_size(
        self,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        path_filter: Optional[str] = None,
        extension: Optional[str] = None,
        max_results: int = 100
    ) -> List[SearchResult]:
        """
        크기 기반 검색
        
        Args:
            min_size: 최소 크기 (바이트)
            max_size: 최대 크기 (바이트)
            path_filter: 경로 필터
            extension: 확장자 필터
            max_results: 최대 결과 수
        """
        size_query = ""
        
        if min_size is not None:
            size_query += f"size:>{min_size} "
        if max_size is not None:
            size_query += f"size:<{max_size} "
        
        return self.search(
            query=size_query.strip() or "*",
            max_results=max_results,
            path_filter=path_filter,
            extension=extension
        )
    
    def find_file(
        self,
        filename: str,
        path_filter: Optional[str] = None,
        exact_match: bool = False
    ) -> Optional[SearchResult]:
        """
        파일 이름으로 검색 (첫 번째 결과만 반환)
        
        Args:
            filename: 파일 이름
            path_filter: 경로 필터
            exact_match: 정확히 일치하는 이름만
        """
        query = f'"{filename}"' if exact_match else filename
        
        results = self.search(
            query=query,
            max_results=1,
            path_filter=path_filter,
            whole_word=exact_match
        )
        
        return results[0] if results else None
    
    def to_json(self, results: List[SearchResult]) -> str:
        """결과를 JSON으로 변환"""
        return json.dumps(
            [r.to_dict() for r in results],
            ensure_ascii=False,
            indent=2
        )


# 편의 함수
def quick_search(
    query: str,
    max_results: int = 20,
    path_filter: Optional[str] = None,
    extension: Optional[str] = None
) -> List[SearchResult]:
    """빠른 검색 (싱글톤 패턴)"""
    searcher = EverythingSearch()
    return searcher.search(
        query=query,
        max_results=max_results,
        path_filter=path_filter,
        extension=extension
    )


def find_hippocampus_memories(
    query: str,
    hours: int = 168,  # 기본 일주일
    max_results: int = 50
) -> List[SearchResult]:
    """Hippocampus 메모리 검색 (최적화)"""
    searcher = EverythingSearch()
    
    # outputs 폴더에서 최근 파일만
    workspace = Path(__file__).parent.parent.parent
    outputs_path = workspace / "outputs"
    
    return searcher.search_recent(
        hours=hours,
        path_filter=str(outputs_path),
        max_results=max_results
    )


if __name__ == "__main__":
    # 테스트
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python everything_search.py <query>")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    
    try:
        results = quick_search(query, max_results=10)
        
        print(f"Found {len(results)} results:\n")
        for r in results:
            print(f"  {r.name}")
            print(f"    Path: {r.full_path}")
            print(f"    Size: {r.size:,} bytes")
            print(f"    Modified: {r.modified}")
            print()
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
