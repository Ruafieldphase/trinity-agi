"""
🌊 Wave Detector - Pattern & Rhythm Detection for Self-Referential AGI

This module detects "wave-like" patterns in Copilot's activities:
- Temporal patterns (daily/weekly rhythms)
- Behavioral patterns (recurring actions)
- Trend detection (gradual changes)

Part of Phase 2: Wave-Particle Duality in Self-Reference
"""

from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
from collections import defaultdict, Counter


class TemporalPattern:
    """Represents a detected temporal pattern (wave)"""
    
    def __init__(
        self,
        pattern_type: str,
        frequency: str,
        strength: float,
        description: str,
        examples: List[Dict[str, Any]]
    ):
        self.pattern_type = pattern_type  # 'daily', 'weekly', 'monthly'
        self.frequency = frequency  # '08:00-09:00', 'Monday', etc.
        self.strength = strength  # 0.0 to 1.0
        self.description = description
        self.examples = examples
        self.detected_at = datetime.now().isoformat()


class BehaviorPattern:
    """Represents a detected behavioral pattern"""
    
    def __init__(
        self,
        action: str,
        frequency_count: int,
        typical_context: Dict[str, Any],
        strength: float
    ):
        self.action = action
        self.frequency_count = frequency_count
        self.typical_context = typical_context
        self.strength = strength
        self.detected_at = datetime.now().isoformat()


class Trend:
    """Represents a detected trend (long-term wave)"""
    
    def __init__(
        self,
        metric: str,
        direction: str,  # 'increasing', 'decreasing', 'stable'
        magnitude: float,
        timespan_hours: int,
        description: str
    ):
        self.metric = metric
        self.direction = direction
        self.magnitude = magnitude
        self.timespan_hours = timespan_hours
        self.description = description
        self.detected_at = datetime.now().isoformat()


