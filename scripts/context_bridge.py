#!/usr/bin/env python3
"""
Context Persistence Bridge - Core Storage
Phase 4.1: Unified context storage across all AGI layers

Purpose: Enable autonomous AGI operation by maintaining shared context
Goal: Reduce user intervention from 90% to 10%
"""

import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

# Drop ASCII control characters that frequently corrupt the JSONL log
CONTROL_CHAR_FILTER = {i: None for i in range(32) if i not in (9, 10, 13)}
logger = logging.getLogger("ContextBridge")


@dataclass
class Context:
    """A single context entry"""
    id: str
    timestamp: str
    layer: str  # Shion, Core, rhythm, flow, etc.
    speaker: str  # Binoche_Observer, system, etc.
    content: str
    tags: List[str]
    importance: float  # 0.0 - 1.0
    related_contexts: List[str]
    metadata: Dict[str, Any]
    
    @classmethod
    def create(cls, layer: str, speaker: str, content: str, 
               tags: List[str] = None, importance: float = 0.5,
               metadata: Dict[str, Any] = None):
        """Factory method to create a new Context"""
        now = datetime.now(timezone.utc)
        timestamp = now.isoformat()
        
        # Generate ID from timestamp + content hash
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        ctx_id = f"ctx_{now.strftime('%Y%m%d_%H%M%S')}_{content_hash}"
        
        return cls(
            id=ctx_id,
            timestamp=timestamp,
            layer=layer,
            speaker=speaker,
            content=content,
            tags=tags or [],
            importance=importance,
            related_contexts=[],
            metadata=metadata or {}
        )


