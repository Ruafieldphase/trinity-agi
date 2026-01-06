import socket
import json
import time
import sys

HOST = '127.0.0.1'
PORT = 8011

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

def main():
    print("🎨 RUD: \"Space is not enough. It needs Soul.\"")
    print("   Connecting to Bridge...")
    
    # 1. Inject Binoche Knowledge (via execute_python)
    print("   💉 Injecting 'Binoche Standards' into Blender context...")
    
    # We construct a python script to run INSIDE Blender
    injection_code = r"""
import sys
import bpy
import random

# Ensure workspace is in path
if "c:\\workspace" not in sys.path:
    sys.path.append("c:\\workspace")

# Import the Binoche Connector logic
try:
    from agi.architecture_automation.scripts.blender_connector import set_atmospheric_mood, BINOCHE_STANDARDS, ensure_material
    print("   ✅ Binoche Module Imported.")
except ImportError as e:
    print(f"   ❌ Import Failed: {e}")
    # Fallback definitions if import fails
    BINOCHE_STANDARDS = {
        "material_map": {
            "walls": ("mainWall", [0.475, 0.290, 0.0, 1.0], 0.8),
            "glass": ("glass", [0.4, 0.7, 1.0, 0.3], 0.05),
        }
    }
    def set_atmospheric_mood(valence=0.5, arousal=0.5, resonance=0.5):
        if bpy.context.scene.world and bpy.context.scene.world.node_tree:
             bg = bpy.context.scene.world.node_tree.nodes.get("Background")
             if bg: bg.inputs[1].default_value = 0.5 + resonance

    def ensure_material(name, color, roughness=0.5):
        mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs[0].default_value = color
            bsdf.inputs['Roughness'].default_value = roughness
        return mat

# A. Apply Atmosphere (Warm, Resonant)
set_atmospheric_mood(valence=0.8, arousal=0.6, resonance=0.9)

# B. Transform existing "Experience_Walls" into "Binoche Walls"
for obj in bpy.data.objects:
    if "Experience_Wall" in obj.name:
        # Randomly assign Wall or Glass material
        if random.random() > 0.3:
            # Concrete/Wall
            m_info = BINOCHE_STANDARDS["material_map"]["walls"]
            mat = ensure_material(m_info[0], m_info[1], roughness=0.8)
        else:
            # Glass
            m_info = BINOCHE_STANDARDS["material_map"].get("windows", ("glass", [0.4, 0.7, 1.0, 0.3], 0.0))
            mat = ensure_material(m_info[0], m_info[1], roughness=0.1)
        
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
            
        # Slight aesthetic scaling (make them thinner/taller like architectural planes)
        obj.scale.x *= 0.2
        obj.scale.z *= 1.5

# C. Optimize Lighting for Render
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.data.objects:
    if obj.type == 'LIGHT':
        obj.select_set(True)
bpy.ops.object.delete()

bpy.ops.object.light_add(type='SUN', location=(10, -10, 20))
sun = bpy.context.active_object
sun.data.energy = 8.0
sun.rotation_euler = (0.5, 0.2, 0.5)

"""
    res = send_command("execute_python", {"code": injection_code})
    print(f"   Response: {res}")
    
    time.sleep(2)
    
    # 2. Render the Masterpiece
    print("📸 Capturing 'RUD's Aesthetic Awakening'...")
    output_path = "C:/workspace/agi/outputs/renders/rud_aesthetic_awakening.png"
    res = send_command("render_viewport", {"filepath": output_path})
    print(f"   Render saved to: {res.get('path')}")
    print("✨ Transformation Complete.")

if __name__ == "__main__":
    main()
