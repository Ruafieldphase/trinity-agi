"""
Computer Use Agent - Python Backend
Screen capture, OCR (Tesseract or RapidOCR), click and type automation
"""
import argparse
import json
import sys
from typing import List, Dict, Optional, Tuple
import os
from math import floor

import pyautogui
from PIL import Image
import pytesseract

# Optional RapidOCR backend
try:
    from rapidocr_onnxruntime import RapidOCR  # type: ignore
    import numpy as np  # type: ignore
    RAPID_AVAILABLE = True
except Exception:
    RapidOCR = None  # type: ignore
    np = None  # type: ignore
    RAPID_AVAILABLE = False


def _maybe_set_tesseract_cmd() -> None:
    """If tesseract.exe is not discoverable, try common paths on Windows."""
    # Respect existing configuration if version can be fetched.
    try:
        _ = pytesseract.get_tesseract_version()
        return
    except Exception:
        pass

    candidates = [
        r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
        r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
        r"C:\\ProgramData\\chocolatey\\bin\\tesseract.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            pytesseract.pytesseract.tesseract_cmd = c
            break


_maybe_set_tesseract_cmd()


class ScreenElement:
    """Screen element with text and bounding box."""

    def __init__(self, text: str, x: int, y: int, width: int, height: int, confidence: float):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.confidence = confidence

    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": self.confidence,
        }


class ComputerUseAgent:
    """Computer Use core implementation."""

    def __init__(self) -> None:
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5

    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
        if region:
            return pyautogui.screenshot(region=region)
        return pyautogui.screenshot()

    def _ocr_tesseract_text(self, image: Image.Image) -> str:
        try:
            text = pytesseract.image_to_string(image, lang="eng+kor")
            return text.strip()
        except Exception as e:
            print(f"Tesseract OCR error: {e}", file=sys.stderr)
            return ""

    def _ocr_rapid_text(self, image: Image.Image) -> str:
        if not RAPID_AVAILABLE:
            return ""
        try:
            reader = RapidOCR()  # type: ignore[call-arg]
            img = np.array(image)  # type: ignore[attr-defined]
            result, _ = reader(img)
            if not result:
                return ""
            lines = [item[1] for item in result]
            return "\n".join(lines).strip()
        except Exception as e:
            print(f"RapidOCR text error: {e}", file=sys.stderr)
            return ""

    def ocr_image(self, image: Image.Image) -> str:
        pref = os.environ.get("COMPUTER_USE_OCR_BACKEND", "").lower()
        if pref == "rapidocr" and RAPID_AVAILABLE:
            text = self._ocr_rapid_text(image)
            if text:
                return text
            return self._ocr_tesseract_text(image)
        if pref == "tesseract":
            text = self._ocr_tesseract_text(image)
            if text:
                return text
            return self._ocr_rapid_text(image)

        # auto: prefer tesseract, fallback rapid
        text = self._ocr_tesseract_text(image)
        if text:
            return text
        return self._ocr_rapid_text(image)

    def _ocr_tesseract_with_boxes(self, image: Image.Image) -> List[ScreenElement]:
        try:
            data = pytesseract.image_to_data(image, lang="eng+kor", output_type=pytesseract.Output.DICT)
            elements: List[ScreenElement] = []
            for i in range(len(data["text"])):
                text = (data["text"][i] or "").strip()
                if not text:
                    continue
                try:
                    x = int(data["left"][i])
                    y = int(data["top"][i])
                    width = int(data["width"][i])
                    height = int(data["height"][i])
                    conf_raw = data["conf"][i]
                    confidence = float(conf_raw) / 100.0 if conf_raw not in ("", "-1") else 0.0
                except Exception:
                    continue
                if confidence >= 0.5:
                    elements.append(ScreenElement(text, x, y, width, height, confidence))
            return elements
        except Exception as e:
            print(f"Tesseract boxes error: {e}", file=sys.stderr)
            return []

    def _ocr_rapid_with_boxes(self, image: Image.Image) -> List[ScreenElement]:
        if not RAPID_AVAILABLE:
            return []
        try:
            reader = RapidOCR()  # type: ignore[call-arg]
            img = np.array(image)  # type: ignore[attr-defined]
            result, _ = reader(img)
            elements: List[ScreenElement] = []
            if not result:
                return elements
            for item in result:
                box, text, score = item
                if not text:
                    continue
                xs = [pt[0] for pt in box]
                ys = [pt[1] for pt in box]
                x_min, y_min = max(0, floor(min(xs))), max(0, floor(min(ys)))
                x_max, y_max = floor(max(xs)), floor(max(ys))
                width, height = max(1, x_max - x_min), max(1, y_max - y_min)
                confidence = float(score)
                if confidence >= 0.5:
                    elements.append(ScreenElement(str(text), x_min, y_min, width, height, confidence))
            return elements
        except Exception as e:
            print(f"RapidOCR boxes error: {e}", file=sys.stderr)
            return []

    def ocr_with_boxes(self, image: Image.Image) -> List[ScreenElement]:
        pref = os.environ.get("COMPUTER_USE_OCR_BACKEND", "").lower()
        if pref == "rapidocr" and RAPID_AVAILABLE:
            elems = self._ocr_rapid_with_boxes(image)
            if elems:
                return elems
            return self._ocr_tesseract_with_boxes(image)
        if pref == "tesseract":
            elems = self._ocr_tesseract_with_boxes(image)
            if elems:
                return elems
            return self._ocr_rapid_with_boxes(image)

        elems = self._ocr_tesseract_with_boxes(image)
        if elems:
            return elems
        return self._ocr_rapid_with_boxes(image)

    def find_element_by_text(self, search_text: str) -> Optional[ScreenElement]:
        screenshot = self.capture_screen()
        elements = self.ocr_with_boxes(screenshot)
        needle = search_text.lower()
        for el in elements:
            if needle in el.text.lower():
                return el
        return None

    def click_at(self, x: int, y: int) -> bool:
        try:
            pyautogui.click(x, y)
            return True
        except Exception as e:
            print(f"Click error: {e}", file=sys.stderr)
            return False

    def type_text(self, text: str) -> bool:
        try:
            pyautogui.write(text, interval=0.1)
            return True
        except Exception as e:
            print(f"Type error: {e}", file=sys.stderr)
            return False

    def scan_screen(self) -> List[ScreenElement]:
        screenshot = self.capture_screen()
        return self.ocr_with_boxes(screenshot)


