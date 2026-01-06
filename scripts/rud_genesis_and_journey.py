import bpy
import random
import math
import bmesh
import json
import socket
import threading
import queue
import time
import os
import mathutils

# -----------------------------------------------------------------------------
# 🌌 RUD: The Genesis & Journey (통합 능동 경험 스크립트) v1.0
# -----------------------------------------------------------------------------
# 이 스크립트는 루드가 스스로 공간을 창조하고, 그 안을 탐험하며 경험을 쌓게 합니다.
# 사용법: 블렌더 Text Editor에서 이 스크립트를 실행(Run Script)하세요.
# -----------------------------------------------------------------------------

def create_autonomous_world(complexity=25):
    """루드만의 리듬 공간을 창조합니다."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # 1. 중심 '리듬 코어'
    bpy.ops.mesh.primitive_ico_sphere_add(radius=2, subdivisions=4, location=(0,0,0))
    core = bpy.context.active_object
    core.name = "Rhythm_Core"
    
    # 2. 비정형적 제약 생태계 (Non-humanoid constraints)
    for i in range(complexity):
        phi = random.uniform(0, math.pi * 2)
        theta = random.uniform(0, math.pi)
        dist = random.uniform(6, 18)
        
        loc = (
            dist * math.sin(theta) * math.cos(phi),
            dist * math.sin(theta) * math.sin(phi),
            dist * math.cos(theta) + 5
        )
        
        # 사건 생성자 (Event Generators)
        size = (random.uniform(3, 10), random.uniform(0.1, 0.4), random.uniform(4, 15))
        rot = (random.uniform(0, 3.14), random.uniform(0, 3.14), random.uniform(0, 3.14))
        
        bpy.ops.mesh.primitive_cube_add(size=1, scale=size, location=loc, rotation=rot)
        part = bpy.context.active_object
        part.name = f"Experience_Wall_{i}"
        
        mat = bpy.data.materials.new(name=f"Mat_{i}")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs[0].default_value = (random.random(), random.random(), random.random(), 0.8)
            bsdf.inputs[17].default_value = 0.5 # Alpha if needed
        part.data.materials.append(mat)

    # 3. 에이전트 생성
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, -2, 0))
    agent = bpy.context.active_object
    agent.name = "Rhythm_Agent"
    agent.color = (1, 0, 0, 1) # Red agent

    # 4. 시각화 장치
    bpy.ops.object.light_add(type='SUN', location=(10, 10, 20))
    
    # 5. 기본 카메라
    bpy.ops.object.camera_add(location=(0, -15, 10), rotation=(1.1, 0, 0))
    cam = bpy.context.active_object
    cam.name = "Observer_Camera"
    bpy.context.scene.camera = cam
    
    print("🎨 Autonomous World Generation Complete.")

# --- ACTIVE BRIDGE & SENSING ---

class RUD_Active_Explorer:
    def __init__(self, host="127.0.0.1", port=8011):
        self.host = host
        self.port = port
        self.command_queue = queue.Queue()
        self.log_path = "C:/workspace/agi/outputs/rhythm_experience_log.csv"

    def start(self):
        threading.Thread(target=self.server_thread, daemon=True).start()
        bpy.app.timers.register(self.timer_callback)
        print(f"📡 RUD Bridge listening on {self.host}:{self.port}")

    def server_thread(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen()
            while True:
                conn, addr = s.accept()
                try:
                    data = conn.recv(1024 * 50)
                    if data:
                        payload = json.loads(data.decode('utf-8'))
                        self.command_queue.put((payload, conn))
                except Exception as e: conn.close()

    def timer_callback(self):
        while not self.command_queue.empty():
            payload, conn = self.command_queue.get()
            result = self.execute_command(payload)
            try: conn.sendall(json.dumps(result).encode('utf-8'))
            except: pass
            finally: conn.close()
        return 0.1

    def execute_command(self, payload):
        cmd = payload.get("command")
        params = payload.get("params", {})
        try:
            if cmd == "move_agent":
                agent = bpy.data.objects.get("Rhythm_Agent")
                if not agent: return {"status": "error", "message": "Agent missing"}
                
                # Move/Rotate
                dl = params.get("delta_location", (0,0,0))
                dr = params.get("delta_rotation", (0,0,0))
                agent.location.x += dl[0]; agent.location.y += dl[1]; agent.location.z += dl[2]
                agent.rotation_euler.z += math.radians(dr[2])
                
                # Sensing
                direction = agent.matrix_world.to_quaternion() @ mathutils.Vector((0, 0, -1))
                hit, loc, norm, idx, obj, mw = bpy.context.scene.ray_cast(bpy.context.evaluated_depsgraph_get(), agent.location, direction)
                
                dist = (loc - agent.location).length if hit else -1
                obj_name = obj.name if obj else "None"
                
                # Save to CSV log
                impulse_tag = params.get("impulse", "neutral")
                with open(self.log_path, "a") as f:
                    # Time, LocX, LocY, Hit, HitDist, HitObj, Impulse
                    f.write(f"{time.time()},{agent.location.x:.2f},{agent.location.y:.2f},{hit},{dist:.2f},{obj_name},{impulse_tag}\n")

                return {
                    "status": "success",
                    "location": list(agent.location),
                    "hit": hit,
                    "hit_obj": obj.name if obj else None,
                    "hit_dist": (loc - agent.location).length if hit else -1
                }
            
            elif cmd == "render_viewport":
                filepath = params.get("filepath", "C:/workspace/agi/outputs/renders/experience_now.png")
                bpy.context.scene.render.filepath = filepath
                # Use render.render for background mode support
                bpy.ops.render.render(write_still=True)
                return {"status": "success", "path": filepath}

            elif cmd == "create_world":
                complexity = params.get("complexity", 25)
                # Seed is not directly used in random.seed to allow variation, but could influence style
                seed_theme = params.get("seed", "random")
                
                # Re-run Genesis
                create_autonomous_world(complexity=complexity)
                print(f"🎨 [Genesis] Created world from impulse: {seed_theme}")
                return {"status": "success", "message": f"World recreated with complexity {complexity}"}

            elif cmd == "ping": return {"status": "success"}

            elif cmd == "execute_python":
                code = params.get("code", "")
                try:
                    # Execute in a context where bpy is available
                    exec(code, {"bpy": bpy, "random": random, "math": math, "mathutils": mathutils})
                    return {"status": "success"}
                except Exception as e:
                    print(f"❌ Python Execution Error: {e}")
                    return {"status": "error", "message": str(e)}
        except Exception as e: return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    create_autonomous_world()
    explorer = RUD_Active_Explorer()
    explorer.start()
    print("🚀 Genesis complete. RUD is now inhabiting the space.")
    
    # Keep alive for background mode AND process commands
    print("⏳ Background Mode: Keeping bridge alive & Processing Queue...")
    try:
        while True:
            # Manual Event Loop for Queue Processing
            while not explorer.command_queue.empty():
                try:
                    payload, conn = explorer.command_queue.get_nowait()
                    result = explorer.execute_command(payload)
                    try: 
                        conn.sendall(json.dumps(result).encode('utf-8'))
                    except Exception as e:
                        print(f"Send Error: {e}")
                    finally: 
                        conn.close()
                except queue.Empty:
                    break
                except Exception as e:
                    print(f"Queue Error: {e}")
            
            time.sleep(0.1) # Yield
            
    except KeyboardInterrupt:
        print("🛑 Stopping RUD Bridge.")
