"""
Document Indexer for Hybrid RAG
코드베이스 문서를 크롤링하여 BM25(기존) + Dense Embedding(신규) 인덱싱
"""
from __future__ import annotations
from typing import List, Dict, Any
import os
import json
import glob
import logging
import sys
from pathlib import Path

# 리포지토리 루트를 sys.path에 추가 (모듈 임포트를 위해)
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from tools.rag.embedding_service import get_embedding_service
from tools.rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)

# 인덱싱 대상 파일 확장자
INDEX_EXTENSIONS = [".py", ".md", ".yaml", ".yml", ".json", ".txt"]

# 제외할 디렉토리
EXCLUDE_DIRS = [
    "__pycache__", ".git", ".venv", "venv", "node_modules",
    ".pytest_cache", "htmlcov", ".mypy_cache", "dist", "build",
]


def should_index_file(file_path: str) -> bool:
    """파일 인덱싱 여부 판단"""
    path = Path(file_path)
    
    # 확장자 체크
    if path.suffix not in INDEX_EXTENSIONS:
        return False
    
    # 제외 디렉토리 체크
    for exclude_dir in EXCLUDE_DIRS:
        if exclude_dir in path.parts:
            return False
    
    return True


def extract_text_from_file(file_path: str, max_length: int = 10000) -> str:
    """
    파일에서 텍스트 추출
    - 바이너리 파일은 스킵
    - max_length로 메모리 제한
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read(max_length)
        return content
    except (UnicodeDecodeError, PermissionError):
        logger.debug(f"Skipping binary/protected file: {file_path}")
        return ""


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    """
    긴 텍스트를 청크로 분할 (오버랩 포함)
    - chunk_size: 청크 크기 (문자 단위)
    - overlap: 청크 간 오버랩 (문맥 유지)
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    return chunks


def index_documents(
    repo_root: str,
    vector_store_path: str = "memory/vector_store.json",
    force_rebuild: bool = False,
) -> Dict[str, Any]:
    """
    리포지토리 문서 인덱싱
    Args:
        repo_root: 리포지토리 루트 경로
        vector_store_path: VectorStore 저장 경로 (repo_root 기준 상대 경로)
        force_rebuild: True면 기존 인덱스 무시하고 재구축
    Returns:
        통계 정보 (indexed_files, total_chunks, skipped_files)
    """
    emb_service = get_embedding_service()
    vector_store = get_vector_store(vector_store_path)
    
    if force_rebuild:
        logger.info("Force rebuild enabled, clearing existing vector store")
        vector_store.vectors = vector_store.vectors[:0]  # 빈 배열로 초기화
        vector_store.metadata = []
        vector_store.doc_ids = []
    
    stats = {
        "indexed_files": 0,
        "total_chunks": 0,
        "skipped_files": 0,
        "errors": [],
    }
    
    # 리포지토리 파일 탐색
    logger.info(f"Scanning repository: {repo_root}")
    for root, dirs, files in os.walk(repo_root):
        # 제외 디렉토리 필터링
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file_name in files:
            file_path = os.path.join(root, file_name)
            
            if not should_index_file(file_path):
                continue
            
            # 상대 경로 (메타데이터 저장용)
            rel_path = os.path.relpath(file_path, repo_root)
            
            try:
                text = extract_text_from_file(file_path)
                if not text.strip():
                    stats["skipped_files"] += 1
                    continue
                
                # 텍스트 청킹
                chunks = chunk_text(text, chunk_size=2000, overlap=200)
                
                for i, chunk in enumerate(chunks):
                    # 문서 ID: 파일경로_청크번호
                    doc_id = f"{rel_path}#{i}"
                    
                    # 임베딩 생성
                    embedding = emb_service.embed(chunk)
                    
                    # 메타데이터
                    meta = {
                        "file_path": rel_path,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "text": chunk[:500],  # 500자까지만 저장 (메모리 절약)
                        "source": "codebase",
                        "type": "doc",
                    }
                    
                    # 벡터 저장소에 추가
                    vector_store.add(doc_id, embedding, meta)
                    stats["total_chunks"] += 1
                
                stats["indexed_files"] += 1
                if stats["indexed_files"] % 10 == 0:
                    logger.info(f"Indexed {stats['indexed_files']} files, {stats['total_chunks']} chunks")
            
            except Exception as e:
                logger.error(f"Error indexing {file_path}: {e}")
                stats["errors"].append({"file": rel_path, "error": str(e)})
                stats["skipped_files"] += 1
    
    # 벡터 저장소 저장
    full_store_path = os.path.join(repo_root, vector_store_path)
    vector_store.save(full_store_path)
    
    logger.info(f"Indexing complete: {stats}")
    return stats


if __name__ == "__main__":
    # 스크립트 직접 실행 시: 리포지토리 루트 자동 탐지 및 인덱싱
    import sys
    
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
    
    force = "--force" in sys.argv
    
    print(f"📚 Document Indexer")
    print(f"Repository: {repo_root}")
    print(f"Force rebuild: {force}")
    print()
    
    stats = index_documents(repo_root, force_rebuild=force)
    
    print()
    print(f"✅ Indexing Complete:")
    print(f"  Indexed files: {stats['indexed_files']}")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Skipped files: {stats['skipped_files']}")
    if stats['errors']:
        print(f"  Errors: {len(stats['errors'])}")
        for err in stats['errors'][:5]:
            print(f"    - {err['file']}: {err['error']}")
