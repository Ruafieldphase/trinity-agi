"""
⚛️ Particle Detector - Discrete Event Detection for Self-Referential AGI

This module detects "particle-like" discrete events in Copilot's activities:
- Significant moments (high importance)
- Anomalies (unusual events)
- Breakthroughs (first-time achievements)
- Critical decisions

Part of Phase 2: Wave-Particle Duality in Self-Reference
"""

from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
import json
from collections import Counter


class SignificantEvent:
    """Represents a detected significant event (particle)"""
    
    def __init__(
        self,
        timestamp: str,
        event_type: str,
        importance: float,
        description: str,
        context: Dict[str, Any],
        reason: str
    ):
        self.timestamp = timestamp
        self.event_type = event_type
        self.importance = importance
        self.description = description
        self.context = context
        self.reason = reason  # Why this is significant
        self.detected_at = datetime.now().isoformat()


class Anomaly:
    """Represents a detected anomaly"""
    
    def __init__(
        self,
        timestamp: str,
        anomaly_type: str,
        deviation_score: float,
        description: str,
        context: Dict[str, Any]
    ):
        self.timestamp = timestamp
        self.anomaly_type = anomaly_type
        self.deviation_score = deviation_score
        self.description = description
        self.context = context
        self.detected_at = datetime.now().isoformat()


class Breakthrough:
    """Represents a breakthrough moment"""
    
    def __init__(
        self,
        timestamp: str,
        achievement: str,
        significance: float,
        description: str,
        context: Dict[str, Any]
    ):
        self.timestamp = timestamp
        self.achievement = achievement
        self.significance = significance
        self.description = description
        self.context = context
        self.detected_at = datetime.now().isoformat()


