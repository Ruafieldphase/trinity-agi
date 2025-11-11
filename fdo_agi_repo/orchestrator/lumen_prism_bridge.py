"""
orchestrator/lumen_prism_bridge.py

루멘의 시선(Lumen's Gaze)을 비노체 프리즘(Binoche Prism)을 통해
구조 전체에 지속적인 울림(Resonance)으로 변환하는 브리지.

루멘 → 비노체(프리즘) → 구조 전체 울림
- 루멘의 관찰과 직관을 비노체의 패턴 필터로 굴절
- 비노체의 선호도와 의사결정 패턴으로 루멘 신호 증폭
- 지속적 울림을 위한 페르소나 기반 공명 유지
"""
from __future__ import annotations
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import datetime
from collections import defaultdict
import sys

# Add repo root to path
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

try:
    from fdo_agi_repo.universal.resonance import ResonanceStore, ResonanceEvent
    from fdo_agi_repo.orchestrator.resonance_bridge import init_resonance_store
except ModuleNotFoundError:
    from universal.resonance import ResonanceStore, ResonanceEvent  # type: ignore
    from orchestrator.resonance_bridge import init_resonance_store  # type: ignore


class LumenPrismBridge:
    """루멘의 시선을 비노체 프리즘으로 변환하여 구조 전체에 울림 생성."""
    
    def __init__(
        self,
        persona_path: Optional[Path] = None,
        lumen_latency_path: Optional[Path] = None,
        resonance_store: Optional[ResonanceStore] = None
    ):
        self.persona_path = persona_path or Path("fdo_agi_repo/outputs/binoche_persona.json")
        self.lumen_latency_path = lumen_latency_path or Path("outputs/lumen_latency_latest.json")
        
        # Initialize resonance store if not provided
        if resonance_store is None:
            init_resonance_store()
            # Use the standard resonance ledger path
            resonance_store_path = Path("fdo_agi_repo/memory/resonance_ledger.jsonl")
            resonance_store = ResonanceStore(resonance_store_path)
        
        self.resonance_store = resonance_store
        
        self.persona: Dict[str, Any] = {}
        self.lumen_data: Dict[str, Any] = {}
        self.prism_cache: List[Dict[str, Any]] = []
        
        self._load_persona()
        self._load_lumen_data()
    
    def _load_persona(self):
        """비노체 페르소나 로드."""
        if self.persona_path.exists():
            try:
                with open(self.persona_path, 'r', encoding='utf-8') as f:
                    self.persona = json.load(f)
                print(f"[LumenPrism] Loaded Binoche persona from {self.persona_path}")
            except Exception as e:
                print(f"[LumenPrism] Failed to load persona: {e}")
        else:
            print(f"[LumenPrism] No persona found at {self.persona_path}, using empty persona")
    
    def _load_lumen_data(self):
        """루멘 레이턴시 데이터 로드."""
        if self.lumen_latency_path.exists():
            try:
                with open(self.lumen_latency_path, 'r', encoding='utf-8') as f:
                    self.lumen_data = json.load(f)
                print(f"[LumenPrism] Loaded Lumen data from {self.lumen_latency_path}")
            except Exception as e:
                print(f"[LumenPrism] Failed to load Lumen data: {e}")
        else:
            print(f"[LumenPrism] No Lumen data found at {self.lumen_latency_path}")
    
    def refract_lumen_gaze(self, lumen_signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        루멘의 시선을 비노체 프리즘으로 굴절.
        
        Args:
            lumen_signal: 루멘의 관찰 신호
                - latency_ms: 레이턴시
                - endpoint: 엔드포인트
                - success: 성공 여부
                - timestamp: 타임스탬프
        
        Returns:
            굴절된 프리즘 신호 (비노체 패턴 반영)
        """
        prism_signal = {
            "original_lumen": lumen_signal,
            "refracted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "prism_filters": {},
            "resonance_amplification": 1.0,
            "binoche_interpretation": {}
        }
        
        # 1. 비노체 품질 기준 적용
        latency = lumen_signal.get("latency_ms", 0)
        success = lumen_signal.get("success", False)
        
        quality_threshold = self.persona.get("quality_standards", {}).get("min_quality", 0.8)
        prism_signal["prism_filters"]["quality_gate"] = success and latency < 5000
        
        # 2. 비노체 선호도로 증폭도 결정
        endpoint = lumen_signal.get("endpoint", "unknown")
        tech_prefs = self.persona.get("work_preferences", {}).get("preferred_technologies", [])
        
        # 비노체가 선호하는 기술 스택과 관련 있으면 증폭
        amplification = 1.0
        for tech in tech_prefs:
            if tech.lower() in endpoint.lower():
                amplification += 0.5
        
        prism_signal["resonance_amplification"] = amplification
        
        # 3. 비노체 의사결정 패턴으로 해석
        decision_patterns = self.persona.get("decision_patterns", {})
        approval_signals = decision_patterns.get("approval_signals", {})
        
        interpretation = {
            "quality_meets_standard": prism_signal["prism_filters"]["quality_gate"],
            "aligns_with_preferences": amplification > 1.0,
            "estimated_approval_rate": approval_signals.get("avg_quality", 0.0)
        }
        prism_signal["binoche_interpretation"] = interpretation
        
        return prism_signal
    
    def generate_continuous_resonance(
        self,
        prism_signal: Dict[str, Any],
        resonance_type: str = "lumen_prism_gaze"
    ) -> ResonanceEvent:
        """
        프리즘 신호를 지속적 울림으로 변환.
        
        Args:
            prism_signal: 굴절된 프리즘 신호
            resonance_type: 울림 유형
        
        Returns:
            ResonanceEvent 객체
        """
        # Task ID와 resonance key 생성
        task_id = prism_signal.get("task_id", f"lumen_prism_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
        resonance_key = prism_signal.get("resonance_key", "lumen:prism:gaze")
        
        event = ResonanceEvent(
            task_id=task_id,
            resonance_key=resonance_key,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            metrics={
                "amplification": prism_signal.get("resonance_amplification", 1.0),
                "latency_ms": prism_signal.get("latency_ms", 0.0),
                "quality_gate": 1.0 if prism_signal.get("prism_filters", {}).get("quality_gate", False) else 0.0
            },
            tags={
                "event_type": resonance_type,
                "prism_signal": prism_signal.get("refracted", {}),
                "binoche_interpretation": prism_signal.get("binoche_interpretation", {})
            }
        )
        
        # Resonance Store에 기록하여 구조 전체에 전파
        if self.resonance_store:
            print(f"[LumenPrism] 📝 Writing resonance event to ledger: {task_id}")
            self.resonance_store.append(event)
            print(f"[LumenPrism] ✅ Resonance event written")
        else:
            print("[LumenPrism] ⚠️ WARNING: resonance_store is None, event not recorded!")
        
        return event
    
    def process_lumen_observation(self, lumen_signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        루멘 관찰 → 비노체 프리즘 → 구조 울림 전체 파이프라인.
        
        Args:
            lumen_signal: 루멘의 관찰 신호
        
        Returns:
            처리 결과 요약
        """
        # 1. 프리즘으로 굴절
        prism_signal = self.refract_lumen_gaze(lumen_signal)
        
        # 2. 지속적 울림 생성
        resonance_event = self.generate_continuous_resonance(prism_signal)
        
        # 3. 캐시에 저장 (최근 N개 유지)
        self.prism_cache.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "lumen": lumen_signal,
            "prism": prism_signal,
            "resonance_task_id": resonance_event.task_id
        })
        
        # 캐시 크기 제한 (최근 100개)
        if len(self.prism_cache) > 100:
            self.prism_cache = self.prism_cache[-100:]
        
        return {
            "status": "success",
            "lumen_signal": lumen_signal,
            "prism_refraction": prism_signal,
            "resonance_propagated": True,
            "amplification": prism_signal.get("resonance_amplification", 1.0)
        }
    
    def get_resonance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        최근 N시간의 루멘-프리즘 울림 요약.
        
        Args:
            hours: 조회할 시간 범위
        
        Returns:
            울림 요약 통계
        """
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
        
        # prism_cache에서 최근 이벤트 수집
        recent_events = []
        for item in self.prism_cache:
            try:
                ts_str = item.get("timestamp", "1970-01-01T00:00:00+00:00")
                ts = datetime.datetime.fromisoformat(ts_str)
                # Ensure timezone aware comparison
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=datetime.timezone.utc)
                if ts >= cutoff:
                    recent_events.append(item)
            except Exception:
                continue
        
        total_count = len(recent_events)
        amplifications = [e.get("prism_signal", {}).get("resonance_amplification", 1.0) for e in recent_events]
        quality_gates = [e.get("prism_signal", {}).get("prism_filters", {}).get("quality_gate", False) for e in recent_events]
        
        return {
            "time_range_hours": hours,
            "total_prism_events": total_count,
            "avg_amplification": sum(amplifications) / len(amplifications) if amplifications else 0.0,
            "quality_pass_rate": sum(quality_gates) / len(quality_gates) if quality_gates else 0.0,
            "cache_size": len(self.prism_cache),
            "persona_loaded": bool(self.persona),
            "lumen_data_loaded": bool(self.lumen_data)
        }
    
    def save_prism_cache(self, output_path: Optional[Path] = None):
        """프리즘 캐시를 파일로 저장."""
        if output_path is None:
            output_path = Path("outputs/lumen_prism_cache.json")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "cache": self.prism_cache,
                "summary": self.get_resonance_summary(24),
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"[LumenPrism] Prism cache saved to {output_path}")


# Global instance
_LUMEN_PRISM_BRIDGE: Optional[LumenPrismBridge] = None


def get_lumen_prism_bridge() -> LumenPrismBridge:
    """Get or create global LumenPrismBridge instance."""
    global _LUMEN_PRISM_BRIDGE
    if _LUMEN_PRISM_BRIDGE is None:
        _LUMEN_PRISM_BRIDGE = LumenPrismBridge()
    return _LUMEN_PRISM_BRIDGE


def refract_lumen_to_resonance(lumen_signal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function: 루멘 신호를 프리즘으로 굴절하여 울림 생성.
    
    Args:
        lumen_signal: 루멘의 관찰 신호
    
    Returns:
        처리 결과
    """
    bridge = get_lumen_prism_bridge()
    return bridge.process_lumen_observation(lumen_signal)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Lumen Prism Bridge - 루멘 시선을 비노체 프리즘으로 울림 생성")
    parser.add_argument("--persona", type=Path, help="Binoche persona JSON path")
    parser.add_argument("--lumen", type=Path, help="Lumen latency data path")
    parser.add_argument("--test-signal", action="store_true", help="Generate test signal")
    parser.add_argument("--process-observations", action="store_true", help="Process all observations from lumen data")
    parser.add_argument("--summary", type=int, default=24, help="Show summary for N hours")
    
    args = parser.parse_args()
    
    bridge = LumenPrismBridge(
        persona_path=args.persona,
        lumen_latency_path=args.lumen
    )
    
    if args.test_signal:
        # 테스트 신호 생성
        test_signal = {
            "latency_ms": 1234.5,
            "endpoint": "/api/v2/recommend/personalized",
            "success": True,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        print("\n[LumenPrism] Processing test signal...")
        result = bridge.process_lumen_observation(test_signal)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        bridge.save_prism_cache()
    
    if args.process_observations and bridge.lumen_data:
        # 루멘 데이터의 모든 관찰 처리
        observations = bridge.lumen_data.get("observations", [])
        print(f"\n[LumenPrism] Processing {len(observations)} observations...")
        
        for obs in observations:
            result = bridge.process_lumen_observation(obs)
            print(f"  ✓ Processed: {obs.get('endpoint', 'unknown')} - {obs.get('latency_ms', 0)}ms")
        
        bridge.save_prism_cache()
        print(f"\n[LumenPrism] ✅ {len(observations)} observations processed and cached")
    
    # 요약 출력
    print("\n[LumenPrism] Resonance Summary:")
    summary = bridge.get_resonance_summary(hours=args.summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
