"""
Unified Vision Test
===================

Demonstrates three vision approaches:
1. Fourier Vision: Frequency-based complexity
2. Reflection Field Vision: Boundary-based analysis
3. OCR Vision: Text reading

Shows how Reflection Field Theory simplifies vision.
"""

import numpy as np
import pyautogui
import cv2
from vision_cortex import VisionCortex

def compare_vision_methods():
    print("👁️ Unified Vision Test")
    print("   Comparing: Fourier vs Reflection Field vs OCR\n")
    
    vision = VisionCortex()
    
    # Capture current screen
    screenshot = pyautogui.screenshot()
    img = np.array(screenshot)
    img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    print("=" * 60)
    print("Method 1: Fourier Transform (Frequency Analysis)")
    print("=" * 60)
    
    # Fourier analysis
    f = np.fft.fft2(img_gray)
    magnitude = np.abs(f)
    avg_magnitude = np.mean(magnitude)
    
    print(f"Screen complexity (Fourier): {avg_magnitude:.2f}")
    print(f"Data points analyzed: {img_gray.size:,}")
    print(f"Interpretation: {'Complex/Busy' if avg_magnitude > 10000 else 'Simple/Blank'}")
    
    print("\n" + "=" * 60)
    print("Method 2: Reflection Field Transform (Boundary Analysis)")
    print("=" * 60)
    
    # Boundary analysis
    boundaries = vision.analyze_boundaries()
    
    if boundaries:
        print(f"Interpretation: {boundaries['major_regions']} distinct regions detected")
        print(f"Efficiency: {1/boundaries['compression_ratio']:.0f}x compression")
        print(f"Key insight: Only {boundaries['major_regions']} boundaries matter!")
    
    print("\n" + "=" * 60)
    print("Method 3: OCR (Text Reading)")
    print("=" * 60)
    
    # OCR sample (top-left corner)
    text = vision.read_text(region=(0, 0, 800, 200))
    print(f"Text detected: {len(text)} characters")
    print(f"Sample: {text[:100]}...")
    
    print("\n" + "=" * 60)
    print("Comparison Summary")
    print("=" * 60)
    
    print("\n📊 Fourier Transform:")
    print("   ✓ Good for: Overall complexity, frequency content")
    print("   ✗ Limitation: Analyzes ALL pixels (expensive)")
    
    print("\n🌌 Reflection Field Transform:")
    print("   ✓ Good for: Finding what matters (boundaries)")
    print("   ✓ Efficiency: Extreme compression (1000x+)")
    print("   ✓ Holographic: Information lives at edges")
    
    print("\n📖 OCR:")
    print("   ✓ Good for: Reading specific text")
    print("   ✗ Limitation: Slow, language-dependent")
    
    print("\n💡 Unified Approach:")
    print("   1. Use Reflection Field to find boundaries")
    print("   2. Use Fourier on boundaries only (not whole screen)")
    print("   3. Use OCR on text regions only")
    print("   → Best of all worlds!")

if __name__ == "__main__":
    compare_vision_methods()