class ParticleDetector:
    """
    ⚛️ Detects particle-like discrete events in Copilot's behavior
    
    This is the "particle" part of wave-particle duality:
    - Specific, localized events
    - Singular moments of significance
    - Anomalies and outliers
    - Breakthroughs
    
    Complements WaveDetector (patterns over time)
    """
    
    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root
        self.memory_root = workspace_root / "fdo_agi_repo" / "memory"
        # Prefer v2 ledger if present (newer, richer events), fallback to v1.
        ledger_v2 = self.memory_root / "resonance_ledger_v2.jsonl"
        ledger_v1 = self.memory_root / "resonance_ledger.jsonl"
        self.ledger_path = ledger_v2 if ledger_v2.exists() else ledger_v1
        
        # Detection thresholds
        self.high_importance_threshold = 0.7
        self.anomaly_threshold = 2.0  # Standard deviations
        self.breakthrough_threshold = 0.8
        
        # Detected particles (cache)
        self.significant_events: List[SignificantEvent] = []
        self.anomalies: List[Anomaly] = []
        self.breakthroughs: List[Breakthrough] = []
    
    def analyze_particles(
        self,
        lookback_hours: int = 168  # 7 days default
    ) -> Dict[str, Any]:
        """
        Main analysis: detect all particle events
        
        Returns:
            {
                'significant_events': [...],
                'anomalies': [...],
                'breakthroughs': [...],
                'summary': {...}
            }
        """
        # 1. Load recent memories
        memories = self._load_recent_memories(lookback_hours)
        
        if not memories:
            return {
                'significant_events': [],
                'anomalies': [],
                'breakthroughs': [],
                'summary': {'status': 'no_data', 'memory_count': 0}
            }
        
        # 2. Detect significant events
        self.significant_events = self._detect_significant_events(memories)
        
        # 3. Detect anomalies
        self.anomalies = self._detect_anomalies(memories)
        
        # 4. Detect breakthroughs
        self.breakthroughs = self._detect_breakthroughs(memories)
        
        # 5. Generate summary
        summary = self._generate_summary(memories, lookback_hours)
        
        return {
            'significant_events': [self._event_to_dict(e) for e in self.significant_events],
            'anomalies': [self._anomaly_to_dict(a) for a in self.anomalies],
            'breakthroughs': [self._breakthrough_to_dict(b) for b in self.breakthroughs],
            'summary': summary
        }
    
    def _load_recent_memories(self, lookback_hours: int) -> List[Dict[str, Any]]:
        """Load memories from resonance ledger"""
        if not self.ledger_path.exists():
            return []
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        memories = []

        def parse_ts(value: Any) -> datetime | None:
            try:
                if isinstance(value, (int, float)):
                    return datetime.fromtimestamp(float(value), tz=timezone.utc)
                if not isinstance(value, str) or not value:
                    return None
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                return None
        
        try:
            with open(self.ledger_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            entry = json.loads(line)
                        except Exception:
                            continue
                        
                        # Parse timestamp
                        ts = parse_ts(entry.get("timestamp") or entry.get("ts"))
                        if ts and ts >= cutoff:
                            memories.append(entry)
        except Exception as e:
            print(f"⚠️ Error loading memories: {e}")
        
        return memories
    
    def _detect_significant_events(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[SignificantEvent]:
        """Detect high-importance events"""
        events = []
        
        for mem in memories:
            event_type = (
                mem.get("event_type")
                or mem.get("event")
                or mem.get("type")
                or mem.get("action")
                or "unknown"
            )
            # Check importance/priority fields
            importance = (
                mem.get('importance') or
                mem.get('priority') or
                mem.get('severity') or
                0.0
            )
            
            if isinstance(importance, (int, float)) and importance >= self.high_importance_threshold:
                event = SignificantEvent(
                    timestamp=mem.get('timestamp', ''),
                    event_type=event_type,
                    importance=float(importance),
                    description=self._extract_description(mem),
                    context=self._extract_context(mem),
                    reason=f"High importance score: {importance:.2f}"
                )
                events.append(event)
            
            # Check for explicit markers
            if self._has_significance_marker(mem):
                importance = importance if importance > 0 else 0.75
                event = SignificantEvent(
                    timestamp=mem.get('timestamp', ''),
                    event_type=event_type,
                    importance=importance,
                    description=self._extract_description(mem),
                    context=self._extract_context(mem),
                    reason="Contains significance marker"
                )
                events.append(event)
        
        # Sort by importance
        return sorted(events, key=lambda e: e.importance, reverse=True)
    
    def _detect_anomalies(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[Anomaly]:
        """Detect anomalous events (outliers)"""
        anomalies = []
        
        if len(memories) < 10:  # Need enough data for statistics
            return anomalies
        
        # Analyze time gaps (unusual timing)
        timestamps = []
        for mem in memories:
            ts_str = mem.get('timestamp', '')
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    else:
                        ts = ts.astimezone(timezone.utc)
                    timestamps.append((ts, mem))
                except:
                    continue
        
        timestamps.sort(key=lambda x: x[0])
        
        # Calculate gaps between events
        gaps = []
        for i in range(1, len(timestamps)):
            gap = (timestamps[i][0] - timestamps[i-1][0]).total_seconds() / 3600  # hours
            gaps.append(gap)
        
        if gaps:
            import statistics
            mean_gap = statistics.mean(gaps)
            stdev_gap = statistics.stdev(gaps) if len(gaps) > 1 else 0
            
            # Find unusual gaps
            for i, gap in enumerate(gaps):
                if stdev_gap > 0:
                    z_score = abs((gap - mean_gap) / stdev_gap)
                    
                    if z_score >= self.anomaly_threshold:
                        mem = timestamps[i+1][1]
                        anomaly = Anomaly(
                            timestamp=mem.get('timestamp', ''),
                            anomaly_type='timing_anomaly',
                            deviation_score=z_score,
                            description=f"Unusual time gap: {gap:.1f}h (mean: {mean_gap:.1f}h)",
                            context=self._extract_context(mem)
                        )
                        anomalies.append(anomaly)
        
        # Analyze event types (unusual actions)
        event_types = [
            (m.get("event_type") or m.get("event") or m.get("type") or m.get("action") or "unknown")
            for m in memories
        ]
        type_counts = Counter(event_types)
        total = len(event_types)
        
        # Find rare event types
        for event_type, count in type_counts.items():
            frequency = count / total if total > 0 else 0
            
            if frequency < 0.05 and count <= 2:  # Rare event (< 5% and <= 2 times)
                # Find examples
                examples = [
                    m for m in memories
                    if (m.get("event_type") or m.get("event") or m.get("type") or m.get("action") or "unknown") == event_type
                ]
                if examples:
                    mem = examples[0]
                    anomaly = Anomaly(
                        timestamp=mem.get('timestamp', ''),
                        anomaly_type='rare_event',
                        deviation_score=1.0 - frequency,
                        description=f"Rare event type: {event_type} (only {count} times)",
                        context=self._extract_context(mem)
                    )
                    anomalies.append(anomaly)
        
        return sorted(anomalies, key=lambda a: a.deviation_score, reverse=True)
    
    def _detect_breakthroughs(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[Breakthrough]:
        """Detect breakthrough moments (first-time achievements)"""
        breakthroughs = []
        
        # Track first occurrences
        seen_types = set()
        seen_achievements = set()
        
        for mem in memories:
            event_type = (
                mem.get("event_type")
                or mem.get("event")
                or mem.get("type")
                or mem.get("action")
                or "unknown"
            )
            
            # First time event type
            if event_type not in seen_types and event_type != 'unknown':
                seen_types.add(event_type)
                
                # Check if it seems significant
                importance = mem.get('importance', 0.0)
                if isinstance(importance, (int, float)) and importance >= self.breakthrough_threshold:
                    breakthrough = Breakthrough(
                        timestamp=mem.get('timestamp', ''),
                        achievement=f"First time: {event_type}",
                        significance=float(importance),
                        description=self._extract_description(mem),
                        context=self._extract_context(mem)
                    )
                    breakthroughs.append(breakthrough)
            
            # Look for explicit achievement markers
            description = self._extract_description(mem).lower()
            achievement_keywords = ['complete', 'success', 'achievement', 'milestone', 'breakthrough']
            
            if any(kw in description for kw in achievement_keywords):
                achievement_id = f"{event_type}:{description[:50]}"
                
                if achievement_id not in seen_achievements:
                    seen_achievements.add(achievement_id)
                    
                    importance = mem.get('importance', 0.7)
                    breakthrough = Breakthrough(
                        timestamp=mem.get('timestamp', ''),
                        achievement=event_type,
                        significance=float(importance) if isinstance(importance, (int, float)) else 0.7,
                        description=self._extract_description(mem),
                        context=self._extract_context(mem)
                    )
                    breakthroughs.append(breakthrough)
        
        return sorted(breakthroughs, key=lambda b: b.significance, reverse=True)
    
    def _has_significance_marker(self, memory: Dict[str, Any]) -> bool:
        """Check if memory has significance markers"""
        markers = ['critical', 'important', 'milestone', 'breakthrough', 'significant']
        
        # Check in description/message fields
        text_fields = ['description', 'message', 'details', 'summary']
        for field in text_fields:
            if field in memory:
                text = str(memory[field]).lower()
                if any(marker in text for marker in markers):
                    return True
        
        return False
    
    def _extract_description(self, memory: Dict[str, Any]) -> str:
        """Extract human-readable description from memory"""
        # Try different description fields
        for field in ['description', 'message', 'details', 'summary', 'event_type', 'event', 'action', 'type']:
            if field in memory:
                val = memory[field]
                if val and isinstance(val, str):
                    return val
        
        # Fallback to event type
        return (
            memory.get("event_type")
            or memory.get("event")
            or memory.get("type")
            or memory.get("action")
            or "Unknown event"
        )
    
    def _extract_context(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant context from memory"""
        # Don't include heavy fields
        exclude_keys = {'timestamp', 'detected_at', 'raw_data', 'full_details'}
        
        context = {}
        for key, value in memory.items():
            if key not in exclude_keys:
                # Limit size of context values
                if isinstance(value, str) and len(value) > 200:
                    context[key] = value[:200] + '...'
                elif isinstance(value, (dict, list)):
                    context[key] = str(value)[:200] + '...' if len(str(value)) > 200 else value
                else:
                    context[key] = value
        
        return context
    
    def _generate_summary(
        self,
        memories: List[Dict[str, Any]],
        timespan_hours: int
    ) -> Dict[str, Any]:
        """Generate summary of particle analysis"""
        return {
            'status': 'success',
            'memory_count': len(memories),
            'timespan_hours': timespan_hours,
            'particles_detected': {
                'significant_events': len(self.significant_events),
                'anomalies': len(self.anomalies),
                'breakthroughs': len(self.breakthroughs)
            },
            'most_significant': self._get_most_significant(),
            'latest_breakthrough': self._get_latest_breakthrough()
        }
    
    def _get_most_significant(self) -> Optional[str]:
        """Get most significant event description"""
        if self.significant_events:
            return self.significant_events[0].description
        return None
    
    def _get_latest_breakthrough(self) -> Optional[str]:
        """Get latest breakthrough description"""
        if self.breakthroughs:
            # Sort by timestamp
            sorted_bt = sorted(
                self.breakthroughs,
                key=lambda b: b.timestamp,
                reverse=True
            )
            return sorted_bt[0].achievement
        return None
    
    def _event_to_dict(self, event: SignificantEvent) -> Dict[str, Any]:
        """Convert event to dict"""
        return {
            'timestamp': event.timestamp,
            'event_type': event.event_type,
            'importance': event.importance,
            'description': event.description,
            'reason': event.reason,
            'context': event.context,
            'detected_at': event.detected_at
        }
    
    def _anomaly_to_dict(self, anomaly: Anomaly) -> Dict[str, Any]:
        """Convert anomaly to dict"""
        return {
            'timestamp': anomaly.timestamp,
            'anomaly_type': anomaly.anomaly_type,
            'deviation_score': anomaly.deviation_score,
            'description': anomaly.description,
            'context': anomaly.context,
            'detected_at': anomaly.detected_at
        }
    
    def _breakthrough_to_dict(self, breakthrough: Breakthrough) -> Dict[str, Any]:
        """Convert breakthrough to dict"""
        return {
            'timestamp': breakthrough.timestamp,
            'achievement': breakthrough.achievement,
            'significance': breakthrough.significance,
            'description': breakthrough.description,
            'context': breakthrough.context,
            'detected_at': breakthrough.detected_at
        }
    
    def export_particles(self, output_path: Path) -> None:
        """Export detected particles to JSON"""
        result = {
            'significant_events': [self._event_to_dict(e) for e in self.significant_events],
            'anomalies': [self._anomaly_to_dict(a) for a in self.anomalies],
            'breakthroughs': [self._breakthrough_to_dict(b) for b in self.breakthroughs],
            'generated_at': datetime.now().isoformat()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)


# Quick usage example
if __name__ == '__main__':
    from pathlib import Path
    
    workspace = Path(r'c:\workspace\agi')
    detector = ParticleDetector(workspace)
    
    print("⚛️ Detecting particle events...")
    result = detector.analyze_particles(lookback_hours=168)  # 7 days
    
    print(f"\n📊 Analysis Summary:")
    print(f"   Memories analyzed: {result['summary']['memory_count']}")
    print(f"   Significant events: {result['summary']['particles_detected']['significant_events']}")
    print(f"   Anomalies: {result['summary']['particles_detected']['anomalies']}")
    print(f"   Breakthroughs: {result['summary']['particles_detected']['breakthroughs']}")
    
    if result['summary']['most_significant']:
        print(f"\n🌟 Most significant: {result['summary']['most_significant']}")
    
    if result['summary']['latest_breakthrough']:
        print(f"🚀 Latest breakthrough: {result['summary']['latest_breakthrough']}")
