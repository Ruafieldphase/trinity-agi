#!/usr/bin/env python3
"""
🎷 Groove Engine - Microtiming & Spectral Balance for Rhythm Enhancement
Computes humanization offsets (push/pull/swing) and spectral EQ hints
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GrooveProfile:
    """
    Groove profile with microtiming and spectral parameters
    
    Attributes:
        swing_ratio: Swing amount (0.0 = straight, 1.0 = full triplet swing)
        push_pull_ms: Average timing offset in milliseconds (-50 to +50)
        microtiming_variance: Randomness in timing (0.0 = robotic, 1.0 = human)
        bass_boost_db: Low-frequency boost (-12 to +12 dB)
        treble_boost_db: High-frequency boost (-12 to +12 dB)
        warmth_factor: Analog warmth simulation (0.0 to 1.0)
    """
    
    def __init__(
        self,
        swing_ratio: float = 0.0,
        push_pull_ms: float = 0.0,
        microtiming_variance: float = 0.3,
        bass_boost_db: float = 0.0,
        treble_boost_db: float = 0.0,
        warmth_factor: float = 0.5,
        name: str = "default"
    ):
        self.swing_ratio = np.clip(swing_ratio, 0.0, 1.0)
        self.push_pull_ms = np.clip(push_pull_ms, -50.0, 50.0)
        self.microtiming_variance = np.clip(microtiming_variance, 0.0, 1.0)
        self.bass_boost_db = np.clip(bass_boost_db, -12.0, 12.0)
        self.treble_boost_db = np.clip(treble_boost_db, -12.0, 12.0)
        self.warmth_factor = np.clip(warmth_factor, 0.0, 1.0)
        self.name = name
    
    def to_dict(self) -> Dict:
        """Serialize to dict"""
        return {
            "name": self.name,
            "swing_ratio": float(self.swing_ratio),
            "push_pull_ms": float(self.push_pull_ms),
            "microtiming_variance": float(self.microtiming_variance),
            "bass_boost_db": float(self.bass_boost_db),
            "treble_boost_db": float(self.treble_boost_db),
            "warmth_factor": float(self.warmth_factor),
            "created_at": datetime.now().isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GrooveProfile':
        """Deserialize from dict"""
        return cls(
            swing_ratio=data.get("swing_ratio", 0.0),
            push_pull_ms=data.get("push_pull_ms", 0.0),
            microtiming_variance=data.get("microtiming_variance", 0.3),
            bass_boost_db=data.get("bass_boost_db", 0.0),
            treble_boost_db=data.get("treble_boost_db", 0.0),
            warmth_factor=data.get("warmth_factor", 0.5),
            name=data.get("name", "loaded")
        )
    
    def save(self, path: Path):
        """Save to JSON file"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Saved groove profile: {path}")
    
    @classmethod
    def load(cls, path: Path) -> Optional['GrooveProfile']:
        """Load from JSON file"""
        if not path.exists():
            logger.warning(f"Groove profile not found: {path}")
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load groove profile: {e}")
            return None


