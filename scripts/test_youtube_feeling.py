#!/usr/bin/env python3
"""
Test YouTube Feeling Learner
=============================
Simple test script to verify the feeling learner works.
"""

import asyncio
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from youtube_feeling_learner import YouTubeFeelingLearner


async def test_basic():
    """Test basic functionality"""
    print("🧪 Testing YouTube Feeling Learner\n")
    print("="*80)
    
    # Test video: A short, well-known video
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    try:
        learner = YouTubeFeelingLearner()
        analysis = await learner.analyze_feeling(
            video_url=test_url,
            context="테스트 실행",
            analyzed_by="test_script"
        )
        
        print("\n✅ TEST PASSED!")
        print(f"   Feeling vector dimension: {len(analysis.feeling_vector)}")
        print(f"   Emotional tone: {analysis.emotional_tone}")
        print(f"   Themes extracted: {len(analysis.resonance_themes)}")
        
        return True
    
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_basic())
    exit(0 if success else 1)
