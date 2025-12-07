import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

def imprint_memory(persona: str, essence: str, axioms: list, concepts: list, source: str = "manual_imprint"):
    """
    Imprints a core truth into the long-term memory (conversation_history_invariants.json).
    """
    memory_path = Path("fdo_agi_repo/memory/conversation_history_invariants.json")
    
    # Load existing memory
    if memory_path.exists():
        try:
            with open(memory_path, "r", encoding="utf-8") as f:
                memory = json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Memory file corrupted. Starting fresh.")
            memory = []
    else:
        memory = []
    
    # Create new entry
    new_entry = {
        "source_file": source,
        "persona": persona,
        "analysis": {
            "essence": essence,
            "axioms": axioms,
            "concepts": concepts,
            "feeling_vector": {
                "energy": 0.8,  # Default high energy for imprinted memories
                "quality": 0.9,
                "valence": 0.9
            }
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # Append and save
    memory.append(new_entry)
    
    with open(memory_path, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Memory Imprinted: {essence[:50]}...")
    print(f"   Persona: {persona}")
    print(f"   Axioms: {len(axioms)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Imprint a core truth into long-term memory.")
    parser.add_argument("--persona", required=True, help="The persona or entity related to this memory")
    parser.add_argument("--essence", required=True, help="The core essence/summary of the truth")
    parser.add_argument("--axioms", nargs="+", required=True, help="List of axioms (truths)")
    parser.add_argument("--concepts", nargs="+", required=True, help="List of related concepts")
    parser.add_argument("--source", default="manual_cli", help="Source of this memory")
    
    args = parser.parse_args()
    
    imprint_memory(args.persona, args.essence, args.axioms, args.concepts, args.source)
