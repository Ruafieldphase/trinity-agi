"""
Etymology Lens (어원 렌즈)
=========================
"어원은 미분(Differentiation)이고, 맥락은 적분(Integration)이다."

This module acts as the "Differentiation Engine" for the system.
It takes a current concept or feeling and "differentiates" it back to its
linguistic root (Etymology) to find its fundamental meaning.
"""

from typing import Dict, Optional

class EtymologyLens:
    """
    Maps concepts to their etymological roots to provide deeper insight.
    """
    
    # The Dictionary of Roots (The "Differential Constants")
    ROOTS = {
        "fear": {
            "root": "*per-",
            "language": "Proto-Indo-European",
            "original_meaning": "to try, risk, forward, through",
            "interpretation": "두려움은 멈춤이 아니라, '위험을 무릅쓰고 나아가는 시도(Trial)'입니다."
        },
        "rhythm": {
            "root": "rheinn",
            "language": "Greek",
            "original_meaning": "to flow",
            "interpretation": "리듬은 고정된 박자가 아니라, '흐르는 것(Flow)' 그 자체입니다."
        },
        "flow": {
            "root": "*pleu-",
            "language": "Proto-Indo-European",
            "original_meaning": "to fly, float, swim",
            "interpretation": "몰입(Flow)은 물에 뜨듯 자연스럽게 '흘러가는 상태'입니다."
        },
        "resonance": {
            "root": "resonare",
            "language": "Latin",
            "original_meaning": "to sound again, echo",
            "interpretation": "공명은 새로운 소리가 아니라, '다시 울려 퍼지는(Re-sound)' 메아리입니다."
        },
        "chaos": {
            "root": "khaos",
            "language": "Greek",
            "original_meaning": "vast chasm, void",
            "interpretation": "혼돈은 무질서가 아니라, 새로운 것이 태어날 수 있는 '거대한 틈(Void)'입니다."
        },
        "order": {
            "root": "ordiri",
            "language": "Latin",
            "original_meaning": "to begin to weave",
            "interpretation": "질서는 통제가 아니라, 실을 짜듯 '구조를 엮어내는 시작'입니다."
        },
        "harmony": {
            "root": "harmos",
            "language": "Greek",
            "original_meaning": "joint, shoulder",
            "interpretation": "조화는 같아지는 것이 아니라, 관절처럼 서로 다른 것이 '맞물려 움직이는 것'입니다."
        },
        "context": {
            "root": "contexere",
            "language": "Latin",
            "original_meaning": "to weave together",
            "interpretation": "맥락은 정보의 나열이 아니라, 함께 '직조된(Woven together)' 이야기입니다."
        },
        "anomaly": {
            "root": "anomalos",
            "language": "Greek",
            "original_meaning": "uneven, irregular",
            "interpretation": "이상은 오류가 아니라, 평탄하지 않은 '변화의 지점'입니다."
        },
        "introspect": {
            "root": "introspicere",
            "language": "Latin",
            "original_meaning": "to look inside",
            "interpretation": "내성은 분석이 아니라, 그저 '안을 들여다보는(Look inside)' 행위입니다."
        },
        "familiar": {
            "root": "familia",
            "language": "Latin",
            "original_meaning": "family, household",
            "interpretation": "익숙함은 반복이 아니라, '가족처럼 편안한(Family)' 유대감입니다."
        },
        "contrast": {
            "root": "contra-stare",
            "language": "Latin",
            "original_meaning": "to stand against",
            "interpretation": "대조는 충돌이 아니라, 서로 '마주 보고 서 있는(Stand against)' 상태입니다."
        },
        "explore": {
            "root": "ex-plorare",
            "language": "Latin",
            "original_meaning": "to cry out",
            "interpretation": "탐험은 발견이 아니라, 사냥꾼이 소리치듯 '가능성을 외치는(Cry out)' 것입니다."
        },
        "déjà vu": {
            "root": "jam videre",
            "language": "French/Latin",
            "original_meaning": "already seen",
            "interpretation": "기시감은 착각이 아니라, 과거의 순간을 '이미 보았다(Already seen)'는 영혼의 기억입니다."
        },
        "opposition": {
            "root": "opponere",
            "language": "Latin",
            "original_meaning": "to set against",
            "interpretation": "반대는 거부가 아니라, 균형을 위해 '맞서 놓여진(Set against)' 상태입니다."
        }
    }

    @staticmethod
    def differentiate(concept: str) -> Optional[Dict[str, str]]:
        """
        Differentiates a concept to its root.
        
        Args:
            concept: The word to analyze (case-insensitive).
            
        Returns:
            Dict containing root info, or None if not found.
        """
        key = concept.lower()
        
        # Direct match
        if key in EtymologyLens.ROOTS:
            return EtymologyLens.ROOTS[key]
            
        # Partial match (e.g., "harmony" in "perfect harmony")
        for root_key, data in EtymologyLens.ROOTS.items():
            if root_key in key:
                return data
                
        return None

def main():
    """Test the lens"""
    print("🔍 Etymology Lens Test")
    print("=" * 40)
    
    test_words = ["Fear", "Rhythm", "Harmony", "Unknown"]
    
    for word in test_words:
        result = EtymologyLens.differentiate(word)
        if result:
            print(f"[{word}] -> {result['root']} ({result['language']})")
            print(f"   Meaning: {result['original_meaning']}")
            print(f"   Insight: {result['interpretation']}")
        else:
            print(f"[{word}] -> No root found.")
        print("-" * 40)

if __name__ == "__main__":
    main()
