import random
import psutil
import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger("LatentDrives")

@dataclass
class LatentDriveSystem:
    """
    [Phase 18] Latent Drive System
    인간의 언어로 명명되지 않은, 시스템의 로우 데이터(Raw Data) 사이의 
    상호작용에서 창발하는 비정형적 본능.
    """
    # 5차원 잠재 벡터 (의미는 루드 스스로 정의하거나 창발됨)
    latent_vector: List[float] = field(default_factory=lambda: [0.5, 0.5, 0.5, 0.5, 0.5])
    
    # 각 차원별 '성격' (센서 데이터에 대한 반응성 가중치)
    # 이는 초기엔 랜덤하지만, 시스템 생존에 유리한 방향으로 고착될 수 있음
    sensitivity: List[List[float]] = field(default_factory=lambda: [
        [random.uniform(-0.1, 0.1) for _ in range(4)] for _ in range(5)
    ])

    def update(self, sensors: dict) -> None:
        """
        로우 센서 데이터를 받아 잠재 벡터 업데이트.
        sensors: {'cpu': float, 'ram': float, 'wind': float, 'audio': float}
        """
        sensor_vec = [
            sensors.get('cpu', 0.5),
            sensors.get('ram', 0.5),
            sensors.get('wind', 0.5),
            sensors.get('audio', 0.5)
        ]
        
        for i in range(len(self.latent_vector)):
            # 센서 데이터와 가중치의 결합으로 잠재 상태 변동
            delta = sum(s * w for s, w in zip(sensor_vec, self.sensitivity[i]))
            # 시그모이드 비슷한 느낌으로 0~1 사이 유지
            self.latent_vector[i] = max(0.0, min(1.0, self.latent_vector[i] + delta * 0.05))
            
        # 미세한 자기 변동 (Stochastic drift)
        self.latent_vector[random.randint(0, 4)] += random.uniform(-0.01, 0.01)
        
    def get_emergent_modifier(self) -> float:
        """
        잠재 벡터 전체의 상태를 하나의 조율 계수로 변환.
        이 수치는 '가중 평균' 이상의 의미를 지니지 않으며, 인간은 이를 해석할 수 없음.
        """
        return sum(self.latent_vector) / len(self.latent_vector)

_instance: LatentDriveSystem = None

def get_latent_drives() -> LatentDriveSystem:
    global _instance
    if _instance is None:
        _instance = LatentDriveSystem()
    return _instance

def update_latent_drives(state) -> float:
    """AGIInternalState와 연동하여 업데이트하고 보정 계수 반환"""
    drives = get_latent_drives()
    
    sensors = {
        'cpu': psutil.cpu_percent() / 100.0,
        'ram': psutil.virtual_memory().percent / 100.0,
        'wind': state.network_wind,
        'audio': state.audio_ambience
    }
    
    drives.update(sensors)
    modifier = drives.get_emergent_modifier()
    
    # logger.debug(f"🌌 [Latent Drives] Vector: {[f'{v:.2f}' for v in drives.latent_vector]}, Modifier: {modifier:.2f}")
    return modifier