class WaveDetector:
    """
    🌊 Detects wave-like patterns in Copilot's behavior
    
    This is the "wave" part of wave-particle duality:
    - Patterns that emerge over time
    - Rhythms and cycles
    - Gradual trends
    
    Complements ParticleDetector (discrete events)
    """
    
    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root
        self.memory_root = workspace_root / "fdo_agi_repo" / "memory"
        self.ledger_path = self.memory_root / "resonance_ledger.jsonl"
        
        # Pattern detection parameters
        self.min_pattern_occurrences = 3  # Minimum to consider it a pattern
        self.min_pattern_strength = 0.3  # Minimum strength to report
        
        # Detected patterns (cache)
        self.temporal_patterns: List[TemporalPattern] = []
        self.behavior_patterns: List[BehaviorPattern] = []
        self.trends: List[Trend] = []
    
    def analyze_patterns(
        self,
        lookback_hours: int = 168  # 7 days default
    ) -> Dict[str, Any]:
        """
        Main analysis: detect all wave patterns
        
        Returns:
            {
                'temporal_patterns': [...],
                'behavior_patterns': [...],
                'trends': [...],
                'summary': {...}
            }
        """
        # 1. Load recent memories
        memories = self._load_recent_memories(lookback_hours)
        
        if not memories:
            return {
                'temporal_patterns': [],
                'behavior_patterns': [],
                'trends': [],
                'summary': {'status': 'no_data', 'memory_count': 0}
            }
        
        # 2. Detect temporal patterns
        self.temporal_patterns = self._detect_temporal_patterns(memories)
        
        # 3. Detect behavioral patterns
        self.behavior_patterns = self._detect_behavior_patterns(memories)
        
        # 4. Detect trends
        self.trends = self._detect_trends(memories, lookback_hours)
        
        # 5. Generate summary
        summary = self._generate_summary(memories, lookback_hours)
        
        return {
            'temporal_patterns': [self._pattern_to_dict(p) for p in self.temporal_patterns],
            'behavior_patterns': [self._pattern_to_dict(p) for p in self.behavior_patterns],
            'trends': [self._trend_to_dict(t) for t in self.trends],
            'summary': summary
        }
    
    def _load_recent_memories(self, lookback_hours: int) -> List[Dict[str, Any]]:
        """Load memories from resonance ledger"""
        if not self.ledger_path.exists():
            return []
        
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        memories = []
        
        try:
            with open(self.ledger_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        
                        # Parse timestamp
                        ts_str = entry.get('timestamp', '')
                        if ts_str:
                            try:
                                ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                                if ts >= cutoff:
                                    memories.append(entry)
                            except:
                                continue
        except Exception as e:
            print(f"⚠️ Error loading memories: {e}")
        
        return memories
    
    def _detect_temporal_patterns(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[TemporalPattern]:
        """Detect time-based patterns (when things happen)"""
        patterns = []
        
        # Group by hour of day
        hour_activities = defaultdict(list)
        for mem in memories:
            ts_str = mem.get('timestamp', '')
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    hour = ts.hour
                    hour_activities[hour].append(mem)
                except:
                    continue
        
        # Detect "active hours"
        total_activities = len(memories)
        for hour, activities in hour_activities.items():
            count = len(activities)
            strength = count / total_activities if total_activities > 0 else 0
            
            if count >= self.min_pattern_occurrences and strength >= self.min_pattern_strength:
                pattern = TemporalPattern(
                    pattern_type='daily',
                    frequency=f'{hour:02d}:00-{hour:02d}:59',
                    strength=strength,
                    description=f'Peak activity at hour {hour:02d}:00 ({count} events)',
                    examples=activities[:3]  # First 3 examples
                )
                patterns.append(pattern)
        
        # Group by day of week
        weekday_activities = defaultdict(list)
        for mem in memories:
            ts_str = mem.get('timestamp', '')
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    weekday = ts.strftime('%A')
                    weekday_activities[weekday].append(mem)
                except:
                    continue
        
        # Detect "active days"
        for weekday, activities in weekday_activities.items():
            count = len(activities)
            strength = count / total_activities if total_activities > 0 else 0
            
            if count >= self.min_pattern_occurrences and strength >= self.min_pattern_strength:
                pattern = TemporalPattern(
                    pattern_type='weekly',
                    frequency=weekday,
                    strength=strength,
                    description=f'High activity on {weekday} ({count} events)',
                    examples=activities[:3]
                )
                patterns.append(pattern)
        
        return sorted(patterns, key=lambda p: p.strength, reverse=True)
    
    def _detect_behavior_patterns(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[BehaviorPattern]:
        """Detect recurring behaviors (what actions repeat)"""
        patterns = []
        
        # Extract actions/events
        actions = []
        for mem in memories:
            # Try different fields where action might be
            action = (
                mem.get('event_type') or
                mem.get('action') or
                mem.get('type') or
                'unknown'
            )
            actions.append((action, mem))
        
        # Count action frequencies
        action_counts = Counter([a[0] for a in actions])
        total_actions = len(actions)
        
        # Group memories by action
        action_memories = defaultdict(list)
        for action, mem in actions:
            action_memories[action].append(mem)
        
        # Detect patterns
        for action, count in action_counts.items():
            if count >= self.min_pattern_occurrences:
                strength = count / total_actions if total_actions > 0 else 0
                
                if strength >= self.min_pattern_strength:
                    # Extract typical context
                    mems = action_memories[action]
                    typical_context = self._extract_typical_context(mems)
                    
                    pattern = BehaviorPattern(
                        action=action,
                        frequency_count=count,
                        typical_context=typical_context,
                        strength=strength
                    )
                    patterns.append(pattern)
        
        return sorted(patterns, key=lambda p: p.strength, reverse=True)
    
    def _detect_trends(
        self,
        memories: List[Dict[str, Any]],
        timespan_hours: int
    ) -> List[Trend]:
        """Detect long-term trends (how things change over time)"""
        trends = []
        
        if len(memories) < 10:  # Need enough data
            return trends
        
        # Sort by time
        sorted_mems = sorted(
            memories,
            key=lambda m: m.get('timestamp', '')
        )
        
        # Split into early/late periods
        mid_point = len(sorted_mems) // 2
        early = sorted_mems[:mid_point]
        late = sorted_mems[mid_point:]
        
        # Activity rate trend
        early_rate = len(early) / (timespan_hours / 2) if timespan_hours > 0 else 0
        late_rate = len(late) / (timespan_hours / 2) if timespan_hours > 0 else 0
        
        if early_rate > 0:
            change = (late_rate - early_rate) / early_rate
            
            if abs(change) >= 0.2:  # 20% change threshold
                direction = 'increasing' if change > 0 else 'decreasing'
                trend = Trend(
                    metric='activity_rate',
                    direction=direction,
                    magnitude=abs(change),
                    timespan_hours=timespan_hours,
                    description=f'Activity rate {direction} by {abs(change)*100:.1f}%'
                )
                trends.append(trend)
        
        # TODO: Add more trend detections
        # - Complexity trends (longer/shorter entries)
        # - Diversity trends (more/fewer unique actions)
        # - Confidence trends (success rate changes)
        
        return trends
    
    def _extract_typical_context(
        self,
        memories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract typical context from similar memories"""
        # Count most common fields
        all_keys = []
        for mem in memories:
            all_keys.extend(mem.keys())
        
        common_keys = [k for k, v in Counter(all_keys).most_common(5)]
        
        # Sample values from first memory
        context = {}
        if memories:
            first = memories[0]
            for key in common_keys:
                if key in first and key not in ['timestamp', 'id']:
                    context[key] = first[key]
        
        return context
    
    def _generate_summary(
        self,
        memories: List[Dict[str, Any]],
        timespan_hours: int
    ) -> Dict[str, Any]:
        """Generate summary of pattern analysis"""
        return {
            'status': 'success',
            'memory_count': len(memories),
            'timespan_hours': timespan_hours,
            'patterns_detected': {
                'temporal': len(self.temporal_patterns),
                'behavioral': len(self.behavior_patterns),
                'trends': len(self.trends)
            },
            'strongest_pattern': self._get_strongest_pattern(),
            'dominant_rhythm': self._get_dominant_rhythm()
        }
    
    def _get_strongest_pattern(self) -> Optional[str]:
        """Get description of strongest pattern"""
        all_patterns = (
            [(p.strength, p.description) for p in self.temporal_patterns] +
            [(p.strength, p.description) for p in self.behavior_patterns]
        )
        
        if all_patterns:
            strongest = max(all_patterns, key=lambda x: x[0])
            return strongest[1]
        
        return None
    
    def _get_dominant_rhythm(self) -> Optional[str]:
        """Get dominant temporal rhythm"""
        if self.temporal_patterns:
            strongest = self.temporal_patterns[0]
            return f"{strongest.pattern_type}: {strongest.frequency}"
        return None
    
    def _pattern_to_dict(self, pattern) -> Dict[str, Any]:
        """Convert pattern object to dict"""
        return {
            'type': pattern.__class__.__name__,
            **{k: v for k, v in pattern.__dict__.items() if not k.startswith('_')}
        }
    
    def _trend_to_dict(self, trend: Trend) -> Dict[str, Any]:
        """Convert trend object to dict"""
        return {
            'metric': trend.metric,
            'direction': trend.direction,
            'magnitude': trend.magnitude,
            'timespan_hours': trend.timespan_hours,
            'description': trend.description,
            'detected_at': trend.detected_at
        }
    
    def export_patterns(self, output_path: Path) -> None:
        """Export detected patterns to JSON"""
        result = {
            'temporal_patterns': [self._pattern_to_dict(p) for p in self.temporal_patterns],
            'behavior_patterns': [self._pattern_to_dict(p) for p in self.behavior_patterns],
            'trends': [self._trend_to_dict(t) for t in self.trends],
            'generated_at': datetime.now().isoformat()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)


# Quick usage example
if __name__ == '__main__':
    from pathlib import Path
    
    workspace = Path(r'c:\workspace\agi')
    detector = WaveDetector(workspace)
    
    print("🌊 Detecting wave patterns...")
    result = detector.analyze_patterns(lookback_hours=168)  # 7 days
    
    print(f"\n📊 Analysis Summary:")
    print(f"   Memories analyzed: {result['summary']['memory_count']}")
    print(f"   Temporal patterns: {result['summary']['patterns_detected']['temporal']}")
    print(f"   Behavioral patterns: {result['summary']['patterns_detected']['behavioral']}")
    print(f"   Trends detected: {result['summary']['patterns_detected']['trends']}")
    
    if result['summary']['strongest_pattern']:
        print(f"\n🌟 Strongest pattern: {result['summary']['strongest_pattern']}")
    
    if result['summary']['dominant_rhythm']:
        print(f"🎵 Dominant rhythm: {result['summary']['dominant_rhythm']}")