class ContextBridge:
    """
    Unified Context Storage and Retrieval System
    
    This is the foundation that allows all AGI layers to share context,
    reducing the need for manual context bridging by the user.
    """
    
    def __init__(self, storage_dir: str = None):
        self.storage_dir = Path(storage_dir or Path.home() / "agi" / "outputs" / "contexts")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.ledger_path = self.storage_dir / "context_ledger.jsonl"
        self.index_path = self.storage_dir / "context_index.json"
        
        # In-memory index for fast lookup
        self.index: Dict[str, Context] = {}
        self._load_index()
    
    def _load_index(self):
        """Load context index from disk"""
        if not self.ledger_path.exists():
            return
        
        print(f"📚 Loading context index from {self.ledger_path}")
        count = 0
        skipped = 0
        
        with open(self.ledger_path, 'r', encoding='utf-8', errors='replace') as f:
            for line_no, line in enumerate(f, 1):
                cleaned = line.translate(CONTROL_CHAR_FILTER).strip()
                if not cleaned:
                    continue
                
                try:
                    data = json.loads(cleaned)
                except json.JSONDecodeError as e:
                    skipped += 1
                    logger.warning("Skipping invalid context line %d: %s", line_no, e)
                    continue
                
                ctx = Context(**data)
                self.index[ctx.id] = ctx
                count += 1
        
        skipped_note = f" (skipped {skipped} corrupt lines)" if skipped else ""
        print(f"✅ Loaded {count} contexts{skipped_note}")
    
    def save(self, context: Context) -> str:
        """
        Save a context to the ledger (append-only)
        Returns: context ID
        """
        # Add to in-memory index
        self.index[context.id] = context
        
        # Append to JSONL ledger
        with open(self.ledger_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(context), ensure_ascii=False) + '\n')
        
        print(f"💾 Saved context: {context.id} [{context.layer}]")
        return context.id
    
    def get(self, context_id: str) -> Optional[Context]:
        """Retrieve a context by ID"""
        return self.index.get(context_id)
    
    def search_by_layer(self, layer: str, limit: int = 10) -> List[Context]:
        """Search contexts by layer"""
        results = [ctx for ctx in self.index.values() if ctx.layer == layer]
        # Sort by timestamp (most recent first)
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:limit]
    
    def search_by_tags(self, tags: List[str], limit: int = 10) -> List[Context]:
        """Search contexts by tags"""
        results = []
        for ctx in self.index.values():
            if any(tag in ctx.tags for tag in tags):
                results.append(ctx)
        
        # Sort by importance × recency
        results.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
        return results[:limit]
    
    def search_by_content(self, query: str, limit: int = 10) -> List[Context]:
        """Simple keyword search (will be replaced with embedding search)"""
        query_lower = query.lower()
        results = []
        
        for ctx in self.index.values():
            if query_lower in ctx.content.lower():
                results.append(ctx)
        
        # Sort by importance
        results.sort(key=lambda x: x.importance, reverse=True)
        return results[:limit]
    
    def link_contexts(self, ctx_id1: str, ctx_id2: str):
        """Create a bidirectional link between two contexts"""
        ctx1 = self.get(ctx_id1)
        ctx2 = self.get(ctx_id2)
        
        if not ctx1 or not ctx2:
            print(f"⚠️ Cannot link: context not found")
            return
        
        if ctx_id2 not in ctx1.related_contexts:
            ctx1.related_contexts.append(ctx_id2)
        
        if ctx_id1 not in ctx2.related_contexts:
            ctx2.related_contexts.append(ctx_id1)
        
        # Update ledger (append updated versions)
        self.save(ctx1)
        self.save(ctx2)
        
        print(f"🔗 Linked: {ctx_id1} <-> {ctx_id2}")
    
    def get_context_chain(self, context_id: str, max_depth: int = 3) -> List[Context]:
        """
        Get a chain of related contexts (BFS traversal)
        This recreates the "conversation thread" automatically
        """
        visited = set()
        queue = [(context_id, 0)]
        chain = []
        
        while queue:
            ctx_id, depth = queue.pop(0)
            
            if ctx_id in visited or depth > max_depth:
                continue
            
            visited.add(ctx_id)
            ctx = self.get(ctx_id)
            
            if ctx:
                chain.append(ctx)
                for related_id in ctx.related_contexts:
                    if related_id not in visited:
                        queue.append((related_id, depth + 1))
        
        return chain
    
    def recent(self, layer: str = None, limit: int = 20) -> List[Context]:
        """Get recent contexts, optionally filtered by layer"""
        contexts = list(self.index.values())
        
        if layer:
            contexts = [ctx for ctx in contexts if ctx.layer == layer]
        
        contexts.sort(key=lambda x: x.timestamp, reverse=True)
        return contexts[:limit]
    
    def stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        layer_counts = {}
        for ctx in self.index.values():
            layer_counts[ctx.layer] = layer_counts.get(ctx.layer, 0) + 1
        
        return {
            "total_contexts": len(self.index),
            "layers": layer_counts,
            "storage_path": str(self.ledger_path),
            "storage_size_mb": self.ledger_path.stat().st_size / 1024 / 1024 if self.ledger_path.exists() else 0
        }


def main():
    """Test the Context Bridge"""
    bridge = ContextBridge()
    
    print("\n📊 Context Bridge Statistics:")
    stats = bridge.stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # Example: Save a new context
    ctx = Context.create(
        layer="Shion",
        speaker="Binoche_Observer",
        content="Alpha Background Self는 배경자아가 의식과 무의식 사이를 전환하는 시스템이다.",
        tags=["alpha", "background_self", "philosophy"],
        importance=0.9,
        metadata={"session": "phase4_planning"}
    )
    
    bridge.save(ctx)
    
    # Example: Search by tags
    print("\n🔍 Searching by tags ['alpha', 'background_self']:")
    results = bridge.search_by_tags(["alpha", "background_self"], limit=5)
    for r in results:
        print(f"  - [{r.timestamp}] {r.layer}: {r.content[:80]}...")
    
    # Example: Recent contexts
    print("\n📅 Recent contexts:")
    recent = bridge.recent(limit=5)
    for r in recent:
        print(f"  - [{r.layer}] {r.speaker}: {r.content[:60]}...")


if __name__ == "__main__":
    main()
