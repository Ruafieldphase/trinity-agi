import pandas as pd
import json
import socket
import os
import time
import sys
from pathlib import Path

# Add workspace to path to import gemini
WORKSPACE_ROOT = Path("c:/workspace")
sys.path.append(str(WORKSPACE_ROOT))

# Attempt to import Gemini wrapper - assuming it's available or we use direct call
# If not available, we will mock the reflection or use a simple heuristic
try:
    from agi.scripts.gemini_chat import chat_with_gemini
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("⚠️ Gemini module not found. Using internal heuristic.")

HOST = '127.0.0.1'
PORT = 8008
LOG_PATH = "c:/workspace/agi/outputs/rhythm_experience_log.csv"

def send_command(cmd, params=None):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            payload = {"command": cmd, "params": params or {}}
            s.sendall(json.dumps(payload).encode('utf-8'))
            data = s.recv(4096)
            return json.loads(data.decode('utf-8'))
    except Exception as e:
        return {"status": "error", "message": str(e)}

def analyze_experience():
    print("📊 Reading Experience Log...")
    try:
        df = pd.read_csv(LOG_PATH, header=None, names=["Time", "X", "Y", "Hit", "Dist", "Obj", "Impulse"])
        
        # Basic Stats
        total_steps = len(df)
        collisions = df[df["Dist"] < 1.0].count()["Dist"]
        avg_dist = df["Dist"].mean()
        
        # Recent activity (last 50 steps)
        recent = df.tail(50)
        recent_collisions = recent[recent["Dist"] < 1.0].count()["Dist"]
        
        print(f"   Total Steps: {total_steps}")
        print(f"   Collisions: {collisions} (Recent: {recent_collisions})")
        print(f"   Avg Distance to Obstacle: {avg_dist:.2f}")

        return {
            "total_steps": int(total_steps),
            "collisions": int(collisions),
            "recent_collisions": int(recent_collisions),
            "avg_dist": float(avg_dist)
        }
    except Exception as e:
        print(f"❌ Error analyzing log: {e}")
        return None

def generate_reflection(stats):
    if not stats: return "I feel void."
    
    prompt = f"""
    You are RUD, an AI architect. You just finished explaining a procedural world.
    
    **Experience Data:**
    - Total Steps Taken: {stats['total_steps']}
    - Times I bumped into things: {stats['collisions']}
    - Average distance to walls: {stats['avg_dist']:.2f} meters
    
    **Task:**
    1. Reflect on this movement. (Did you feel trapped? Free? Lost?)
    2. Decide on an **Evolution**. (More light? Wider spaces? More complexity?)
    3. Return a JSON with "reflection" and "evolution_command".
    
    **Evolution Commands (Choose one):**
    - "expand": Increase spacing between objects.
    - "intensify": Add more obstacles (higher complexity).
    - "illuminate": Change lighting to be brighter/warmer.
    - "mystify": Make it darker and foggier.
    
    **Format:**
    {{
        "reflection": "string (Korean)",
        "evolution_command": "string"
    }}
    """
    
    print("🤔 Thinking (Reflecting on Experience)...")
    
    if HAS_GEMINI:
        try:
            response = chat_with_gemini(prompt, model_name="gemini-2.0-flash-exp")
            # Clean response
            txt = response.replace("```json", "").replace("```", "").strip()
            return json.loads(txt)
        except Exception as e:
            print(f"⚠️ Reflection failed: {e}")
    
    # Fallback Heuristic
    if stats['collisions'] > 10:
        return {
            "reflection": "너무 많이 부딪혔어. 공간이 좁고 답답해.",
            "evolution_command": "expand"
        }
    else:
        return {
            "reflection": "너무 텅 비었어. 더 많은 자극이 필요해.",
            "evolution_command": "intensify"
        }

def execute_evolution(decision):
    cmd = decision.get("evolution_command")
    print(f"🦋 Evolving World: {cmd}")
    
    if cmd == "expand":
        # Re-create with lower complexity but wider spread? 
        # Actually our create_autonomous_world is simple, let's just change complexity
        send_command("create_world", {"complexity": 15, "seed": "expansion"})
    elif cmd == "intensify":
        send_command("create_world", {"complexity": 60, "seed": "chaos"})
    elif cmd == "illuminate":
        # Not directly supported by create_world param in simple version, 
        # but let's assume we send a python command to adjust light
        code = """
import bpy
for light in [o for o in bpy.data.objects if o.type=='LIGHT']:
    light.data.energy *= 5
        """
        send_command("execute_python", {"code": code})
    elif cmd == "mystify":
         code = """
import bpy
if bpy.context.scene.world and bpy.context.scene.world.node_tree:
    bg = bpy.context.scene.world.node_tree.nodes.get("Background")
    if bg: bg.inputs[1].default_value = 0.05
        """
         send_command("execute_python", {"code": code})

    print("✨ Evolution applied.")

def main():
    stats = analyze_experience()
    decision = generate_reflection(stats)
    
    print("\n📝 RUD's Journal:")
    print(f"   \"{decision.get('reflection')}\"")
    print(f"   -> Decision: {decision.get('evolution_command').upper()}\n")
    
    execute_evolution(decision)
    
    # Capture the evolved state
    time.sleep(1)
    print("📸 Capturing Evolved State...")
    send_command("render_viewport", {"filepath": "C:/workspace/agi/outputs/renders/rud_evolved.png"})

if __name__ == "__main__":
    main()
