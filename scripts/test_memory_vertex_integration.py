import sys
import os
from pathlib import Path
from workspace_root import get_workspace_root

# Add paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(get_workspace_root()))

from unified_memory_system import UnifiedMemorySystem
from vertex_ai_smart_router import VertexAISmartRouter

def test_memory_vertex_integration():
    print("🧠 Testing Memory + Vertex AI Integration...")
    
    # 1. Initialize Systems
    try:
        memory = UnifiedMemorySystem()
        print("✅ UnifiedMemorySystem initialized")
        
        router = VertexAISmartRouter(project_id="naeda-genesis", location="global")
        print("✅ VertexAISmartRouter initialized")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return

    # 2. Add some dummy memories if empty (to ensure retrieval works)
    print("\n📥 Injecting dummy memories...")
    memory.add_memory("user", "What is the philosophical meaning of rhythm in AGI?")
    memory.add_memory("ai", "Rhythm is the phase transition at the critical point of compression and reflection.")
    
    # 3. Test Retrieval
    query = "Explain the critical point in rhythm AGI"
    print(f"\n🔍 Recalling context for: '{query}'")
    
    retrieval = memory.recall(query)
    context = retrieval.get("context_str", "")
    print(f"📄 Context found: {len(context)} chars")
    print(f"---\n{context}\n---")
    
    # 4. Generate Response with Vertex AI
    print("\n🤖 Generating response with Vertex AI (Gemini 3 Pro)...")
    
    full_prompt = f"""
    [Context]
    {context}
    
    [Query]
    {query}
    """
    
    try:
        # Use 'smart' model (Gemini 3 Pro) for reasoning
        response = router.generate(full_prompt, task_hint="philosophy")
        print("\n✨ Vertex AI Response:")
        print(response)
        print("\n✅ Integration Test SUCCESS!")
    except Exception as e:
        print(f"\n❌ Vertex AI Generation failed: {e}")

if __name__ == "__main__":
    test_memory_vertex_integration()
