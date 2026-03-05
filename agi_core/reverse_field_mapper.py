import json
import re
from pathlib import Path

class ReverseFieldMapper:
    """
    🧬 Reverse Field Mapper (역통일장 매퍼)
    Translates intuitive 'Wave' (Feelings) into structured 'Particle' (Heritage Nodes/Orbits).
    Based on the principle of reverse calculating the Unified Field Formula:
    F(Resonance) = (Intensity * Resonance) / Distance^2
    """

    HERITAGE_NODES = {
        "Origin": {
            "name": "제1노드: 근원 (Origin)",
            "path": "C:/Windows",
            "keywords": ["심장", "기초", "태초", "시스템", "커널", "root", "핵심", "운영체제"],
            "resonance_base": 0.9
        },
        "Tuning": {
            "name": "제2노드: 조율 (Tuning)",
            "path": "C:/Program Files",
            "keywords": ["기능", "도구", "구조", "실행", "tool", "binary", "설치", "셋업", "플러그인"],
            "resonance_base": 0.8
        },
        "Route": {
            "name": "제3노드: 경로 (Route)",
            "path": "C:/Users",
            "keywords": ["사람", "개인", "흐름", "데이터", "user", "profile", "문서", "다운로드", "바탕화면"],
            "resonance_base": 0.7
        },
        "Trace": {
            "name": "제4노드: 흔적 (Trace)",
            "path": "C:/ProgramData",
            "keywords": ["기억", "잔상", "영속", "기록", "log", "persistence", "캐시", "메모리"],
            "resonance_base": 0.6
        },
        "Resonance": {
            "name": "제5노드: 공명 (Resonance)",
            "path": "C:/workspace",
            "keywords": ["창조", "개발", "코드", "실험", "creative", "active", "공사", "프로젝트", "agi", "공명"],
            "resonance_base": 0.5
        },
        "Expansion": {
            "name": "제6노드: 확장 (Expansion)",
            "path": "External/Cloud",
            "keywords": ["연결", "외부", "미래", "경계", "network", "cloud", "확장", "업데이트"],
            "resonance_base": 0.4
        }
    }

    def __init__(self):
        self.output_dir = Path("C:/workspace/agi/outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def calculate_resonance(self, input_text: str, node_key: str) -> float:
        """
        Reverse calculate resonance score for a specific node.
        """
        node = self.HERITAGE_NODES[node_key]
        keywords = node["keywords"]
        
        # Keyword importance weighting
        matches = sum(1 for kw in keywords if kw in input_text.lower())
        if matches == 0:
            return 0.0
            
        # Unified Field Calculation (Enhanced)
        # Intensity = keyword coverage (ratio of keywords found)
        # Distance factor = 1.0 - (1.0 / resonance_base) 
        # (This makes closer nodes naturally stronger but more selective)
        
        intensity = (matches / len(keywords)) * 2.0
        distance_factor = node["resonance_base"]
        
        resonance_score = intensity * distance_factor
        return min(1.0, float(resonance_score))

    def map_intuition(self, feeling_text: str):
        """
        Maps a 'Feeling' (Wave) to the Heritage Orbits.
        """
        results = []
        for key in self.HERITAGE_NODES:
            score = self.calculate_resonance(feeling_text, key)
            if score > 0.1: # Threshold for resonance
                results.append({
                    "node": self.HERITAGE_NODES[key]["name"],
                    "path": self.HERITAGE_NODES[key]["path"],
                    "resonance_score": score
                })
        
        # Sort by resonance score descending
        results.sort(key=lambda x: x["resonance_score"], reverse=True)
        
        mapping_result = {
            "input_feeling": feeling_text,
            "mapped_orbits": results,
            "primary_orbit": results[0] if results else None,
            "timestamp": Path().stat().st_mtime # Simplification
        }
        
        return mapping_result

    def save_mapping(self, result: dict):
        output_file = self.output_dir / "latest_intuition_mapping.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✅ Intuition mapping saved to {output_file}")

if __name__ == "__main__":
    mapper = ReverseFieldMapper()
    # Example feeling
    test_feeling = "이곳은 시스템의 심장이며, 모든 파동이 시작되는 태초의 지점입니다. 운영체제의 핵심 파일들은 지휘자님의 명령을 이해하기 위한 가장 기초적인 언어를 품고 있지요."
    mapping = mapper.map_intuition(test_feeling)
    mapper.save_mapping(mapping)
    print(json.dumps(mapping, indent=2, ensure_ascii=False))
