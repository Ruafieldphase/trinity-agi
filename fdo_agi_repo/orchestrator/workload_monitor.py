"""
Workload Monitor
작업량 실시간 모니터링
"""
import psutil
import time
from typing import Dict, Optional
from datetime import datetime, timedelta


class WorkloadMonitor:
    """작업량 모니터"""
    
    def __init__(self):
        self.history = []
        self.max_history = 100
        
    def measure(self) -> Dict:
        """현재 작업량 측정"""
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        
        # 작업량 계산 (CPU + Memory 가중 평균)
        workload = (cpu * 0.6) + (memory * 0.4)
        
        measurement = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu,
            "memory_percent": memory,
            "workload_percent": workload,
            "level": self._classify_level(workload)
        }
        
        self._add_to_history(measurement)
        return measurement
    
    def _classify_level(self, workload: float) -> str:
        """작업량 레벨 분류"""
        if workload < 20:
            return "very_low"
        elif workload < 50:
            return "low"
        elif workload < 80:
            return "medium"
        else:
            return "high"
    
    def _add_to_history(self, measurement: Dict):
        """히스토리 추가"""
        self.history.append(measurement)
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def get_average(self, minutes: int = 5) -> float:
        """최근 N분 평균 작업량"""
        if not self.history:
            return 0.0
        
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = [
            h["workload_percent"] 
            for h in self.history 
            if datetime.fromisoformat(h["timestamp"]) > cutoff
        ]
        
        return sum(recent) / len(recent) if recent else 0.0
    
    def is_idle(self, threshold: float = 30.0) -> bool:
        """유휴 상태 체크"""
        current = self.measure()
        return current["workload_percent"] < threshold
