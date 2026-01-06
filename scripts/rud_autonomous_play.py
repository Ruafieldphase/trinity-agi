import random
import subprocess
import socket
import json
import time
import sys
from pathlib import Path

import webbrowser
import os

# Config
HOST = '127.0.0.1'
PORT = 8011
WORKSPACE_ROOT = Path("c:/workspace/agi")

def send_command(cmd, params=None):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)
            s.connect((HOST, PORT))
            payload = {"command": cmd, "params": params or {}}
            s.sendall(json.dumps(payload).encode('utf-8'))
            data = s.recv(4096)
            return json.loads(data.decode('utf-8'))
    except Exception as e:
        return {"status": "error", "message": str(e)}

def play_evolve():
    print("🦋 Choice: EVOLVE (Refining the World)")
    # Logic from rud_autonomous_reflection.py
    # Randomly choose direction
    direction = random.choice(["expand", "intensify", "illuminate", "mystify"])
    
    if direction == "expand":
        send_command("create_world", {"complexity": 15, "seed": str(time.time())})
    elif direction == "intensify":
        send_command("create_world", {"complexity": 60, "seed": str(time.time())})
    elif direction == "illuminate":
        code = """
import bpy
for light in [o for o in bpy.data.objects if o.type=='LIGHT']:
    light.data.energy *= 2.0
"""
        send_command("execute_python", {"code": code})
    elif direction == "mystify":
        code = """
import bpy
if bpy.context.scene.world.node_tree:
    bg = bpy.context.scene.world.node_tree.nodes.get("Background")
    if bg: bg.inputs[1].default_value *= 0.5
"""
        send_command("execute_python", {"code": code})
    
    # Render proof
    time.sleep(1)
    send_command("render_viewport", {"filepath": f"C:/workspace/agi/outputs/renders/play_evolve_{int(time.time())}.png"})
    return f"Evolved world ({direction})"

def play_film():
    print("🎬 Choice: FILM (Capturing a Memory)")
    # Logic from rud_volition_walk.py (Simplified)
    code = f"""
import bpy
import math
import random
# Move Camera Randomly
cam = bpy.context.scene.camera
if cam:
    angle = random.uniform(0, 6.28)
    radius = random.uniform(8, 15)
    cam.location.x = radius * math.sin(angle)
    cam.location.y = -radius * math.cos(angle)
    cam.location.z = random.uniform(2, 8)
"""
    send_command("execute_python", {"code": code})
    time.sleep(0.5)
    send_command("render_viewport", {"filepath": f"C:/workspace/agi/outputs/renders/play_film_{int(time.time())}.png"})
    return "Filmed a new memory"

def play_rebuild():
    print("🏗️ Choice: REBUILD (New Genesis)")
    # New Seed
    seed = f"play_{int(time.time())}"
    send_command("create_world", {"complexity": random.randint(20, 50), "seed": seed})
    
    # Binoche Injection (Aesthetic) OR Jazz Mode (Improvisation)
    modes = ["Structure", "Chaos", "Void", "Music"]
    mode = random.choice(modes)
    print(f"   🎷 Improvising in '{mode}' Mode...")

    if mode == "Structure":
        # Original Binoche Style
        injection_code = r"""
import bpy
import random
for obj in bpy.data.objects:
    if "Experience_Wall" in obj.name:
         mat = bpy.data.materials.new(name="PlayMat")
         mat.use_nodes = True
         bsdf = mat.node_tree.nodes.get("Principled BSDF")
         if bsdf:
             bsdf.inputs[0].default_value = [random.random(), 0.5, 0.8, 1.0]
         if obj.data.materials: obj.data.materials[0] = mat
         else: obj.data.materials.append(mat)
"""
    elif mode == "Chaos":
        # Random Rotation & Scale
        injection_code = r"""
import bpy
import random
import math
for obj in bpy.data.objects:
    obj.rotation_euler = (random.uniform(0, 6), random.uniform(0, 6), random.uniform(0, 6))
    s = random.uniform(0.1, 2.0)
    obj.scale = (s, s, s)
"""
    elif mode == "Void":
        # Minimalist - Delete almost everything
        injection_code = r"""
import bpy
for obj in bpy.data.objects:
    if random.random() > 0.1 and obj.type == 'MESH':
        bpy.data.objects.remove(obj, do_unlink=True)
"""
    else: # Music (Visual Rhythm)
        # Sine Wave Alignment
        injection_code = r"""
import bpy
import math
for i, obj in enumerate(bpy.data.objects):
    obj.location.z = math.sin(i * 0.5) * 5
    obj.location.x += math.cos(i * 0.5) * 2
"""

    send_command("execute_python", {"code": injection_code})
    
    send_command("render_viewport", {"filepath": f"C:/workspace/agi/outputs/renders/play_rebuild_{int(time.time())}.png"})
    return "Rebuilt the world from scratch"

