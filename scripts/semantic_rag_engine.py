import os
import json
import logging
import sqlite3
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
import requests
from workspace_root import get_workspace_root

# LangChain components
try:
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    # Fallback for flexibility
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_community.vectorstores import Chroma
        from langchain.schema import Document
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False

logger = logging.getLogger(__name__)

class QdrantRemoteStore:
    def __init__(self, base_url: str, api_key: Optional[str], collection: str, timeout_s: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.collection = collection
        self.timeout_s = timeout_s
        self.headers: Dict[str, str] = {}
        if api_key:
            self.headers["api-key"] = api_key
        self._collection_ready = False
        self._vector_dim: Optional[int] = None

    def _collection_url(self) -> str:
        return f"{self.base_url}/collections/{self.collection}"

    def _points_url(self) -> str:
        return f"{self.base_url}/collections/{self.collection}/points"

    def _search_url(self) -> str:
        return f"{self.base_url}/collections/{self.collection}/points/search"

    def _ensure_collection(self, dim: int) -> bool:
        if self._collection_ready and self._vector_dim == dim:
            return True
        try:
            resp = requests.get(self._collection_url(), headers=self.headers, timeout=self.timeout_s)
            if resp.status_code == 404:
                payload = {"vectors": {"size": dim, "distance": "Cosine"}}
                create = requests.put(self._collection_url(), headers=self.headers, json=payload, timeout=self.timeout_s)
                if not create.ok:
                    logger.warning("Remote vector store create failed: %s", create.text)
                    return False
            elif not resp.ok:
                logger.warning("Remote vector store check failed: %s", resp.text)
                return False
            self._collection_ready = True
            self._vector_dim = dim
            return True
        except Exception as exc:
            logger.warning("Remote vector store unavailable: %s", exc)
            return False

    def upsert(self, ids: List[str], vectors: List[List[float]], payloads: List[Dict[str, Any]]) -> bool:
        if not ids:
            return True
        if not self._ensure_collection(len(vectors[0])):
            return False
        points = []
        for idx, vec, payload in zip(ids, vectors, payloads):
            points.append({"id": idx, "vector": vec, "payload": payload})
        try:
            resp = requests.put(
                f"{self._points_url()}?wait=true",
                headers=self.headers,
                json={"points": points},
                timeout=self.timeout_s,
            )
            if not resp.ok:
                logger.warning("Remote vector upsert failed: %s", resp.text)
                return False
            return True
        except Exception as exc:
            logger.warning("Remote vector upsert error: %s", exc)
            return False

    def search(self, vector: List[float], top_k: int) -> List[Dict[str, Any]]:
        if not self._ensure_collection(len(vector)):
            return []
        payload = {"vector": vector, "limit": top_k, "with_payload": True}
        try:
            resp = requests.post(self._search_url(), headers=self.headers, json=payload, timeout=self.timeout_s)
            if not resp.ok:
                logger.warning("Remote vector search failed: %s", resp.text)
                return []
            data = resp.json()
            results = []
            for item in data.get("result") or []:
                payload = item.get("payload") or {}
                payload_copy = dict(payload)
                content = payload_copy.pop("content", None) or payload_copy.get("text")
                score = float(item.get("score", 0.0))
                distance = 1.0 - score if 0.0 <= score <= 1.0 else score
                results.append(
                    {
                        "content": content,
                        "metadata": payload_copy,
                        "score": distance,
                        "remote_provider": "qdrant",
                    }
                )
            return results
        except Exception as exc:
            logger.warning("Remote vector search error: %s", exc)
            return []

class SemanticRAGEngine:
    """
    Semantic RAG Engine using LangChain and ChromaDB.
    Provides vector-based search and indexing.
    """
    
    def __init__(self, workspace_root: Path, collection_name: str = "agi_memory"):
        self.workspace_root = workspace_root
        self.vector_store_path = self._select_vector_store_path(workspace_root)
        self.collection_name = collection_name
        self.embeddings = None
        self.vector_store = None
        self.remote_store = self._init_remote_store()
        self.remote_write_enabled = self._bool_env("AGI_REMOTE_VECTOR_WRITE", default=True)
        self.remote_read_enabled = self._bool_env("AGI_REMOTE_VECTOR_READ", default=True)
        
        if not LANGCHAIN_AVAILABLE:
            logger.error("LangChain or required libraries not available.")
            return

        try:
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
            # Initialize embeddings - Use a lightweight model for local execution
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu', 'local_files_only': True}
            )
            
            # Initialize Chroma vector store
            try:
                self.vector_store = self._init_vector_store(self.vector_store_path)
                logger.info(f"SemanticRAGEngine initialized. Collection: {collection_name}")
            except Exception as init_error:
                if self._should_fallback(init_error):
                    fallback_path = self.vector_store_path.parent / "vector_store_fallback"
                    logger.warning("Vector store init failed; trying fallback at %s", fallback_path)
                    self.vector_store_path = fallback_path
                    self.vector_store = self._init_vector_store(self.vector_store_path)
                else:
                    raise
        except Exception as e:
            logger.error(f"Failed to initialize SemanticRAGEngine: {e}")

    def _init_vector_store(self, store_path: Path) -> Chroma:
        store_path.mkdir(parents=True, exist_ok=True)
        self._cleanup_stale_journal(store_path)
        return Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(store_path)
        )

    def _cleanup_stale_journal(self, store_path: Optional[Path] = None) -> None:
        base_path = store_path or self.vector_store_path
        journal_path = base_path / "chroma.sqlite3-journal"
        if not journal_path.exists():
            return
        stale_path = base_path / "chroma.sqlite3-journal.stale"
        if stale_path.exists():
            stale_path = base_path / "chroma.sqlite3-journal.stale.1"
        try:
            journal_path.rename(stale_path)
            logger.warning("Detected stale Chroma journal. Renamed to %s", stale_path.name)
        except Exception as exc:
            logger.warning("Failed to rename stale journal: %s", exc)

    def _should_fallback(self, error: Exception) -> bool:
        message = str(error).lower()
        return "disk i/o" in message or "access is denied" in message or "database is locked" in message

    def _select_vector_store_path(self, workspace_root: Path) -> Path:
        env_path = os.environ.get("AGI_VECTOR_STORE_DIR")
        if env_path:
            return Path(env_path)
        default_path = workspace_root / "fdo_agi_repo" / "memory" / "vector_store"
        if self._can_write_sqlite(default_path):
            return default_path
        return Path.home() / ".cache" / "chroma" / "agi_memory"

    def _can_write_sqlite(self, dir_path: Path) -> bool:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            test_path = dir_path / ".sqlite_write_test.sqlite3"
            conn = sqlite3.connect(test_path)
            conn.execute("CREATE TABLE IF NOT EXISTS test_io (id INTEGER PRIMARY KEY, val TEXT)")
            conn.commit()
            conn.close()
            test_path.unlink(missing_ok=True)
            return True
        except Exception:
            return False

    def _bool_env(self, key: str, default: bool = False) -> bool:
        value = os.environ.get(key)
        if value is None:
            return default
        return value.strip().lower() in ("1", "true", "yes", "on")

    def _init_remote_store(self) -> Optional[QdrantRemoteStore]:
        provider = os.environ.get("AGI_REMOTE_VECTOR_PROVIDER", "").strip().lower()
        if not provider:
            return None
        if provider != "qdrant":
            logger.warning("Unknown remote vector provider: %s", provider)
            return None
        base_url = os.environ.get("AGI_REMOTE_VECTOR_URL") or os.environ.get("QDRANT_URL")
        if not base_url:
            logger.warning("Remote vector provider set but no URL configured.")
            return None
        api_key = os.environ.get("AGI_REMOTE_VECTOR_API_KEY") or os.environ.get("QDRANT_API_KEY")
        collection = os.environ.get("AGI_REMOTE_VECTOR_COLLECTION") or self.collection_name
        timeout_s = float(os.environ.get("AGI_REMOTE_VECTOR_TIMEOUT", "10"))
        return QdrantRemoteStore(base_url, api_key, collection, timeout_s)

    def _stable_id(self, text: str, metadata: Dict[str, Any]) -> str:
        meta_json = json.dumps(metadata, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha1(f"{text}\n{meta_json}".encode("utf-8")).hexdigest()
        return digest

    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add items to the vector store.
        Expected format: list of dicts with 'text' and optional 'metadata'.
        """
        if not self.vector_store and not self.remote_store:
            return
            
        langchain_docs = []
        for doc in documents:
            text = doc.get("text") or doc.get("content") or json.dumps(doc, ensure_ascii=False)
            metadata = doc.get("metadata") or {}
            
            # Ensure metadata doesn't contain complex types (Chroma restriction)
            clean_metadata = {}
            for k, v in metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_metadata[k] = v
                else:
                    clean_metadata[k] = str(v)
            
            # Add essential info to metadata if missing
            if "source" not in clean_metadata and "type" in doc:
                clean_metadata["source"] = doc["type"]
            
            langchain_docs.append(Document(page_content=text, metadata=clean_metadata))
            
        if langchain_docs and self.vector_store:
            self.vector_store.add_documents(langchain_docs)
            # No need for manual persist() in recent versions, but safe to have if the API exists
            if hasattr(self.vector_store, 'persist'):
                self.vector_store.persist()
            logger.info(f"Added {len(langchain_docs)} documents to vector store.")
        if langchain_docs and self.remote_store and self.remote_write_enabled and self.embeddings:
            try:
                texts = [doc.page_content for doc in langchain_docs]
                vectors = self.embeddings.embed_documents(texts)
                payloads: List[Dict[str, Any]] = []
                ids: List[str] = []
                for doc in langchain_docs:
                    payload = dict(doc.metadata)
                    payload["content"] = doc.page_content
                    payloads.append(payload)
                    ids.append(self._stable_id(doc.page_content, doc.metadata))
                self.remote_store.upsert(ids, vectors, payloads)
                logger.info("Mirrored %s documents to remote vector store.", len(langchain_docs))
            except Exception as exc:
                logger.warning("Remote vector mirror failed: %s", exc)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic similarity search.
        """
        if not self.vector_store and not self.remote_store:
            logger.warning("Vector store not initialized. Cannot search.")
            return []
            
        try:
            formatted_results = []
            if self.vector_store:
                results = self.vector_store.similarity_search_with_score(query, k=top_k)
                for doc, score in results:
                    formatted_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": float(score) # Distance score (lower is better in Chroma)
                    })
            if self.remote_store and self.remote_read_enabled and self.embeddings:
                query_vector = self.embeddings.embed_query(query)
                remote_results = self.remote_store.search(query_vector, top_k=top_k)
                formatted_results.extend(remote_results)
            return formatted_results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

if __name__ == "__main__":
    # Quick Test
    logging.basicConfig(level=logging.INFO)
    import sys
    sys.path.insert(0, str(get_workspace_root()))
    sys.path.insert(0, str(get_workspace_root() / "fdo_agi_repo"))
    root = get_workspace_root()
    engine = SemanticRAGEngine(root)
    
    if engine.vector_store:
        test_docs = [
            {"text": "Shion이는 AGI 시스템의 페르소나 중 하나입니다.", "metadata": {"category": "persona"}},
            {"text": "LangChain은 LLM 오케스트레이션 프레임워크입니다.", "metadata": {"category": "technology"}}
        ]
        engine.add_documents(test_docs)
        
        results = engine.search("Shion이가 누구야?")
        print(f"\nSearch results for 'Shion이가 누구야?':")
        for r in results:
            print(f"- {r['content']} (Score: {r['score']})")
