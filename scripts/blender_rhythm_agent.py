import bpy
import bgl
import blf
import mathutils
import csv
import time
import os

# -----------------------------------------------------------------------------
# 📐 리듬 정보이론 기반: 블렌더 리듬 에이전트 스켈레톤 v1.0
# -----------------------------------------------------------------------------
# 목적: 에이전트의 이동과 레이캐스트를 '사건(Event)'으로 기록하여 
#       도면과 공간 간의 리듬 제약을 데이터화함.
# -----------------------------------------------------------------------------

class RHYTHM_OT_AgentSimulator(bpy.types.Operator):
    """리듬 에이전트 시뮬레이터: 이동 및 충돌 사건 기록"""
    bl_idname = "rhythm.agent_simulator"
    bl_label = "Rhythm Agent Simulator"
    
    def __init__(self):
        self._timer = None
        self.agent = None
        self.logs = []
        self.is_running = False
        self.last_pos = None

    def invoke(self, context, event):
        # 1. 에이전트 설정 (선택된 오브젝트 또는 신규 생성)
        if context.active_object:
            self.agent = context.active_object
        else:
            bpy.ops.mesh.primitive_cube_add(size=1)
            self.agent = context.active_object
            self.agent.name = "Rhythm_Agent"

        self.last_pos = self.agent.location.copy()
        
        # 2. 타이머 등록 (실시간 루프)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        
        self.is_running = True
        print(f"--- [Rhythm Agent Started: {self.agent.name}] ---")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC':
            return self.cancel(context)

        if event.type == 'TIMER':
            self.process_rhythm(context)

        return {'PASS_THROUGH'}

    def process_rhythm(self, context):
        """에이전트의 리듬(이동 및 감지) 처리"""
        curr_pos = self.agent.location.copy()
        curr_dir = self.agent.matrix_world.to_quaternion() @ mathutils.Vector((0, 0, -1)) # 전방 벡터 (Blender 기준 수정 가능)

        # 1. 레이캐스트 (시선/감지 사건)
        # 씬의 모든 메쉬 오브젝트와의 충돌 체크
        depsgraph = context.evaluated_depsgraph_get()
        origin = curr_pos
        direction = curr_dir
        
        hit, location, normal, index, object, matrix = context.scene.ray_cast(depsgraph, origin, direction)

        # 2. 사건 기록 (Event Logging)
        event_data = {
            "timestamp": time.time(),
            "pos_x": round(curr_pos.x, 3),
            "pos_y": round(curr_pos.y, 3),
            "pos_z": round(curr_pos.z, 3),
            "is_moving": (curr_pos - self.last_pos).length > 0.01,
            "hit": hit,
            "hit_dist": round((location - origin).length, 3) if hit else -1,
            "hit_obj": object.name if object else "None"
        }

        self.logs.append(event_data)
        self.last_pos = curr_pos

        # 콘솔 출력 (디버깅용)
        if hit and event_data["hit_dist"] < 2.0: # 2미터 이내 접근 시 '사건'으로 강조
            print(f"⚠️ [EVENT] Conflict with {object.name} at distance {event_data['hit_dist']}")

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        self.save_logs()
        print("--- [Rhythm Agent Stopped and Logs Saved] ---")
        return {'CANCELLED'}

    def save_logs(self):
        """기록된 사건 데이터를 CSV로 저장"""
        save_path = os.path.join(bpy.path.abspath("//"), "rhythm_agent_log.csv")
        keys = self.logs[0].keys() if self.logs else []
        
        with open(save_path, 'w', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(self.logs)
        
        print(f"Log saved to: {save_path}")

# -----------------------------------------------------------------------------
# 메뉴/UI UI 등록 (생략 가능, 콘솔에서 호출용)
# -----------------------------------------------------------------------------
def register():
    bpy.utils.register_class(RHYTHM_OT_AgentSimulator)

def unregister():
    bpy.utils.unregister_class(RHYTHM_OT_AgentSimulator)

if __name__ == "__main__":
    register()
    # 즉시 실행 테스트를 원하면 아래 주석 해제 후 블렌더에서 실행
    # bpy.ops.rhythm.agent_simulator('INVOKE_DEFAULT')
