"""
Modeling Proposer - Bridges CAD Analysis and Human Interaction
==============================================================
Role: Translator (Structural Intention)
Function:
  - Consumes JSON from dxf_parser_engine.
  - Generates a human-friendly modeling proposal.
  - Interfaces with AskFirstMiddleware to trigger a HOLD.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

class ModelingProposer:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.proposal_template = (
            "🏛️ **Architectural Modeling Proposal**\n\n"
            "새로운 도면 '{source}'에 대한 분석을 마쳤습니다.\n"
            "다음과 같이 공간 구축을 진행할까요?\n\n"
            "**[분석 요약]**\n"
            "- 도면 유형: {view_type}\n"
            "- 감지된 클러스터: {cluster_count}개\n"
            "- 총 개체 수: {entity_count}개\n\n"
            "**[권장 파라미터 (적분상수 C)]**\n"
            "{parameters}\n\n"
            "**[구축 단계]**\n"
            "{steps}\n\n"
            "위 항목에 대해 승인해 주시면 Blender 모델링을 시작합니다."
        )

    def generate_proposal(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        metadata = parsed_data.get("metadata", {})
        clusters = parsed_data.get("clusters", [])
        estimated = parsed_data.get("estimated_parameters", {})
        
        source_name = Path(metadata.get("source", "unknown")).name
        view_types = [c.get("type") for c in clusters]
        primary_view = "Floor Plan" if "PLAN" in view_types else "Elevation"
        
        total_entities = sum(len(c.get("entities", [])) for c in clusters)
        
        # Use estimated parameters
        t_wall = estimated.get("wall_thickness", 200)
        h_ceil = estimated.get("ceiling_height", 3500)
        
        params = [
            f"- 벽체 두께: {t_wall}mm",
            f"- 층고: {h_ceil}mm",
            "- 스케일: 1:1 (mm단위)"
        ]
        
        steps = [
            "1. 평면도 기반 베이스 슬라브 생성",
            "2. 입면도(Folding) 기반 벽체 및 개구부(창/문) 추출",
            "3. 지붕 및 바닥 마감 작업"
        ]
        
        message = self.proposal_template.format(
            source=source_name,
            view_type=primary_view,
            cluster_count=len(clusters),
            entity_count=total_entities,
            parameters="\n".join(params),
            steps="\n".join(steps)
        )
        
        return {
            "source": source_name,
            "message": message,
            "parameters": {
                "wall_thickness": t_wall,
                "ceiling_height": h_ceil
            }
        }

if __name__ == "__main__":
    # Test
    sample_json = {
        "clusters": [{"type": "PLAN", "entities": [{}, {}]}],
        "metadata": {"source": "test.dxf"}
    }
    proposer = ModelingProposer(Path("."))
    print(proposer.generate_proposal(sample_json)["message"])
