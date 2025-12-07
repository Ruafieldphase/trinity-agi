"""
OBS Live Eye - FSD를 위한 실시간 화면 관찰
==========================================

OBS WebSocket을 통해 현재 화면을 실시간으로 가져옵니다.
정적 스크린샷 대신 OBS가 캡처하는 라이브 화면을 활용합니다.

사용법:
    eye = OBSLiveEye()
    if eye.connect():
        frame = eye.get_current_frame()  # Base64 PNG
        eye.disconnect()
"""

import os
import sys
import base64
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# obsws-python 임포트
try:
    import obsws_python as obsp
    OBS_AVAILABLE = True
except ImportError:
    OBS_AVAILABLE = False
    print("⚠️ obsws-python not installed. Install with: pip install obsws-python")


class OBSLiveEye:
    """FSD를 위한 OBS 실시간 관찰 눈"""
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 4455,
        password: Optional[str] = None,
        timeout: float = 5.0
    ):
        self.host = host
        self.port = port
        self.password = password or os.environ.get("OBS_WS_PASSWORD")
        self.timeout = timeout
        
        self.client = None
        self.logger = logging.getLogger("obs_eye")
        self.logger.setLevel(logging.INFO)
        
        self.screenshot_dir = Path("outputs/obs_live_screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    def connect(self) -> bool:
        """OBS에 연결"""
        if not OBS_AVAILABLE:
            self.logger.error("obsws-python not available")
            return False
        
        try:
            self.client = obsp.ReqClient(
                host=self.host,
                port=self.port,
                password=self.password,
                timeout=self.timeout
            )
            self.logger.info(f"✓ Connected to OBS at {self.host}:{self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to OBS: {e}")
            return False
    
    def disconnect(self):
        """연결 해제"""
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass
            self.client = None
    
    def get_status(self) -> Dict[str, Any]:
        """OBS 상태 조회"""
        if not self.client:
            return {"connected": False}
        
        try:
            stream_status = self.client.get_stream_status()
            record_status = self.client.get_record_status()
            
            return {
                "connected": True,
                "streaming": getattr(stream_status, "output_active", False),
                "recording": getattr(record_status, "output_active", False),
                "timecode": getattr(stream_status, "output_timecode", "00:00:00")
            }
        except Exception as e:
            self.logger.error(f"Status error: {e}")
            return {"connected": True, "error": str(e)}
    
    def get_current_frame(self, source_name: Optional[str] = None) -> Optional[str]:
        """
        현재 화면 프레임 가져오기 (Base64 PNG)
        
        Args:
            source_name: 특정 소스 이름 (None이면 현재 씬)
        
        Returns:
            Base64 인코딩된 PNG 이미지
        """
        if not self.client:
            self.logger.error("Not connected to OBS")
            return None
        
        try:
            # 소스 이름이 없으면 현재 씬 사용
            if source_name is None:
                scene_resp = self.client.get_current_program_scene()
                source_name = getattr(scene_resp, "current_program_scene_name", "장면")
            
            # OBS WebSocket v5 API - 파라미터 이름이 다름
            response = self.client.get_source_screenshot(
                name=source_name,  # source_name이 아니라 name
                img_format="png",  # image_format이 아니라 img_format
                width=1920,
                height=1080,
                quality=-1
            )
            
            # Base64 이미지 추출
            image_data = getattr(response, "image_data", None)
            if image_data:
                # data:image/png;base64,... 형식에서 순수 base64만 추출
                if "," in image_data:
                    image_data = image_data.split(",")[1]
                return image_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Screenshot error: {e}")
            return None
    
    def save_current_frame(self, name: str = "obs_frame") -> Optional[str]:
        """현재 프레임을 파일로 저장"""
        frame_data = self.get_current_frame()
        if not frame_data:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = self.screenshot_dir / filename
        
        try:
            image_bytes = base64.b64decode(frame_data)
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            self.logger.info(f"Saved: {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Save error: {e}")
            return None
    
    def get_scenes(self) -> list:
        """씬 목록 가져오기"""
        if not self.client:
            return []
        
        try:
            resp = self.client.get_scene_list()
            scenes = getattr(resp, "scenes", [])
            return [getattr(s, "scene_name", s) for s in scenes]
        except Exception as e:
            self.logger.error(f"Scene list error: {e}")
            return []
    
    def switch_scene(self, scene_name: str) -> bool:
        """씬 전환"""
        if not self.client:
            return False
        
        try:
            self.client.set_current_program_scene(scene_name=scene_name)
            return True
        except Exception as e:
            self.logger.error(f"Scene switch error: {e}")
            return False


# 싱글톤
_obs_eye = None

def get_obs_eye() -> OBSLiveEye:
    """OBS Eye 싱글톤"""
    global _obs_eye
    if _obs_eye is None:
        _obs_eye = OBSLiveEye()
    return _obs_eye


# 테스트
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== OBS Live Eye Test ===")
    
    eye = OBSLiveEye()
    
    if eye.connect():
        print(f"Status: {eye.get_status()}")
        print(f"Scenes: {eye.get_scenes()}")
        
        # 스크린샷 테스트
        filepath = eye.save_current_frame("test")
        if filepath:
            print(f"✓ Screenshot saved: {filepath}")
        else:
            print("✗ Screenshot failed")
        
        eye.disconnect()
    else:
        print("✗ Could not connect to OBS")
        print("  Make sure OBS is running with WebSocket enabled (port 4455)")
