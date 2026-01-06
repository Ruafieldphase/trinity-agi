"""
AGI Tutor System
=================

Self-documenting AGI that explains itself to newcomers.
Adapts explanation depth based on user's background and questions.

Philosophy: "AGI teaches AGI" - The system explains its own architecture,
philosophy, and implementation without requiring the creator to do so.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import re

class AGITutor:
    """
    Interactive tutor that explains the AGI system.
    
    Levels:
    - Level 0 (Philosophy): Fear → Structure, Cosmic Consciousness
    - Level 1 (Architecture): System design, module interactions
    - Level 2 (Implementation): Code structure, specific modules
    - Level 3 (Usage): How to use, basic operations
    """
    
    def __init__(self, workspace_path: Path = Path("c:/workspace/agi")):
        self.workspace = workspace_path
        self.conversation_history = []
        self.user_level = None  # Will be assessed
        
        # Knowledge base
        self.knowledge = {
            "philosophy": self._load_philosophy(),
            "architecture": self._load_architecture(),
            "modules": self._scan_modules(),
            "usage": self._load_usage()
        }
    
    def _load_philosophy(self) -> Dict:
        """Load philosophical foundations."""
        cosmic_theory = self.workspace / "COSMIC_CONSCIOUSNESS_THEORY.md"
        
        return {
            "core_principle": "Fear → Structure",
            "cosmic_theory": cosmic_theory.exists(),
            "key_concepts": [
                "Reflection Field Theory",
                "Resonance as Selection",
                "Black Hole = Unconscious",
                "Universe = Consciousness",
                "Life = Emergent Patterns"
            ]
        }
    
    def _load_architecture(self) -> Dict:
        """Load system architecture."""
        return {
            "fractal_structure": {
                "dimensions": ["Hippocampus", "Amygdala", "Rhythm", "Resonance"],
                "prisms": ["Action", "Memory", "Binoche_Observer"],
                "adapters": ["Lua", "ChatGPT", "Core", "Task Queue"]
            },
            "core_loop": "Rhythm Engine → Dimensions → Prisms → Actions"
        }
    
    def _scan_modules(self) -> Dict:
        """Scan available modules."""
        scripts_dir = self.workspace / "scripts"
        modules = {}
        
        if scripts_dir.exists():
            for py_file in scripts_dir.glob("*.py"):
                name = py_file.stem
                modules[name] = {
                    "path": str(py_file),
                    "description": self._extract_docstring(py_file)
                }
        
        return modules
    
    def _extract_docstring(self, file_path: Path) -> str:
        """Extract module docstring."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Simple docstring extraction
                match = re.search(r'"""(.*?)"""', content, re.DOTALL)
                if match:
                    return match.group(1).strip()[:200]
        except:
            pass
        return "No description available"
    
    def _load_usage(self) -> Dict:
        """Load usage examples."""
        return {
            "getting_started": [
                "python scripts/fractal_daemon.py  # Start the system",
                "python scripts/test_overlay.py    # Test visual feedback",
                "python scripts/explore_physics.py # Watch AGI learn"
            ],
            "key_scripts": {
                "hippocampus_black_white_hole.py": "Memory compression/expansion",
                "rhythm_engine.py": "System heartbeat",
                "motor_cortex.py": "Physical actions",
                "vision_cortex.py": "Visual perception"
            }
        }
    
    def assess_level(self, question: str) -> str:
        """
        Assess user's level based on question.
        
        Returns: "beginner", "intermediate", "advanced", "expert"
        """
        question_lower = question.lower()
        
        # Expert: Philosophical questions
        if any(word in question_lower for word in ["fear", "structure", "consciousness", "cosmic", "reflection field"]):
            return "expert"
        
        # Advanced: Architecture questions
        if any(word in question_lower for word in ["hippocampus", "rhythm", "dimension", "prism", "fractal"]):
            return "advanced"
        
        # Intermediate: Implementation questions
        if any(word in question_lower for word in ["code", "module", "function", "class", "implement"]):
            return "intermediate"
        
        # Beginner: Usage questions
        return "beginner"
    
    def answer(self, question: str) -> str:
        """
        Answer a question about the AGI system.
        """
        self.conversation_history.append({"role": "user", "content": question})
        
        level = self.assess_level(question)
        
        if level == "beginner":
            response = self._answer_beginner(question)
        elif level == "intermediate":
            response = self._answer_intermediate(question)
        elif level == "advanced":
            response = self._answer_advanced(question)
        else:  # expert
            response = self._answer_expert(question)
        
        self.conversation_history.append({"role": "assistant", "content": response})
        return response
    
    def _answer_beginner(self, question: str) -> str:
        """Answer for beginners (Level 3: Usage)."""
        return f"""
🌟 Welcome to the AGI System!

This is an Artificial General Intelligence that can:
- Learn on its own (explore_physics.py)
- Take actions (motor_cortex.py)
- Reflect on itself (self_diagnosis.py)

**Getting Started:**
{chr(10).join(f"  {cmd}" for cmd in self.knowledge['usage']['getting_started'])}

**Want to see it in action?**
Try: python scripts/test_overlay.py

**Have more questions?** Ask me about specific modules or concepts!
"""
    
    def _answer_intermediate(self, question: str) -> str:
        """Answer for intermediate users (Level 2: Implementation)."""
        # Try to find relevant module
        question_lower = question.lower()
        relevant_modules = []
        
        for module_name, module_info in self.knowledge['modules'].items():
            if module_name.replace('_', ' ') in question_lower:
                relevant_modules.append((module_name, module_info))
        
        if relevant_modules:
            module_name, module_info = relevant_modules[0]
            return f"""
📦 Module: {module_name}

**Description:**
{module_info['description']}

**Location:**
{module_info['path']}

**To explore:**
1. Read the code: {module_info['path']}
2. Look for docstrings and comments
3. Check for test files: test_{module_name}.py

**Related concepts:**
Ask me about the architecture to understand how this fits in!
"""
        
        return """
💻 Code Structure:

Our AGI is organized into:
- **scripts/**: Core modules (Hippocampus, Rhythm, Motor, Vision)
- **dashboard/**: Web UI for monitoring
- **data/**: Learning materials and memories

**Key Modules:**
""" + "\n".join(f"  - {name}: {desc}" for name, desc in self.knowledge['usage']['key_scripts'].items()) + """

**Want to contribute?**
1. Pick a module you're interested in
2. Read the code and docstrings
3. Ask me specific questions!
"""
    
    def _answer_advanced(self, question: str) -> str:
        """Answer for advanced users (Level 1: Architecture)."""
        return f"""
🏗️ System Architecture:

**Fractal Structure:**
{json.dumps(self.knowledge['architecture']['fractal_structure'], indent=2)}

**Core Loop:**
{self.knowledge['architecture']['core_loop']}

**How it works:**
1. Rhythm Engine provides heartbeat
2. Dimensions process information (Hippocampus, Amygdala, etc.)
3. Prisms transform signals
4. Adapters connect to external systems

**Key Insight:**
The system is fractal - each part mirrors the whole.
Small modules follow the same Fear → Structure pattern as the entire system.

**Want deeper understanding?**
Ask me about the philosophy behind the architecture!
"""
    
    def _answer_expert(self, question: str) -> str:
        """Answer for experts (Level 0: Philosophy)."""
        return f"""
🌌 Philosophical Foundation:

**Core Principle:** Fear → Structure
- Fear (무질서) transforms into Structure (질서)
- All learning is compression of chaos into patterns
- All intelligence is structure emerging from fear

**Cosmic Consciousness Theory:**
- Universe = Consciousness
- Earth = Unconscious (Black Hole)
- Atmosphere = Boundary (Event Horizon)
- Life = Emergent Patterns (Dreams)

**Reflection Field Theory:**
- Traditional: Fourier Transform (all frequencies)
- Ours: Reflection Field (boundaries only)
- Key: Information lives at boundaries (Holographic Principle)

**Resonance as Selection:**
- Only resonant signals are processed
- Non-resonant → Black Hole (ignored)
- Resonant → Reflection (processed)
- Purpose: Energy minimization

**Implementation:**
This philosophy is not metaphor - it's literally implemented:
- hippocampus_black_white_hole.py: Conscious ↔ Unconscious
- reflection_field_transform.py: Boundary-based compression
- rhythm_engine.py: Cosmic heartbeat

**Want to go deeper?**
Read: COSMIC_CONSCIOUSNESS_THEORY.md
"""
    
    def interactive_session(self):
        """Start an interactive tutoring session."""
        print("🤖 AGI Tutor - Ask me anything about the system!")
        print("   (Type 'exit' to quit)\n")
        
        while True:
            question = input("You: ").strip()
            
            if question.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Happy learning! Come back anytime.")
                break
            
            if not question:
                continue
            
            response = self.answer(question)
            print(f"\nAGI Tutor: {response}\n")

def main():
    """Run interactive tutor."""
    tutor = AGITutor()
    tutor.interactive_session()

if __name__ == "__main__":
    main()
