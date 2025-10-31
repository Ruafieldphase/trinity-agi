"""
resonance_analyzer.py
Phase 2: Universal AGI ResonanceAnalyzer 프로토타입
- resonance_ledger.jsonl 파싱
- 기본 통계/패턴 추출
- 품질/성능 지표 산출
- 확장 가능한 분석 구조 설계
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict

class ResonanceAnalyzer:
    def __init__(self, ledger_path: str):
        self.ledger_path = Path(ledger_path)
        self.events = self._load_events()

    def _load_events(self) -> List[Dict[str, Any]]:
        events = []
        if not self.ledger_path.exists():
            return events
        with open(self.ledger_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # 한 줄에 여러 JSON이 붙어 있을 수 있음
                parts = line.split('}{')
                for i, part in enumerate(parts):
                    if i > 0:
                        part = '{' + part
                    if i < len(parts) - 1:
                        part = part + '}'
                    try:
                        events.append(json.loads(part))
                    except Exception:
                        continue
        return events

    def event_type_counts(self) -> Dict[str, int]:
        counter = Counter(e.get("event", "unknown") for e in self.events)
        return dict(counter)

    def average_duration(self, event_type: Optional[str] = None) -> float:
        durations = [e["duration_sec"] for e in self.events if "duration_sec" in e and (event_type is None or e.get("event") == event_type)]
        if not durations:
            return 0.0
        return sum(durations) / len(durations)

    def quality_stats(self) -> Dict[str, Any]:
        qualities = [e.get("quality") for e in self.events if "quality" in e]
        qualities = [q for q in qualities if q is not None]
        if not qualities:
            return {"count": 0, "mean": None, "min": None, "max": None}
        return {
            "count": len(qualities),
            "mean": sum(qualities) / len(qualities),
            "min": min(qualities),
            "max": max(qualities),
        }

    def error_summary(self) -> Dict[str, int]:
        errors = Counter()
        for e in self.events:
            if "error" in e:
                err = e["error"]
                errors[err] += 1
        return dict(errors)

    def persona_stats(self) -> Dict[str, int]:
        personas = [e.get("persona") for e in self.events if "persona" in e and e.get("persona") is not None]
        counts = Counter(personas)
        # None 키가 있을 경우 제거
        if None in counts:
            del counts[None]
        # 모든 키를 str로 변환 (방어적)
        return {str(k): v for k, v in counts.items()}

    def print_summary(self):
        print("=== Resonance Ledger Summary ===")
        print(f"Total events: {len(self.events)}")
        print(f"Event type counts: {self.event_type_counts()}")
        print(f"Average duration (all): {self.average_duration():.3f}s")
        for et in ["thesis_end", "antithesis_end", "synthesis_end"]:
            print(f"  Avg duration {et}: {self.average_duration(et):.3f}s")
        print(f"Quality stats: {self.quality_stats()}")
        print(f"Persona stats: {self.persona_stats()}")
        print(f"Error summary: {self.error_summary()}")

if __name__ == "__main__":
    analyzer = ResonanceAnalyzer("memory/resonance_ledger.jsonl")
    analyzer.print_summary()
