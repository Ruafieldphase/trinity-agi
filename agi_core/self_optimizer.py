"""
Self-Optimizer Engine
=====================
Role: Mimesis Feedback Processor
Function:
  - Analyzes thought_stream_latest.json for ARCH_MODELING_COMPLETE events.
  - Correlates success/failure with rhythm modes.
  - Generates 'tuning' signals for Breathing boundaries.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from agi_core.self_code_analyst import SelfCodeAnalyst
from agi_core.self_patch_generator import SelfPatchGenerator

logger = logging.getLogger("SelfOptimizer")

class SelfOptimizer:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.thought_stream_path = workspace_root / "outputs" / "thought_stream_latest.json"
        self.optimization_log_path = workspace_root / "outputs" / "self_optimization_log.json"
        self.code_analyst = SelfCodeAnalyst(workspace_root)
        self.patch_generator = SelfPatchGenerator(workspace_root)

    def analyze_modeling_performance(self) -> Optional[Dict[str, Any]]:
        """
        최근 모델링 작업의 성과를 분석합니다.
        """
        if not self.thought_stream_path.exists():
            return None

        try:
            with open(self.thought_stream_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            last_record = data.get("last_record", {})
            if last_record.get("event") != "ARCH_MODELING_COMPLETE":
                return None

            # 분석 로직:
            # 여기서는 단순히 성공 여부를 넘어, 파라미터의 '복잡도'나 '수정 빈도'를 미래에 반영할 수 있습니다.
            # 현재는 '성공적으로 완료됨' 자체가 긍정적 강화 신호입니다.
            
            return {
                "source": last_record.get("source"),
                "status": "SUCCESS",
                "parameters": last_record.get("parameters"),
                "timestamp": last_record.get("timestamp")
            }
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return None

    def calculate_tuning_signal(self, performance: Dict[str, Any]) -> Dict[str, float]:
        """
        성과를 바탕으로 경계 조정 계수를 계산합니다.
        """
        # 성향(Propensity): 성공 시에는 더 과감하게(Base 낮춤), 실패 시에는 더 조심스럽게(Base 높임)
        # behavior="higher_is_safer" 기준
        
        tuning = {
            "phase_base_adjustment": 0.0
        }

        if performance["status"] == "SUCCESS":
            # 성공적일 경우, 더 낮은 점수에서도 EXPANSION으로 진입할 수 있도록 Base를 약간 낮춤 (0.5%씩)
            tuning["phase_base_adjustment"] = -0.005 # 200mm -> 199mm or 60 -> 59.7
        else:
            # 실패할 경우, 더 높은 점수가 필요하도록 Base를 높임 (2%씩)
            tuning["phase_base_adjustment"] = 0.02

        return tuning

    def log_optimization(self, tuning: Dict[str, float], performance: Dict[str, Any]):
        """최적화 이력을 기록합니다."""
        history = []
        if self.optimization_log_path.exists():
            try:
                with open(self.optimization_log_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except:
                pass
        
        history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "performance_source": performance.get("source") if performance else "Internal/CodeAnalyst",
            "tuning_applied": tuning
        })

        with open(self.optimization_log_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

    def run_recursive_code_improvement(self) -> List[Dict[str, Any]]:
        """
        [Phase 13.5] 코드를 분석하고 수정을 제안합니다.
        """
        findings = self.code_analyst.scan_logs()
        proposed_patches = []
        
        for finding in findings[:3]: # 상위 3개 에러만 처리
            patch = self.patch_generator.generate_fix(finding)
            if patch:
                proposed_patches.append(patch)
                
        if proposed_patches:
            self.log_optimization({"code_patches_suggested": len(proposed_patches)}, None)
            
        return proposed_patches

if __name__ == "__main__":
    # Test
    opt = SelfOptimizer(Path("c:/workspace/agi"))
    perf = opt.analyze_modeling_performance()
    if perf:
        tuning = opt.calculate_tuning_signal(perf)
        print(f"Proposed Tuning: {tuning}")
        opt.log_optimization(tuning, perf)
