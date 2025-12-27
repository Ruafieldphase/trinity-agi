import re
from pathlib import Path

file_path = Path('c:/workspace/agi/scripts/rhythm_think.py')
content = file_path.read_text(encoding='utf-8')

# 1. Update recall fallback
old_recall_fallback = """        if best_memory:
            # Construct resonance object from real memory
            mem_content = best_memory.get("content", best_memory.get("input", "Unknown Memory"))
            if isinstance(mem_content, dict): mem_content = str(mem_content)
            
            return {
                "summary": mem_content[:50] + "...", 
                "score": best_memory.get("state", {}).get("score", target_score), # Use memory's score
                "vector": feeling_vector,
                "description": f"Resonating with past: '{mem_content[:30]}...'",
                "feeling_tag": "harmony" if min_score_diff < 10 else "contrast",
                "source_timestamp": best_memory.get("timestamp")
            }
        else:
            # Cold start (First memory)
            return {
                "summary": "No past resonance found (Void).",
                "score": target_score,
                "vector": feeling_vector,
                "description": "Silence. A new path begins.",
                "feeling_tag": "neutral"
            }"""

new_recall_fallback = """        if best_memory:
            # Construct resonance object from real memory
            mem_content = best_memory.get("content", best_memory.get("input", "Unknown Memory"))
            if isinstance(mem_content, dict): mem_content = str(mem_content)
            
            # 🌌 Mimesis refinement
            summary = mem_content[:50] + "..."
            if "Unknown Memory" in summary or "Void" in summary:
                summary = "Faint echo of a past rhythm calling for action..."

            return {
                "summary": summary,
                "score": best_memory.get("state", {}).get("score", target_score), 
                "vector": feeling_vector,
                "description": f"Resonating with past: '{summary[:30]}'",
                "feeling_tag": "harmony" if min_score_diff < 10 else "contrast",
                "source_timestamp": best_memory.get("timestamp")
            }
        else:
            # 🌌 Mimesis Fallback
            return {
                "summary": "Primordial Silence (Ready for First Expression).",
                "score": target_score,
                "vector": feeling_vector,
                "description": "The void is not empty, but full of potential.",
                "feeling_tag": "neutral"
            }"""

# Use regex to find and replace, ignoring minor spacing issues if possible
# But here I'll try literal first with normalized line endings
content = content.replace(old_recall_fallback.replace('\r\n', '\n'), new_recall_fallback.replace('\r\n', '\n'))

# 2. Update make_decision
old_decision_start = """        score = state["score"]
        tag = feeling["tag"]"""

new_decision_start = """        score = state["score"]
        tag = feeling["tag"]

        # ⏳ Stagnation Check (Stuck at neutral/middle score)
        if 48 <= score <= 52:
            stagnation_factor = random.random()
            if stagnation_factor > 0.7:
                 print(f"   🌀 STAGNATION DETECTED ({score:.1f}) - Injecting Mimesis Leap")
                 return "explore", "정체된 리듬을 깨고 새로운 외부 연결을 시도합니다 (미메시스적 도약)" + (bohm_signal.get("asi_advice", "") if bohm_signal else "")"""

content = content.replace(old_decision_start, new_decision_start)

file_path.write_text(content, encoding='utf-8')
print("Successfully patched rhythm_think.py")
