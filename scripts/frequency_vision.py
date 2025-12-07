import numpy as np
import cv2
import pyautogui
import time

def frequency_vision():
    print("👁️ Activating Fourier Vision (Frequency Domain)...")
    
    # 1. Capture Screen
    screenshot = pyautogui.screenshot()
    img = np.array(screenshot)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # Resize for speed (optional, but good for real-time)
    # img = cv2.resize(img, (0, 0), fx=0.5, fy=0.5)
    
    rows, cols = img.shape
    print(f"   Input Resolution: {cols}x{rows}")
    
    # 2. Fast Fourier Transform (FFT)
    print("   Transforming to Frequency Domain...")
    f = np.fft.fft2(img)
    fshift = np.fft.fftshift(f)
    
    # 3. Magnitude Spectrum
    # 20*log(abs(f)) to scale it for human vision
    magnitude_spectrum = 20 * np.log(np.abs(fshift))
    
    # Normalize to 0-255 for display
    magnitude_spectrum = cv2.normalize(magnitude_spectrum, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    
    # 4. Display
    print("✨ Visualization Ready.")
    
    # Show Original vs Spectrum
    # Resize spectrum to match original if needed, or just show side by side
    # For simplicity, let's just show the Spectrum
    
    cv2.imshow('Fourier Vision: Magnitude Spectrum', magnitude_spectrum)
    cv2.imshow('Original Reality (Time Domain)', img)
    
    print("   Press any key to close...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    frequency_vision()
