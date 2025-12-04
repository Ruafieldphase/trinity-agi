#!/usr/bin/env python3
"""
Context Embedding Engine
Phase 4.2: Semantic search for Context Bridge

Enables finding contexts by meaning, not just keywords.
Example: "배경자아" will find both "Background Self" and "Alpha" contexts
"""

import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
import json


class ContextEmbedding:
    """
    Semantic embedding and search for contexts
    Uses sentence-transformers for multilingual support
    """
    
    def __init__(self, model_name: str = "paraphrase-multilingual-mpnet-base-v2"):
        """
        Initialize embedding model
        
        Args:
            model_name: HuggingFace model name
                - paraphrase-multilingual-mpnet-base-v2: Korean + English (768 dim)
                - all-minilm-l6-v2: Faster, English only (384 dim)
        """
        self.model_name = model_name
        self.model = None
        self.cache_path = Path.home() / "agi" / "outputs" / "contexts" / "embeddings.npy"
        self.index_path = Path.home() / "agi" / "outputs" / "contexts" / "embedding_index.json"
        
        # Lazy loading - only load when needed
        self._embeddings_cache: Optional[np.ndarray] = None
        self._index_cache: Optional[dict] = None
    
    def _load_model(self):
        """Lazy load the model (only when needed)"""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                print(f"📚 Loading embedding model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                print("✅ Model loaded")
            except ImportError:
                print("⚠️ sentence-transformers not installed")
                print("Run: pip install sentence-transformers --break-system-packages")
                raise
    
    def embed(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text (Korean/English/Mixed)
            
        Returns:
            Embedding vector (768-dim for multilingual model)
        """
        self._load_model()
        return self.model.encode(text, convert_to_numpy=True)
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts (faster than one-by-one)
        
        Args:
            texts: List of texts
            
        Returns:
            Matrix of embeddings (n_texts × embedding_dim)
        """
        self._load_model()
        return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors
        Range: -1 (opposite) to 1 (identical)
        """
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def find_similar(self, query_embedding: np.ndarray, 
                     all_embeddings: np.ndarray, 
                     top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Find most similar embeddings to a query
        
        Args:
            query_embedding: Query vector
            all_embeddings: Matrix of all embeddings
            top_k: Number of results to return
            
        Returns:
            List of (index, similarity_score) tuples, sorted by similarity desc
        """
        # Compute similarities for all vectors at once (vectorized)
        similarities = np.dot(all_embeddings, query_embedding) / (
            np.linalg.norm(all_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get top k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        return [(int(idx), float(similarities[idx])) for idx in top_indices]
    
    def save_embeddings(self, embeddings: np.ndarray, context_ids: List[str]):
        """
        Save embeddings to disk for persistence
        
        Args:
            embeddings: Matrix of embeddings
            context_ids: Corresponding context IDs
        """
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save embeddings as numpy array
        np.save(self.cache_path, embeddings)
        
        # Save index (context_id -> row number)
        index = {ctx_id: i for i, ctx_id in enumerate(context_ids)}
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Saved {len(context_ids)} embeddings to {self.cache_path}")
    
    def load_embeddings(self) -> Tuple[np.ndarray, dict]:
        """
        Load embeddings from disk
        
        Returns:
            (embeddings matrix, {context_id: row_index} dict)
        """
        if not self.cache_path.exists():
            return np.array([]), {}
        
        embeddings = np.load(self.cache_path)
        
        with open(self.index_path, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        print(f"📚 Loaded {len(index)} embeddings from cache")
        return embeddings, index


def demo_semantic_search():
    """
    Demonstrate semantic search capabilities
    """
    print("=" * 60)
    print("🔍 Semantic Search Demo")
    print("=" * 60)
    
    # Sample contexts (Korean + English)
    contexts = [
        "Alpha Background Self는 배경자아가 의식과 무의식 사이를 전환하는 시스템이다",
        "비노체님은 관찰자이자 개입자로서의 역할을 한다",
        "Context Bridge는 레이어 간 맥락을 공유한다",
        "리듬이 틀리면 Alpha가 개입한다",
        "시스템의 면역 체계 역할을 한다"
    ]
    
    try:
        embedder = ContextEmbedding()
        
        print("\n📊 Generating embeddings for sample contexts...")
        embeddings = embedder.embed_batch(contexts)
        print(f"✅ Generated embeddings: {embeddings.shape}")
        
        # Test queries
        queries = [
            "배경자아",
            "immune system",
            "intervention"
        ]
        
        for query in queries:
            print(f"\n🔍 Query: '{query}'")
            query_emb = embedder.embed(query)
            results = embedder.find_similar(query_emb, embeddings, top_k=3)
            
            print("   Top matches:")
            for idx, score in results:
                print(f"   {score:.3f} - {contexts[idx][:60]}...")
    
    except ImportError:
        print("\n⚠️ sentence-transformers not yet installed")
        print("Installation in progress...")


if __name__ == "__main__":
    demo_semantic_search()
