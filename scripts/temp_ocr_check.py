import cv2
import pytesseract
import sys

try:
    img = cv2.imread(r'c:\workspace\agi\outputs\eye_check_v2.png')
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' 
    # Attempt simple path first, or rely on PATH
    text = pytesseract.image_to_string(img)
    print("--- OCR RESULT START ---")
    print(text)
    print("--- OCR RESULT END ---")
    
    # Check for keywords
    keywords = ["AGI-Heartbeat", "AGI-Brain", "Administrator", "PowerShell", "cmd.exe"]
    found = [k for k in keywords if k in text]
    if found:
        print(f"FAIL: Found visible windows matching: {found}")
    else:
        print("PASS: No blacklisted windows detected in OCR.")
        
except Exception as e:
    print(f"Error: {e}")
