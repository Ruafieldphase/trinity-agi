"""
Self-Expansion Engine package (루빛 설계 스켈레톤)

구성:
- self_acquisition: 외부 신호/데이터 능동 획득
- self_compression: 획득한 정보를 리듬/상태에 압축 통합
- self_tooling: 필요한 도구를 스스로 생성/검증/배포
- pipeline: 세 축을 하나의 주기로 묶는 오케스트레이션

주의: 현재는 스켈레톤이며, 실제 수집/압축/도구생성 로직을
확장하면서 채워넣도록 설계되어 있음.
"""

from .pipeline import SelfExpansionEngine

__all__ = ["SelfExpansionEngine"]
