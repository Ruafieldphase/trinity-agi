"""
Step Extractor Module
Phase 2.5 Week 2 Day 9: 자막/프레임에서 실행 단계 추출

Purpose:
    YouTube 분석 결과에서 실행 가능한 단계를 자동 추출

Features:
1. 자막에서 액션 키워드 인식 (click, download, install, run, type)
2. 시간 순서대로 단계 정렬
3. UI 요소 식별 (버튼, 입력 필드 등)
4. 실행 가능한 JSON 형식 생성

Example:
    >>> extractor = StepExtractor()
    >>> analysis = load_json("analysis.json")
    >>> steps = extractor.extract_steps(analysis)
    >>> print(steps[0])
    {"order": 1, "action": "download", "target": "Docker Desktop"}
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# Configuration
# ============================================================================

# 액션 키워드 매핑
ACTION_KEYWORDS = {
    "click": ["click", "press", "select", "choose", "tap"],
    "type": ["type", "enter", "input", "write", "fill"],
    "download": ["download", "get", "fetch", "retrieve"],
    "install": ["install", "setup", "configure", "deploy"],
    "wait": ["wait", "pause", "hold", "sleep"],
    "run": ["run", "execute", "launch", "start", "open"],
    "close": ["close", "exit", "quit", "stop"],
    "scroll": ["scroll", "move", "navigate"],
}

# UI 요소 키워드
UI_ELEMENTS = {
    "button": ["button", "btn", "next", "finish", "ok", "accept", "install", "download"],
    "input": ["field", "box", "input", "textbox", "form"],
    "menu": ["menu", "dropdown", "select"],
    "link": ["link", "url", "website", "page"],
    "checkbox": ["checkbox", "check", "option"],
}

# 소프트웨어 설치 관련 패턴
INSTALL_PATTERNS = [
    r"download\s+(?:the\s+)?(.+?)(?:\s+installer)?",
    r"click\s+(?:on\s+)?(?:the\s+)?(.+?)\s+button",
    r"run\s+(?:the\s+)?(.+?)(?:\.exe)?",
    r"install\s+(.+)",
    r"type\s+(.+?)\s+in\s+(?:the\s+)?(.+?)\s+field",
]


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ExtractedStep:
    """추출된 실행 단계"""
    order: int
    action: str  # click, type, download, install, wait, run
    target: Optional[str] = None  # 버튼 이름, 파일명 등
    value: Optional[str] = None  # 입력할 텍스트 (type 액션)
    timestamp: Optional[float] = None  # 영상 타임스탬프 (초)
    description: str = ""
    confidence: float = 0.0  # 0.0 ~ 1.0
    source: str = "subtitle"  # subtitle, frame, ocr
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "order": self.order,
            "action": self.action,
            "target": self.target,
            "value": self.value,
            "timestamp": self.timestamp,
            "description": self.description,
            "confidence": self.confidence,
            "source": self.source
        }


# ============================================================================
# Step Extractor
# ============================================================================

class StepExtractor:
    """
    YouTube 분석 결과에서 실행 단계를 자동 추출
    
    현재 구현: 자막 기반 (v1)
    향후 개선: 프레임 OCR, LLM 기반 추출
    """
    
    def __init__(self):
        self.action_keywords = ACTION_KEYWORDS
        self.ui_elements = UI_ELEMENTS
        self.install_patterns = [re.compile(p, re.IGNORECASE) for p in INSTALL_PATTERNS]
    
    def extract_steps(
        self,
        analysis_path: Path,
        min_confidence: float = 0.3
    ) -> List[ExtractedStep]:
        """
        분석 결과 JSON에서 실행 단계 추출
        
        Args:
            analysis_path: 분석 결과 JSON 파일 경로
            min_confidence: 최소 신뢰도 (0.0 ~ 1.0)
        
        Returns:
            List[ExtractedStep]: 추출된 단계 리스트
        """
        # Load analysis
        with open(analysis_path, "r", encoding="utf-8") as f:
            analysis = json.load(f)
        
        steps: List[ExtractedStep] = []
        
        # Extract from subtitles (if available)
        if "subtitles" in analysis:
            subtitle_steps = self._extract_from_subtitles(analysis["subtitles"])
            steps.extend(subtitle_steps)
        
        # TODO: Extract from frames (OCR)
        # if "frames" in analysis:
        #     frame_steps = self._extract_from_frames(analysis["frames"])
        #     steps.extend(frame_steps)
        
        # Filter by confidence
        steps = [s for s in steps if s.confidence >= min_confidence]
        
        # Sort by timestamp and assign order
        steps.sort(key=lambda s: s.timestamp if s.timestamp else 0)
        for i, step in enumerate(steps, start=1):
            step.order = i
        
        return steps
    
    def _extract_from_subtitles(
        self,
        subtitles: List[Dict[str, Any]]
    ) -> List[ExtractedStep]:
        """자막에서 단계 추출"""
        steps: List[ExtractedStep] = []
        
        for sub in subtitles:
            text = sub.get("text", "").lower()
            timestamp = sub.get("start", 0.0)
            
            # Try pattern matching first
            for pattern in self.install_patterns:
                match = pattern.search(text)
                if match:
                    step = self._create_step_from_pattern(text, match, timestamp)
                    if step:
                        steps.append(step)
                        break  # Use first matching pattern
            else:
                # Fallback: keyword-based extraction
                step = self._create_step_from_keywords(text, timestamp)
                if step:
                    steps.append(step)
        
        return steps
    
    def _create_step_from_pattern(
        self,
        text: str,
        match: re.Match,
        timestamp: float
    ) -> Optional[ExtractedStep]:
        """패턴 매칭으로 단계 생성"""
        groups = match.groups()
        
        # Determine action from text
        action = "unknown"
        for act, keywords in self.action_keywords.items():
            if any(kw in text for kw in keywords):
                action = act
                break
        
        # Extract target
        target = groups[0] if groups else None
        if target:
            target = target.strip()
        
        # Create step
        return ExtractedStep(
            order=0,  # Will be set later
            action=action,
            target=target,
            timestamp=timestamp,
            description=text,
            confidence=0.7,  # High confidence for pattern match
            source="subtitle"
        )
    
    def _create_step_from_keywords(
        self,
        text: str,
        timestamp: float
    ) -> Optional[ExtractedStep]:
        """키워드 기반 단계 생성"""
        # Find action
        action = None
        for act, keywords in self.action_keywords.items():
            if any(kw in text for kw in keywords):
                action = act
                break
        
        if not action:
            return None
        
        # Find UI element
        target = None
        for element_type, keywords in self.ui_elements.items():
            for kw in keywords:
                if kw in text:
                    target = kw
                    break
            if target:
                break
        
        # Create step
        return ExtractedStep(
            order=0,
            action=action,
            target=target,
            timestamp=timestamp,
            description=text,
            confidence=0.4,  # Lower confidence for keyword match
            source="subtitle"
        )
    
    def save_steps(
        self,
        steps: List[ExtractedStep],
        output_path: Path
    ):
        """단계를 JSON 파일로 저장"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "steps_count": len(steps),
            "steps": [s.to_dict() for s in steps],
            "generated_at": None  # Will be set by caller
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI 테스트"""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Step Extractor - Extract execution steps from YouTube analysis")
    parser.add_argument("--analysis", required=True, help="Analysis JSON file path")
    parser.add_argument("--output", help="Output JSON file path (optional)")
    parser.add_argument("--min-confidence", type=float, default=0.3, help="Minimum confidence (0.0-1.0)")
    
    args = parser.parse_args()
    
    analysis_path = Path(args.analysis)
    if not analysis_path.exists():
        print(f"❌ Analysis file not found: {analysis_path}")
        return 1
    
    print(f"📄 Loading analysis: {analysis_path}")
    
    extractor = StepExtractor()
    steps = extractor.extract_steps(analysis_path, min_confidence=args.min_confidence)
    
    print(f"\n✅ Extracted {len(steps)} steps")
    print("\n" + "="*60)
    
    for step in steps:
        print(f"\nStep {step.order}: {step.action.upper()}")
        if step.target:
            print(f"  Target: {step.target}")
        if step.value:
            print(f"  Value: {step.value}")
        print(f"  Time: {step.timestamp:.1f}s")
        print(f"  Confidence: {step.confidence:.2f}")
        print(f"  Description: {step.description[:60]}...")
    
    print("\n" + "="*60)
    
    # Save if output path provided
    if args.output:
        output_path = Path(args.output)
        extractor.save_steps(steps, output_path)
        print(f"\n💾 Steps saved: {output_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())
