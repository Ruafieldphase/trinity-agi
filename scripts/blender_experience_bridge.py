import bpy
import json
import socket
import threading
import queue
import time
import os
import mathutils

# -----------------------------------------------------------------------------
# 🌟 RUD 능동 경험 브릿지 (Active Experience Bridge) v1.0
# -----------------------------------------------------------------------------
# 목적: AI(RUD)가 블렌더 공간을 직접 보고, 움직이고, 사건을 기록하게 함.
# -----------------------------------------------------------------------------

class BLENDER_RUD_Bridge:
    def __init__(self, host="127.0.0.1", port=8008):
        self.host = host
        self.port = port
        self.command_queue = queue.Queue()
        self.is_running = False
        self.agent = None
        self.log_file = os.path.join(bpy.path.abspath("//"), "rhythm_experience_log.csv")

    def start(self):
        threading.Thread(target=self.server_thread, daemon=True).start()
        bpy.app.timers.register(self.timer_callback)
        print(f"✅ RUD Active Bridge started on {self.host}:{self.port}")

    def server_thread(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen()
            while True:
                conn, addr = s.accept()
                try:
                    data = conn.recv(1024 * 50) # 50KB buffer for complex commands
                    if data:
                        payload = json.loads(data.decode('utf-8'))
                        self.command_queue.put((payload, conn))
                except Exception as e:
                    print(f"Bridge server error: {e}")
                    conn.close()

    def timer_callback(self):
        while not self.command_queue.empty():
            payload, conn = self.command_queue.get()
            result = self.execute_command(payload)
            try:
                conn.sendall(json.dumps(result).encode('utf-8'))
            except:
                pass
            finally:
                conn.close()
        return 0.1

    def execute_command(self, payload):
        cmd = payload.get("command")
        params = payload.get("params", {})
        
        try:
            if cmd == "ping":
                return {"status": "success", "message": "pong"}
            
            elif cmd == "get_scene_info":
                return {
                    "status": "success", 
                    "objects": [obj.name for obj in bpy.data.objects if obj.type == 'MESH'],
                    "camera": bpy.context.scene.camera.name if bpy.context.scene.camera else None
                }

            elif cmd == "render_viewport":
                filepath = params.get("filepath", "C:/workspace/agi/outputs/renders/viewport_now.png")
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                # Use current viewport if possible, or setup a temp camera
                bpy.context.scene.render.filepath = filepath
                bpy.ops.render.opengl(write_still=True)
                return {"status": "success", "path": filepath}

            elif cmd == "move_agent":
                agent_name = params.get("name", "Rhythm_Agent")
                delta_loc = params.get("delta_location", (0,0,0))
                delta_rot = params.get("delta_rotation", (0,0,0)) # Euler degrees
                
                self.agent = bpy.data.objects.get(agent_name)
                if not self.agent:
                    bpy.ops.mesh.primitive_cube_add(size=0.5)
                    self.agent = bpy.context.active_object
                    self.agent.name = agent_name
                
                # Update pos
                self.agent.location.x += delta_loc[0]
                self.agent.location.y += delta_loc[1]
                self.agent.location.z += delta_loc[2]
                
                # Update rot
                self.agent.rotation_euler.x += (delta_rot[0] * 3.14159 / 180)
                self.agent.rotation_euler.y += (delta_rot[1] * 3.14159 / 180)
                self.agent.rotation_euler.z += (delta_rot[2] * 3.14159 / 180)
                
                # Collision Check (Raycast)
                direction = self.agent.matrix_world.to_quaternion() @ mathutils.Vector((0, 0, -1))
                hit, loc, norm, idx, obj, mw = bpy.context.scene.ray_cast(bpy.context.evaluated_depsgraph_get(), self.agent.location, direction)
                
                return {
                    "status": "success",
                    "location": [self.agent.location.x, self.agent.location.y, self.agent.location.z],
                    "event": "collision" if hit and (loc - self.agent.location).length < 0.5 else "none",
                    "hit_obj": obj.name if obj else None,
                    "hit_dist": (loc - self.agent.location).length if hit else -1
                }

            elif cmd == "execute_python":
                exec(params.get("code", ""))
                return {"status": "success"}

        except Exception as e:
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    bridge = BLENDER_RUD_Bridge()
    bridge.start()
