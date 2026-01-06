import numpy as np
import cv2
import pyautogui
import os
import argparse
from datetime import datetime
from pathlib import Path

def create_flashbulb_memory(trigger_type: str = "manual", intensity: float = 1.0):
    """
    Captures a 'Flashbulb Memory' of the current visual state.
    Compresses the visual reality into a Fourier Magnitude Spectrum (Feeling Image).
    """
    print(f"📸 Flashbulb Triggered: {trigger_type} (Intensity: {intensity})")
    
    # Setup paths
    memory_dir = Path("fdo_agi_repo/memory/flashbulbs")
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_base = f"flashbulb_{timestamp}_{trigger_type}"
    
    # 1. Capture Reality (Screen)
    try:
        screenshot = pyautogui.screenshot()
        img = np.array(screenshot)
        img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    except Exception as e:
        print(f"❌ Screen capture failed: {e}")
        return

    # 2. Compress to Feeling (Fourier Transform)
    print("🧠 Compressing to Unconscious Feeling (FFT)...")
    f = np.fft.fft2(img_gray)
    fshift = np.fft.fftshift(f)
    
    # Magnitude Spectrum (The "0101" View)
    magnitude_spectrum = 20 * np.log(np.abs(fshift))
    
    # Normalize for storage
    spectrum_img = cv2.normalize(magnitude_spectrum, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    
    # 3. Store Memory
    spectrum_path = memory_dir / f"{filename_base}_spectrum.png"
    cv2.imwrite(str(spectrum_path), spectrum_img)
    
    # Optional: Save low-res thumbnail of reality for reference (The "Conscious" trace)
    reality_thumb = cv2.resize(img, (0, 0), fx=0.1, fy=0.1)
    thumb_path = memory_dir / f"{filename_base}_reality_thumb.jpg"
    cv2.imwrite(str(thumb_path), reality_thumb)
    
    print(f"✅ Memory Stored:")
    print(f"   Feeling: {spectrum_path}")
    print(f"   Trace:   {thumb_path}")
    
    return str(spectrum_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a Flashbulb Memory.")
    parser.add_argument("--trigger", default="manual", help="Trigger type (fear, wow, manual)")
    parser.add_argument("--intensity", type=float, default=1.0, help="Emotional intensity (0.0-1.0)")
    
    args = parser.parse_args()
    
    create_flashbulb_memory(args.trigger, args.intensity)
