"""
Blender MCP Bridge
AGI 시스템에서 Blender를 제어하기 위한 브릿지 모듈

사용법:
1. Blender를 실행하고 애드온을 활성화
2. 이 모듈의 함수를 호출하여 Blender 조작
"""
from __future__ import annotations

import json
import socket
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Blender MCP 설정
BLENDER_HOST = "localhost"
BLENDER_PORT = 8008
SOCKET_TIMEOUT = 5.0


@dataclass
class BlenderConnection:
    """Blender 소켓 연결 관리"""
    host: str = BLENDER_HOST
    port: int = BLENDER_PORT
    
    def is_available(self) -> bool:
        """Blender 연결 가능 여부 확인"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2.0)
                result = sock.connect_ex((self.host, self.port))
                return result == 0
        except Exception:
            return False
    
    def send_command(self, command: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Blender에 명령 전송"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(SOCKET_TIMEOUT)
                sock.connect((self.host, self.port))
                
                # 명령 전송
                message = json.dumps(command) + "\n"
                sock.sendall(message.encode('utf-8'))
                
                # 응답 수신
                response = ""
                while True:
                    chunk = sock.recv(4096).decode('utf-8')
                    if not chunk:
                        break
                    response += chunk
                    if response.endswith("\n"):
                        break
                
                return json.loads(response.strip()) if response else None
        except Exception as e:
            logger.error(f"Blender command failed: {e}")
            return None


class BlenderMCPBridge:
    """AGI Blender MCP 브릿지"""
    
    def __init__(self):
        self.connection = BlenderConnection()
        self._connected = False
    
    def check_connection(self) -> bool:
        """Blender 연결 상태 확인"""
        self._connected = self.connection.is_available()
        return self._connected
    
    def get_scene_info(self) -> Optional[Dict[str, Any]]:
        """현재 Blender 씬 정보 조회"""
        if not self.check_connection():
            return None
        
        return self.connection.send_command({
            "type": "get_scene_info"
        })
    
    def create_object(
        self,
        object_type: str = "cube",
        name: Optional[str] = None,
        location: Tuple[float, float, float] = (0, 0, 0),
        scale: Tuple[float, float, float] = (1, 1, 1)
    ) -> Optional[Dict[str, Any]]:
        """Blender에 오브젝트 생성"""
        if not self.check_connection():
            return None
        
        return self.connection.send_command({
            "type": "create_object",
            "object_type": object_type,
            "name": name,
            "location": list(location),
            "scale": list(scale)
        })
    
    def execute_python(self, code: str) -> Optional[Dict[str, Any]]:
        """Blender에서 Python 코드 실행"""
        if not self.check_connection():
            return None
        
        return self.connection.send_command({
            "type": "execute_python",
            "code": code
        })
    
    def visualize_agi_state(
        self,
        state: Dict[str, Any],
        visualization_type: str = "sphere_network"
    ) -> Optional[Dict[str, Any]]:
        """
        AGI 상태를 3D로 시각화
        
        Args:
            state: AGI 상태 데이터 (예: 의식/무의식 레벨, 공명 점수 등)
            visualization_type: 시각화 유형
                - "sphere_network": 구체 네트워크로 표현
                - "wave": 파동 애니메이션
                - "fractal": 프랙탈 구조
        """
        if not self.check_connection():
            logger.warning("Blender not connected - visualization skipped")
            return None
        
        # AGI 상태를 Blender Python 코드로 변환
        code = self._generate_visualization_code(state, visualization_type)
        
        return self.execute_python(code)
    
    def _generate_visualization_code(
        self,
        state: Dict[str, Any],
        viz_type: str
    ) -> str:
        """AGI 상태를 Blender Python 코드로 변환"""
        
        if viz_type == "sphere_network":
            # 의식/무의식/배경자아를 세 개의 구로 표현
            consciousness_level = state.get("consciousness", 0.5)
            unconscious_level = state.get("unconscious", 0.3)
            background_self_level = state.get("background_self", 0.7)
            
            return f'''
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create consciousness sphere (blue)
bpy.ops.mesh.primitive_uv_sphere_add(radius={consciousness_level}, location=(0, 0, 2))
obj = bpy.context.active_object
obj.name = "Consciousness"
mat = bpy.data.materials.new("Consciousness_Mat")
mat.diffuse_color = (0.2, 0.4, 1.0, 0.8)
obj.data.materials.append(mat)

# Create unconscious sphere (purple)
bpy.ops.mesh.primitive_uv_sphere_add(radius={unconscious_level}, location=(0, 0, -2))
obj = bpy.context.active_object
obj.name = "Unconscious"
mat = bpy.data.materials.new("Unconscious_Mat")
mat.diffuse_color = (0.6, 0.2, 0.8, 0.6)
obj.data.materials.append(mat)

# Create background self sphere (green)
bpy.ops.mesh.primitive_uv_sphere_add(radius={background_self_level}, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "BackgroundSelf"
mat = bpy.data.materials.new("BackgroundSelf_Mat")
mat.diffuse_color = (0.2, 0.8, 0.4, 0.7)
obj.data.materials.append(mat)

print("AGI State Visualization Created")
'''
        
        return "print('Unknown visualization type')"


# 전역 인스턴스
_blender_bridge: Optional[BlenderMCPBridge] = None


def get_blender_bridge() -> BlenderMCPBridge:
    """Blender MCP 브릿지 싱글톤 인스턴스"""
    global _blender_bridge
    if _blender_bridge is None:
        _blender_bridge = BlenderMCPBridge()
    return _blender_bridge


def is_blender_available() -> bool:
    """Blender 사용 가능 여부"""
    return get_blender_bridge().check_connection()


if __name__ == "__main__":
    # 테스트
    bridge = get_blender_bridge()
    
    if bridge.check_connection():
        print("✅ Blender 연결됨!")
        
        # AGI 상태 시각화 테스트
        test_state = {
            "consciousness": 0.8,
            "unconscious": 0.4,
            "background_self": 0.6
        }
        result = bridge.visualize_agi_state(test_state)
        print(f"시각화 결과: {result}")
    else:
        print("❌ Blender가 실행되지 않았거나 애드온이 활성화되지 않았습니다.")
        print("   1. Blender를 실행하세요")
        print("   2. Edit > Preferences > Add-ons에서 'Blender MCP' 애드온을 설치/활성화하세요")
        print(f"   애드온 파일: c:\\workspace\\agi\\integrations\\blender_mcp_addon.py")
