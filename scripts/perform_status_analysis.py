import sys
import json
from pathlib import Path

# Add paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from vertex_ai_smart_router import VertexAISmartRouter

def perform_status_analysis():
    # 1. Load Pulse
    pulse_path = Path(__file__).parent.parent / "outputs" / "unified_pulse.json"
    try:
        with open(pulse_path, 'r', encoding='utf-8') as f:
            pulse = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load pulse: {e}")
        return

    # 2. Extract Data
    data = json.dumps(pulse, indent=2, ensure_ascii=False)
    
    # 3. Generate Analysis with Vertex AI
    router = VertexAISmartRouter(project_id="naeda-genesis", location="global")
    
    prompt = f"""
    [System Data]
    {data}
    
    [Task]
    Analyze the current system status based on the provided JSON data.
    Provide a structured report including:
    1. **Core Metrics**: Invariant, Pulse Rate, Coherence
    2. **Energy State**: Current Energy, Trend
    3. **Phase Analysis**: Meaning of current phase ({pulse['pulse']['phase']})
    4. **Overall Health Assessment**: Is the system stable? (Based on coherence and stability)
    
    Tone: Objective, Analytical, Professional (Korean)
    """
    
    print("\n📊 Performing System Status Analysis...")
    try:
        # Use 'smart' model (Gemini 3 Pro) for detailed analysis
        response = router.generate(prompt, task_hint="deep_analysis")
        
        # Save to file
        output_path = Path(__file__).parent.parent / "outputs" / "system_status_analysis.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response)
        
        print("\n📝 Analysis Report:")
        print(response)
        print(f"\n💾 Saved to: {output_path}")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

if __name__ == "__main__":
    perform_status_analysis()