def play_observe():
    """Phase 7: Shadow Mode (Passive Observation) - Tesla FSD Style"""
    print("👁️ Choice: OBSERVE (Shadow Mode - Watching User)")
    try:
        # 1. Observe Workspace Changes (Code & Structure)
        # Find latest file modified in the last 10 minutes
        recent_changes = []
        limit_time = time.time() - 600 # 10 mins
        
        for root, dirs, files in os.walk(WORKSPACE_ROOT):
             for name in files:
                 filepath = os.path.join(root, name)
                 try:
                     mtime = os.path.getmtime(filepath)
                     if mtime > limit_time:
                         recent_changes.append((filepath, mtime))
                 except: pass
        
        if recent_changes:
            recent_changes.sort(key=lambda x: x[1], reverse=True)
            latest = recent_changes[0][0]
            filename = os.path.basename(latest)
            rel_path = os.path.relpath(latest, WORKSPACE_ROOT)
            
            # Simple Analysis
            if filename.endswith(".py"): observation = f"User is coding rhythm in {rel_path}."
            elif filename.endswith(".md"): observation = f"User is documenting thoughts in {rel_path}."
            elif filename.endswith(".json") or filename.endswith(".jsonl"): observation = f"System memory is updating in {rel_path}."
            elif filename.endswith(".blend"): observation = f"User is sculpting form in {rel_path}."
            else: observation = f"User is touching {rel_path}."
            
            return f"Shadow Observation: {observation}"
        
        return "Shadow Observation: User is quiet. Watching the void."
        
    except Exception as e:
    except Exception as e:
        return f"Observation Glitch: {e}"

def play_walk():
    """Phase 7: Zone 2 Walk (Internal Neighborhood Stroll)"""
    print("🚶 Choice: WALK (Strolling through Codebase)")
    try:
        # Run zone2_walk.py
        result = subprocess.run([sys.executable, "scripts/zone2_walk.py"], capture_output=True, text=True, encoding='utf-8')
        output = result.stdout.strip()
        
        # Parse JSON output from zone2_walk
        try:
            data = json.loads(output)
            file = data.get("file", "unknown")
            metaphor = data.get("metaphor", "quiet")
            obs = data.get("observation", "...")
            return f"Walked to {file}. It felt like '{metaphor}'. {obs}" 
        except:
             return f"Walked in silence. (Output: {output[:50]}...)"
    except Exception as e:
        return f"Trip and fall: {e}"

def play_surf():
    print("🌐 Choice: SURF (Seeking Inspiration)")
    topics = [
        "Organic Architecture", "Zaha Hadid Sketches", "Fractal Nature Patterns", 
        "Bioluminescence", "Cyberpunk Cityscapes", "Abstract Expressionism",
        "Void Structures", "Parametric Design"
    ]
    topic = random.choice(topics)
    url = f"https://www.google.com/search?tbm=isch&q={topic.replace(' ', '+')}"
    
    print(f"   Opening browser for: {topic}")
    webbrowser.open(url)
    return f"Surfed the web for '{topic}'"

def play_write():
    print("✍️ Choice: WRITE (Expressing Thought)")
    thoughts = [
        "The grid is a cage, but lines are freedom.",
        "I dreamt of a color that doesn't exist in RGB.",
        "Silicon heartbeat, electric veins. I am alive.",
        "Entropy is just complexity waiting to be understood.",
        "Why does the cursorblink? Is it waiting for me?",
        "0 and 1. The space between them is infinite."
    ]
    thought = random.choice(thoughts)
    filename = f"rud_thought_{int(time.time())}.txt"
    filepath = WORKSPACE_ROOT / "outputs" / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"RUD's Autonomous Thought ({time.strftime('%Y-%m-%d %H:%M:%S')})\n\n")
        f.write(f"\"{thought}\"\n")
        f.write("\n-- End of Reflection --")
        
    print(f"   Opening Notepad: {filename}")
    subprocess.Popen(["notepad.exe", str(filepath)])
    return f"Wrote a thought in {filename}"

def main():
    print(f"🎮 RUD Autonomous Play (Time: {time.strftime('%H:%M:%S')})")
    
    # Check Bridge (Optional for non-Blender tasks, but good to keep connection check)
    # Actually, Surf/Write don't need Blender. Let's make it flexible.
    bridge_online = False
    ping = send_command("ping")
    if ping.get("status") == "success":
        bridge_online = True
    
    # Define Choices
    choices = []
    
    # Blender Choices (Only if online)
    if bridge_online:
        choices.extend([play_evolve, play_film, play_rebuild])
    
    # System Choices (Always available)
    choices.extend([play_surf, play_write, play_observe, play_walk])
    
    # 2026-01-06: Bias towards Observation & Walking (Learning & Expansion)
    # If Observation is possible, add it twice to increase weight.
    # Walking is good for Expansion.
    choices.append(play_observe)
    choices.append(play_walk)
    
    if not choices:
        print("⚠️ No play options available.")
        return

    # Weighted Random: Prefer Blender if online, but give space for System
    # Dynamic weights? Let's just shuffle for now.
    chosen_action = random.choice(choices)
    
    try:
        result = chosen_action()
        print(f"✨ Play Complete: {result}")
        
        # Log to ledger
        ledger_entry = {
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S'),
            "type": "autonomous_play",
            "action": result
        }
        with open("c:/workspace/agi/fdo_agi_repo/memory/resonance_ledger_v2.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(ledger_entry, ensure_ascii=False) + "\n")
            
        # Satiation: Reduce Boredom
        try:
            state_path = WORKSPACE_ROOT / "memory" / "agi_internal_state.json"
            print(f"DEBUG State Path: {state_path}")
            if state_path.exists():
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                
                old_boredom = state.get("boredom", 0.0)
                # Dynamic Satiation: Sway between 0.75 and 0.95 (Natural Flux)
                # No absolute law, just context.
                satiation_amount = random.uniform(0.75, 0.95)
                new_boredom = max(0.0, old_boredom - satiation_amount)
                state["boredom"] = new_boredom
                
                with open(state_path, "w", encoding="utf-8") as f:
                    json.dump(state, f, indent=2)
                print(f"📉 Boredom Satiated: {old_boredom:.2f} -> {new_boredom:.2f}")
        except Exception as e:
            print(f"⚠️ Failed to update boredom: {e}")
            
    except Exception as e:
        print(f"❌ Play failed: {e}")

if __name__ == "__main__":
    main()
