#!/usr/bin/env python3
"""
Language Drift Detector
=======================
Detects when the system drifts from the user's preferred language.
Part of the Background Self's sensor suite.
"""

import re
from typing import Dict, Tuple

class LanguageDriftDetector:
    """
    Detects language drift (e.g., outputting English when Korean is preferred).
    """
    
    def __init__(self, target_language: str = 'ko'):
        self.target_language = target_language
        
    def detect(self, text: str) -> Tuple[bool, float, str]:
        """
        Analyze text for language drift.
        
        Returns:
            (is_drift, drift_score, reason)
        """
        if not text or len(text.strip()) < 10:
            return False, 0.0, "Text too short"
            
        # Simple heuristic: Count Hangul vs English characters
        hangul_count = len(re.findall(r'[가-힣]', text))
        english_count = len(re.findall(r'[a-zA-Z]', text))
        total_count = len(text)
        
        if total_count == 0:
            return False, 0.0, "Empty text"
            
        # Ratios
        hangul_ratio = hangul_count / total_count
        english_ratio = english_count / total_count
        
        if self.target_language == 'ko':
            # If Korean is preferred but English dominates significantly
            if english_ratio > 0.5 and hangul_ratio < 0.1:
                drift_score = min(1.0, english_ratio * 2)
                return True, drift_score, f"English dominance detected ({english_ratio:.1%})"
            
            # If mixed but mostly English
            if english_ratio > hangul_ratio * 2:
                drift_score = 0.6
                return True, drift_score, f"High English ratio ({english_ratio:.1%} vs {hangul_ratio:.1%})"
                
        return False, 0.0, "Normal"

if __name__ == "__main__":
    # Test
    detector = LanguageDriftDetector('ko')
    
    samples = [
        "안녕하세요, Shion입니다.",
        "Hello, I am Shion. I am an AGI.",
        "시스템 상태는 stable합니다. Check complete.",
        "System check complete. All systems operational."
    ]
    
    print("Target: Korean")
    for s in samples:
        drift, score, reason = detector.detect(s)
        print(f"Text: {s[:30]}... -> Drift: {drift}, Score: {score:.2f}, Reason: {reason}")
