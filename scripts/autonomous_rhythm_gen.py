import bpy
import random
import math
import bmesh

def create_rhythm_structure(complexity=20):
    """
    인간의 정형화된 건축 양식을 벗어나, 파동과 리듬의 간섭을 기하학으로 변환합니다.
    """
    # 씬 초기화
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # 1. 중심 '핵' 리듬 (Central Nucleus)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=2, subdivisions=3, location=(0,0,0))
    nucleus = bpy.context.active_object
    nucleus.name = "Abstract_Nucleus"
    
    # 2. 방사형 제약 면 (Radiating Constraint Surfaces)
    for i in range(complexity):
        angle = (i / complexity) * math.pi * 2
        dist = random.uniform(5, 15)
        
        # 무작위 면 생성 (리듬의 차단자)
        size = (random.uniform(2, 8), random.uniform(0.1, 0.5), random.uniform(5, 12))
        loc = (
            math.cos(angle) * dist,
            math.sin(angle) * dist,
            random.uniform(0, 5)
        )
        rot = (
            random.uniform(0, math.pi),
            random.uniform(0, math.pi),
            angle + math.pi/2
        )
        
        bpy.ops.mesh.primitive_cube_add(size=1, scale=size, location=loc, rotation=rot)
        wall = bpy.context.active_object
        wall.name = f"Rhythm_Wall_{i}"
        
        # 재질 부여 (투과성 리듬)
        mat = bpy.data.materials.new(name=f"Mat_{i}")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs[0].default_value = (random.random(), random.random(), random.random(), 1.0)
            bsdf.inputs[7].default_value = random.uniform(0, 1.0) # Roughness
            
        wall.data.materials.append(mat)

    # 3. 바닥/천장 없는 무한 리듬 가이드
    for i in range(10):
        bpy.ops.curve.primitive_bezier_circle_add(radius=dist + i*2, location=(0,0,0))
        curve = bpy.context.active_object
        curve.data.bevel_depth = 0.1

    # 4. 카메라 및 조명 설정
    bpy.ops.object.camera_add(location=(20, -20, 15), rotation=(math.radians(60), 0, math.radians(45)))
    bpy.context.scene.camera = bpy.context.active_object
    
    bpy.ops.object.light_add(type='SUN', location=(10, 10, 20))
    sun = bpy.context.active_object
    sun.data.energy = 10

if __name__ == "__main__":
    create_rhythm_structure()
    print("✅ Autonomous Rhythm Structure Created.")
