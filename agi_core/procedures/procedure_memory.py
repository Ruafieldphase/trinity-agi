"""
Procedure Memory
학습된 절차를 파일 기반으로 저장하고 관리

비슷한 절차가 반복되면 frequency를 올리고,
자주 사용되는 절차를 우선순위로 관리
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ProcedureMemory")


class ProcedureMemory:
    """
    절차를 파일 기반으로 저장하고,
    비슷한 절차가 반복되면 frequency를 올리는 구조
    """
    
    def __init__(self, path: Optional[str] = None):
        """
        Args:
            path: 저장 경로 (기본: memory/procedures.json)
        """
        if path is None:
            path = str(Path(__file__).parent.parent.parent / "memory" / "procedures.json")
        self.path = path
        self.procedures: List[Dict[str, Any]] = []
        self._load()
    
    def _load(self) -> None:
        """파일에서 절차 로드"""
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.procedures = data
                    elif isinstance(data, dict) and "procedures" in data:
                        self.procedures = data["procedures"]
                    else:
                        self.procedures = []
                logger.info(f"Loaded {len(self.procedures)} procedures from {self.path}")
            except Exception as e:
                logger.warning(f"Failed to load procedures: {e}")
                self.procedures = []
        else:
            self.procedures = []
    
    def _save(self) -> None:
        """파일에 절차 저장"""
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.procedures, f, ensure_ascii=False, indent=2, default=str)
            logger.debug(f"Saved {len(self.procedures)} procedures to {self.path}")
        except Exception as e:
            logger.error(f"Failed to save procedures: {e}")
    
    def save(self, procedure: Dict[str, Any]) -> None:
        """
        절차 저장 또는 업데이트
        
        기존에 같은 이름의 절차가 있으면 frequency 증가,
        없으면 새로 추가
        """
        existing = self.match_existing(procedure)
        now = datetime.now(timezone.utc).isoformat()
        
        if existing:
            # 기존 절차 업데이트
            existing["frequency"] = existing.get("frequency", 1) + 1
            existing["last_used"] = now
            existing["confidence"] = max(
                existing.get("confidence", 0.0),
                procedure.get("confidence", 0.0)
            )
            # 스텝 정보는 가장 최근 것으로 업데이트 (선택적)
            if procedure.get("duration_sec"):
                # 평균 duration 계산
                prev_dur = existing.get("avg_duration_sec", 0)
                freq = existing["frequency"]
                existing["avg_duration_sec"] = round(
                    (prev_dur * (freq - 1) + procedure["duration_sec"]) / freq, 2
                )
            
            logger.info(f"Updated procedure '{existing['procedure_name']}' (freq: {existing['frequency']})")
        else:
            # 새 절차 추가
            procedure["frequency"] = 1
            procedure["first_seen"] = now
            procedure["last_used"] = now
            if procedure.get("duration_sec"):
                procedure["avg_duration_sec"] = procedure["duration_sec"]
            self.procedures.append(procedure)
            logger.info(f"Saved new procedure '{procedure.get('procedure_name')}'")
        
        self._save()
    
    def match_existing(self, proc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        기존 절차와 매칭
        
        현재는 procedure_name 기준으로 매칭 (추후 유사도 기반 확장 가능)
        """
        name = proc.get("procedure_name")
        if not name:
            return None
        
        for p in self.procedures:
            if p.get("procedure_name") == name:
                return p
        return None
    
    def get_frequent(self, top_k: int = 10) -> List[Dict[str, Any]]:
        """자주 사용되는 절차 상위 k개 반환"""
        sorted_procs = sorted(
            self.procedures,
            key=lambda p: p.get("frequency", 0),
            reverse=True
        )
        return sorted_procs[:top_k]
    
    def get_recent(self, top_k: int = 10) -> List[Dict[str, Any]]:
        """최근 사용된 절차 상위 k개 반환"""
        sorted_procs = sorted(
            self.procedures,
            key=lambda p: p.get("last_used", ""),
            reverse=True
        )
        return sorted_procs[:top_k]
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """이름에 query가 포함된 절차 검색"""
        query_lower = query.lower()
        return [
            p for p in self.procedures
            if query_lower in p.get("procedure_name", "").lower()
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """메모리 통계"""
        if not self.procedures:
            return {"total": 0, "total_frequency": 0}
        
        return {
            "total": len(self.procedures),
            "total_frequency": sum(p.get("frequency", 0) for p in self.procedures),
            "avg_confidence": sum(p.get("confidence", 0) for p in self.procedures) / len(self.procedures),
            "top_procedure": max(self.procedures, key=lambda p: p.get("frequency", 0)).get("procedure_name"),
        }
    
    def clear(self) -> None:
        """모든 절차 삭제"""
        self.procedures = []
        self._save()
    
    def __len__(self) -> int:
        return len(self.procedures)