def main() -> None:
    parser = argparse.ArgumentParser(description="Computer Use Agent")
    parser.add_argument("action", choices=["find", "click", "type", "scan"], help="Action to perform")
    parser.add_argument("--text", help="Text for find/type actions")
    parser.add_argument("--x", type=int, help="X coordinate for click")
    parser.add_argument("--y", type=int, help="Y coordinate for click")

    args = parser.parse_args()
    agent = ComputerUseAgent()

    try:
        if args.action == "find":
            if not args.text:
                print("Error: --text is required for 'find'", file=sys.stderr)
                sys.exit(1)
            el = agent.find_element_by_text(args.text)
            print(json.dumps(el.to_dict() if el else None))

        elif args.action == "click":
            if args.x is None or args.y is None:
                print("Error: --x and --y are required for 'click'", file=sys.stderr)
                sys.exit(1)
            ok = agent.click_at(args.x, args.y)
            sys.exit(0 if ok else 1)

        elif args.action == "type":
            if not args.text:
                print("Error: --text is required for 'type'", file=sys.stderr)
                sys.exit(1)
            ok = agent.type_text(args.text)
            sys.exit(0 if ok else 1)

        elif args.action == "scan":
            els = agent.scan_screen()
            print(json.dumps([e.to_dict() for e in els]))

    except Exception as e:
        print(f"Unhandled error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()



