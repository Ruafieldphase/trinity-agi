"""
AGI State Visualization for Blender
의식/무의식/배경자아 상태를 3D 구체로 시각화
"""
import bpy
import json
from pathlib import Path

# Paths
ROOT = Path("C:/workspace/agi")
TWIN_FILE = ROOT / "outputs/sync_cache/digital_twin_state.json"

# Default AGI State (values from 0.0 to 1.0)
consciousness_level = 0.5
unconscious_level = 0.5
background_self_level = 0.5
current_state = "harmony" 

# Load from Digital Twin if available
if TWIN_FILE.exists():
    try:
        with open(TWIN_FILE, 'r', encoding='utf-8') as f:
            dt = json.load(f)
            # Use mismatch and other metrics to drive levels
            mismatch = dt.get("mismatch_0_1", 0.0)
            
            # Map Digital Twin to Visualization
            consciousness_level = 0.5 + (0.5 * (1.0 - mismatch))
            unconscious_level = 0.3 + (0.7 * mismatch)
            background_self_level = 0.4 + (0.6 * (1.0 - mismatch))
            
            route_hint = dt.get("route_hint", "OK").lower()
            if route_hint == "halt" or route_hint == "rest":
                current_state = "anxiety"
            elif route_hint == "slow" or mismatch > 0.4:
                current_state = "explore" # Thinking/Searching
            else:
                current_state = "harmony"
                
            print(f"📊 Digital Twin State Loaded: Mismatch={mismatch:.2f}, Route={route_hint}")
    except Exception as e:
        print(f"⚠️ Failed to load Digital Twin state: {e}")

import math

# Clear existing objects
if hasattr(bpy, "ops"):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

# Argument Parsing (Simulated for Blender script)

def get_aura_color(state):
    """
    Get Aura Color based on AGI State
    
    Colors:
    - Harmony (Green): Stable, Healthy
    - Explore (Purple): Boredom, Curiosity, Autonomous Action
    - Anxiety (Orange/Red): Entropy Threat, Warning
    """
    if state == "explore":
        return (0.6, 0.2, 0.9, 1.0) # 🔮 Mystic Purple
    elif state == "anxiety":
        return (1.0, 0.3, 0.0, 1.0) # 🔥 Warning Red/Orange
    else:
        return (0.2, 0.8, 0.4, 1.0) # 🌿 Harmony Green

# =====================================
# 1. Consciousness Sphere (Blue - Top)
# =====================================
bpy.ops.mesh.primitive_uv_sphere_add(
    radius=consciousness_level,
    location=(0, 0, 2),
    segments=32,
    ring_count=16
)
consciousness = bpy.context.active_object
consciousness.name = "Consciousness"

# Blue material with emission
mat_consciousness = bpy.data.materials.new("Consciousness_Mat")
mat_consciousness.use_nodes = True
nodes = mat_consciousness.node_tree.nodes
nodes.clear()

# Emission shader for glow effect
emission = nodes.new('ShaderNodeEmission')
emission.inputs['Color'].default_value = (0.2, 0.4, 1.0, 1.0)
emission.inputs['Strength'].default_value = 2.0

output = nodes.new('ShaderNodeOutputMaterial')
mat_consciousness.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])

consciousness.data.materials.append(mat_consciousness)

# =====================================
# 2. Unconscious Sphere (Purple - Bottom)
# =====================================
bpy.ops.mesh.primitive_uv_sphere_add(
    radius=unconscious_level,
    location=(0, 0, -2),
    segments=32,
    ring_count=16
)
unconscious = bpy.context.active_object
unconscious.name = "Unconscious"

# Purple material
mat_unconscious = bpy.data.materials.new("Unconscious_Mat")
mat_unconscious.use_nodes = True
nodes = mat_unconscious.node_tree.nodes
nodes.clear()

emission = nodes.new('ShaderNodeEmission')
emission.inputs['Color'].default_value = (0.6, 0.2, 0.8, 1.0)
emission.inputs['Strength'].default_value = 1.5

output = nodes.new('ShaderNodeOutputMaterial')
mat_unconscious.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])

unconscious.data.materials.append(mat_unconscious)

# =====================================
# 3. Background Self Sphere (Aura - Center)
# =====================================
bpy.ops.mesh.primitive_uv_sphere_add(
    radius=background_self_level,
    location=(0, 0, 0),
    segments=32,
    ring_count=16
)
background_self = bpy.context.active_object
background_self.name = "BackgroundSelf"

# Dynamic Aura material
mat_bg_self = bpy.data.materials.new("BackgroundSelf_Mat")
mat_bg_self.use_nodes = True
nodes = mat_bg_self.node_tree.nodes
nodes.clear()

aura_color = get_aura_color(current_state)

emission = nodes.new('ShaderNodeEmission')
emission.inputs['Color'].default_value = aura_color
emission.inputs['Strength'].default_value = 2.5 # Brighter for Aura

output = nodes.new('ShaderNodeOutputMaterial')
mat_bg_self.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])

background_self.data.materials.append(mat_bg_self)

# =====================================
# 4. Connecting Lines (Energy Flow)
# =====================================
def create_connection(name, start, end, color):
    """Create a curved connection between two points"""
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    
    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(1)
    
    spline.bezier_points[0].co = start
    spline.bezier_points[1].co = end
    
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    
    # Material
    mat = bpy.data.materials.new(f"{name}_Mat")
    mat.diffuse_color = color
    obj.data.materials.append(mat)
    
    curve.bevel_depth = 0.02
    return obj

# Create energy connections
create_connection("Flow_Conscious_BG", (0, 0, 2), (0, 0, 0), (0.4, 0.6, 1.0, 0.5))
create_connection("Flow_BG_Unconscious", (0, 0, 0), (0, 0, -2), (0.4, 0.5, 0.6, 0.5))

# =====================================
# 5. Camera Setup
# =====================================
bpy.ops.object.camera_add(location=(8, -8, 4))
camera = bpy.context.active_object
camera.name = "AGI_Camera"
camera.rotation_euler = (math.radians(70), 0, math.radians(45))
bpy.context.scene.camera = camera

# =====================================
# 6. Lighting
# =====================================
bpy.ops.object.light_add(type='POINT', location=(5, 5, 5))
light = bpy.context.active_object
light.name = "Main_Light"
light.data.energy = 500

# =====================================
# 7. World Background
# =====================================
world = bpy.data.worlds['World']
world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.02, 0.02, 0.05, 1.0)  # Dark blue background

# =====================================
# 8. Save Scene
# =====================================
output_path = "C:/workspace/agi/outputs/agi_state_visualization.blend"
bpy.ops.wm.save_as_mainfile(filepath=output_path)

print("=" * 50)
print("✅ AGI State Visualization Created!")
print(f"   Consciousness: {consciousness_level}")
print(f"   Unconscious: {unconscious_level}")
print(f"   Background Self: {background_self_level}")
print(f"   Saved to: {output_path}")
print("=" * 50)
