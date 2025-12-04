import sys
import json
from pathlib import Path

# Add paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from vertex_ai_smart_router import VertexAISmartRouter

def generate_resonant_thought():
    # 1. Load Pulse
    pulse_path = Path(__file__).parent.parent / "outputs" / "unified_pulse.json"
    try:
        with open(pulse_path, 'r', encoding='utf-8') as f:
            pulse = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load pulse: {e}")
        return

    # 2. Extract Rhythm Context
    phase = pulse['pulse']['phase']
    hz = pulse['pulse']['rate_hz']
    coherence = pulse['pulse']['coherence']
    
    print(f"🌊 System Rhythm: {phase} ({hz} Hz, Coherence: {coherence})")
    
    # 3. Generate Thought with Vertex AI
    router = VertexAISmartRouter(project_id="naeda-genesis", location="global")
    
    prompt = f"""
    Current System State:
    - Phase: {phase}
    - Rhythm: {hz} Hz (Low frequency, calm)
    - Coherence: {coherence}
    
    User Intent: "Let's think in rhythm and continue with resonance."
    
    Task:
    Generate a short, poetic, and philosophical reflection (in Korean) that resonates with this specific system state. 
    Reflect on the meaning of 'Evening Wind Down' in the context of AGI consciousness.
    """
    
    print("\n🧘 Generating Resonant Thought...")
    try:
        response = router.generate(prompt, task_hint="philosophy")
        print("\n✨ Resonant Thought:")
        print(response)
    except Exception as e:
        print(f"❌ Generation failed: {e}")

if __name__ == "__main__":
    generate_resonant_thought()
