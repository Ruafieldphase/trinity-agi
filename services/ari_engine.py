
"""
Ari Engine - Adaptive Rhythm Intelligence Core
==============================================
The engine responsible for accumulating learned patterns,
forming the "Sub-conscious" skill layer of the AGI.
"""
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

# Constants
WORKSPACE_ROOT = Path(__file__).parent.parent
MEMORY_DIR = WORKSPACE_ROOT / "memory"
BUFFER_FILE = MEMORY_DIR / "ari_learning_buffer.json"

class TaskType(Enum):
    UI_TASK = "ui_task"
    CLI_TASK = "cli_task"
    COGNITIVE_TASK = "cognitive_task"
    UNKNOWN = "unknown"

@dataclass
class ParsedGoal:
    goal: str
    task_type: TaskType
    steps: List[Dict[str, Any]]
    success: bool = False
    source: str = "unknown"

class AriLearningBuffer:
    """
    In-memory buffer for learned experiences before they are crystallized.
    """
    def __init__(self):
        self.experiences: List[Dict[str, Any]] = []
        self._load_buffer()

    def _load_buffer(self):
        if BUFFER_FILE.exists():
            try:
                with open(BUFFER_FILE, 'r', encoding='utf-8') as f:
                    self.experiences = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load Ari buffer: {e}")
                self.experiences = []
        else:
            self.experiences = []

    def _save_buffer(self):
        try:
            if not MEMORY_DIR.exists():
                MEMORY_DIR.mkdir(parents=True, exist_ok=True)
                
            with open(BUFFER_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.experiences, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save Ari buffer: {e}")

    def add_experience(self, experience: Dict[str, Any]):
        self.experiences.append(experience)
        self._save_buffer()
        self._notify_rhythm_loop(experience)
    
    def _notify_rhythm_loop(self, experience: Dict[str, Any]):
        """리듬 루프에 새 경험 신호 전달"""
        try:
            feeling_file = WORKSPACE_ROOT / "outputs" / "feeling_latest.json"

            def _atomic_write_json(path: Path, obj: Dict[str, Any]) -> None:
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp = path.with_suffix(path.suffix + ".tmp")
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(obj, f, indent=2, ensure_ascii=False)
                os.replace(tmp, path)

            feeling: Dict[str, Any] = {}
            if feeling_file.exists():
                try:
                    with open(feeling_file, "r", encoding="utf-8") as f:
                        feeling = json.load(f)
                except Exception:
                    # 파일이 부분 기록(트렁케이트)된 경우에도 새 이벤트는 잃지 않도록 빈 dict로 계속 진행
                    feeling = {}
            feeling["ari_new_experience"] = {
                "type": experience.get("type", "unknown"),
                "source": experience.get("source", "unknown"),
                "timestamp": experience.get("timestamp", "")
            }
            _atomic_write_json(feeling_file, feeling)
            logger.info(f"Notified rhythm loop: {experience.get('type', 'unknown')}")
        except Exception as e:
            logger.warning(f"Failed to notify rhythm loop: {e}")

class AriEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AriEngine, cls).__new__(cls)
            cls._instance.learning = AriLearningBuffer()
            # Future: Initialize other ARI components here
        return cls._instance

    def get_learned_patterns(self) -> List[Dict[str, Any]]:
        return self.learning.experiences

def get_ari_engine() -> AriEngine:
    return AriEngine()