class GrooveEngine:
    """
    Groove Engine - Compute microtiming offsets and spectral hints
    """
    
    def __init__(self, profile: Optional[GrooveProfile] = None):
        """
        Args:
            profile: GrooveProfile to use (defaults to neutral)
        """
        self.profile = profile or GrooveProfile()
        logger.info(f"🎷 Groove Engine initialized (profile: {self.profile.name})")
    
    @classmethod
    def load_profile(cls, path: str) -> 'GrooveEngine':
        """
        Load groove profile from file and create engine
        
        Args:
            path: Path to groove profile JSON file
            
        Returns:
            GrooveEngine with loaded profile (or default if load fails)
        """
        profile = GrooveProfile.load(Path(path))
        return cls(profile=profile)
    
    def compute_beat_offset(self, beat_index: int, bpm: float) -> float:
        """
        Compute timing offset for a beat (in seconds)
        
        Args:
            beat_index: Beat number (0, 1, 2, 3 for 4/4 time)
            bpm: Tempo in beats per minute
            
        Returns:
            Timing offset in seconds (negative = early, positive = late)
        """
        # Base offset from push/pull
        base_offset_sec = self.profile.push_pull_ms / 1000.0
        
        # Swing on off-beats (16th note subdivision)
        beat_time_sec = 60.0 / bpm
        sixteenth_time = beat_time_sec / 4.0
        
        swing_offset = 0.0
        if beat_index % 2 == 1:  # Off-beats
            swing_offset = sixteenth_time * self.profile.swing_ratio * 0.5
        
        # Add microtiming variance (humanization)
        variance_offset = 0.0
        if self.profile.microtiming_variance > 0:
            max_variance_ms = 5.0 * self.profile.microtiming_variance
            variance_offset = np.random.uniform(-max_variance_ms, max_variance_ms) / 1000.0
    
    def compute_microtiming_offset(self, beat_index: int, bpm: float) -> float:
        """
        Alias for compute_beat_offset for backward compatibility
        
        Args:
            beat_index: Beat number
            bpm: Tempo in BPM
            
        Returns:
            Timing offset in seconds
        """
        return self.compute_beat_offset(beat_index, bpm)
        
        total_offset = base_offset_sec + swing_offset + variance_offset
        
        return total_offset
    
    def get_spectral_eq_hints(self) -> Dict[str, float]:
        """
        Get spectral EQ hints for audio processing
        
        Returns:
            Dict with frequency band gain adjustments (dB)
        """
        return {
            "bass_gain_db": self.profile.bass_boost_db,
            "mid_gain_db": 0.0,  # Neutral for now
            "treble_gain_db": self.profile.treble_boost_db,
            "warmth_saturation": self.profile.warmth_factor
        }
    
    def apply_groove_to_sequence(
        self, 
        beat_times: List[float], 
        bpm: float
    ) -> List[float]:
        """
        Apply groove to a sequence of beat times
        
        Args:
            beat_times: Original beat times (in seconds)
            bpm: Tempo
            
        Returns:
            Grooved beat times
        """
        grooved_times = []
        
        for i, beat_time in enumerate(beat_times):
            offset = self.compute_beat_offset(i, bpm)
            grooved_times.append(beat_time + offset)
        
        return grooved_times
    
    def generate_test_pattern(self, bpm: float = 120, num_beats: int = 16) -> Dict:
        """
        Generate a test rhythm pattern with groove applied
        
        Args:
            bpm: Tempo
            num_beats: Number of beats
            
        Returns:
            Dict with original and grooved beat times
        """
        beat_duration = 60.0 / bpm
        original_times = [i * beat_duration for i in range(num_beats)]
        grooved_times = self.apply_groove_to_sequence(original_times, bpm)
        
        return {
            "bpm": bpm,
            "num_beats": num_beats,
            "original_times": original_times,
            "grooved_times": grooved_times,
            "offsets_ms": [(g - o) * 1000 for o, g in zip(original_times, grooved_times)],
            "profile": self.profile.to_dict()
        }


# Preset profiles
PRESET_PROFILES = {
    "j_dilla_swing": GrooveProfile(
        swing_ratio=0.65,
        push_pull_ms=-8.0,
        microtiming_variance=0.4,
        bass_boost_db=3.0,
        warmth_factor=0.8,
        name="J Dilla Swing"
    ),
    "funk_push": GrooveProfile(
        swing_ratio=0.3,
        push_pull_ms=15.0,  # Ahead of the beat
        microtiming_variance=0.5,
        bass_boost_db=6.0,
        treble_boost_db=-2.0,
        warmth_factor=0.9,
        name="Funk Push"
    ),
    "laid_back": GrooveProfile(
        swing_ratio=0.2,
        push_pull_ms=-20.0,  # Behind the beat
        microtiming_variance=0.6,
        bass_boost_db=2.0,
        warmth_factor=0.7,
        name="Laid Back"
    ),
    "robotic": GrooveProfile(
        swing_ratio=0.0,
        push_pull_ms=0.0,
        microtiming_variance=0.0,
        bass_boost_db=0.0,
        treble_boost_db=0.0,
        warmth_factor=0.0,
        name="Robotic (No Groove)"
    )
}


def get_preset_profile(name: str) -> Optional[GrooveProfile]:
    """Get a preset groove profile by name"""
    return PRESET_PROFILES.get(name)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test with J Dilla swing
    profile = get_preset_profile("j_dilla_swing")
    engine = GrooveEngine(profile)
    
    # Generate test pattern
    pattern = engine.generate_test_pattern(bpm=95, num_beats=8)
    
    print("\n🎷 Groove Engine Test Pattern:")
    print(json.dumps(pattern, indent=2))
    
    # Save profile
    output_path = Path("outputs/groove_profile_test.json")
    profile.save(output_path)
    
    # Load and verify
    loaded_profile = GrooveProfile.load(output_path)
    print(f"\n✅ Loaded profile: {loaded_profile.name}")
    
    # Show spectral hints
    hints = engine.get_spectral_eq_hints()
    print(f"\n🎚️ Spectral EQ Hints:")
    print(json.dumps(hints, indent=2))
