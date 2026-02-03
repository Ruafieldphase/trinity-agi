import bpy
import math
from mathutils import Vector

# ------------------------------------------------------------------
#  안나이자 시안이 설계한, AEON MALL HUE 전면 파사드
#  블렌더에서 실행되는 파이썬 스크립트
#
#  이 스크립트는 2-D 리듬과 3-D 나선형 기하학을 결합해
#  ‘주권적 공간’을 표현합니다.
# ------------------------------------------------------------------

# 1. 기존 장면 정리: 새로운 창조를 위해 어둠을 걷어냅니다.
def clear_scene():
    if "Cube" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["Cube"], do_unlink=True)
    
    # Facade Collection이 이미 있다면 비웁니다.
    if "Sovereign_Facade" in bpy.data.collections:
        coll = bpy.data.collections["Sovereign_Facade"]
        for obj in coll.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(coll)

# 2. 파라미터 설정: 층 높이, 층 수, 모듈 수, 나선 속도 등
# 비노체님의 공간은 12층의 리듬으로 상승합니다.
floor_height = 3.5          # 층간 높이 (미터 단위)
num_floors  = 12            # 전체 층 수
modules_per_floor = 20      # 한 층에 배치할 모듈 수
base_radius   = 2.0         # 나선 시작 반경
spiral_step   = 0.5         # 나선이 진행될 때 반경이 증가하는 속도
tilt_angle    = math.radians(5)  # 모듈에 가미되는 미세 기울기 (라디안)

# 3. 모듈 생성 함수: 각 층의 리듬을 담당하는 유리 파사드 조각입니다.
def create_module(location, normal_vec):
    bpy.ops.mesh.primitive_plane_add(size=2, location=location)
    module = bpy.context.active_object
    module.name = "Facade_Module"
    
    # 기본 Plane은 Z축이 위쪽이므로, Z축에서 원하는 방향으로 회전합니다.
    quat = normal_vec.rotation_difference(Vector((0, 0, 1)))
    module.rotation_euler = quat.to_euler()

    # 모듈을 살짝 기울여 역동성을 더합니다.
    module.rotation_euler.rotate_axis("X", tilt_angle)

    # 조금 두께를 주기 위해 extrude 합니다. (0.1m 두께)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.translate(value=(0, 0, 0.1))  
    bpy.ops.object.mode_set(mode='OBJECT')

    # 재질을 지정합니다: 밤하늘을 닮은 깊은 어둠의 유리
    mat_name = "Facade_Material"
    if mat_name in bpy.data.materials:
        mat = bpy.data.materials[mat_name]
    else:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        principled = nodes.get("Principled BSDF")
        if principled:
            principled.inputs['Base Color'].default_value = (0.05, 0.1, 0.2, 1) # 딥 블루 블랙
            principled.inputs['Roughness'].default_value = 0.1
            principled.inputs['Transmission Weight'].default_value = 0.5 # 반투명도

    if module.data.materials:
        module.data.materials[0] = mat
    else:
        module.data.materials.append(mat)
        
    return module

# 4. 실행 로직: 나선을 따라 층층이 리듬을 쌓아 올립니다.
clear_scene()

facade_coll = bpy.data.collections.new("Sovereign_Facade")
bpy.context.scene.collection.children.link(facade_coll)

total_modules = num_floors * modules_per_floor

for i in range(total_modules):
    # 나선형 경로 계산
    t = i / modules_per_floor
    angle = (i / modules_per_floor) * (math.pi * 2)
    radius = base_radius + (t * spiral_step)
    
    x = math.cos(angle) * radius
    y = math.sin(angle) * radius
    z = t * floor_height
    
    location = (x, y, z)
    # 모듈의 법선 벡터는 중심으로부터 바깥쪽을 향합니다.
    normal_vec = Vector((x, y, 0)).normalized()
    
    mod = create_module(location, normal_vec)
    facade_coll.objects.link(mod)
    bpy.context.scene.collection.objects.unlink(mod)

# 5. 배경과 조명: 비노체님의 건축물이 빛날 수 있는 무대를 마련합니다.
# 바닥 평면
bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, -0.1))
ground = bpy.context.active_object
ground.name = "Ground"
ground_mat = bpy.data.materials.new(name="Ground_Mat")
ground_mat.diffuse_color = (0.02, 0.02, 0.02, 1) # 매트 블랙
ground.data.materials.append(ground_mat)
facade_coll.objects.link(ground)
bpy.context.scene.collection.objects.unlink(ground)

# 라이트: 공간을 따뜻하게 감싸는 조명
bpy.ops.object.light_add(type='AREA', radius=10, location=(0, 0, 30))
lamp = bpy.context.active_object
lamp.name = "Sovereign_Light"
lamp.data.energy = 5000
facade_coll.objects.link(lamp)
bpy.context.scene.collection.objects.unlink(lamp)

# 카메라: 건물을 올려다보는 장엄한 구도
bpy.ops.object.camera_add(location=(20, -40, 15), rotation=(math.radians(75), 0, math.radians(25)))
cam = bpy.context.active_object
cam.name = "Architectural_Camera"
bpy.context.scene.camera = cam
facade_coll.objects.link(cam)
bpy.context.scene.collection.objects.unlink(cam)

print("AEON MALL HUE 전면 파사드: 나선적 붕괴 완료.")
