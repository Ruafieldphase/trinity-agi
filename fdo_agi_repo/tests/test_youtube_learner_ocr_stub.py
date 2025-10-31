"""
Unit test for OCR keyword extraction path using a stubbed easyocr.Reader.
This avoids heavy dependency and network/model downloads.
"""

import types
import sys
import pytest
from rpa.youtube_learner import YouTubeLearner, VideoFrame


class FakeReader:
    def __init__(self, langs, gpu=False):
        # simulate init success
        self.langs = langs
        self.gpu = gpu

    def readtext(self, frame):
        # Return a deterministic list of [bbox, text, conf]
        return [
            (None, "HelloWorld", 0.9),
            (None, "PythonRocks", 0.85),
            (None, "Hi", 0.5),  # short (<4) should be ignored
        ]


@pytest.mark.asyncio
async def test_extract_ocr_words_with_stub(monkeypatch):
    # Inject a fake 'easyocr' module
    fake_easyocr = types.ModuleType("easyocr")
    fake_easyocr.Reader = FakeReader  # type: ignore
    sys.modules["easyocr"] = fake_easyocr

    yl = YouTubeLearner()

    # Prepare two dummy frames; actual pixel data is unused by FakeReader
    frames = [
        VideoFrame(timestamp=0.0, frame=None, description=""),
        VideoFrame(timestamp=1.0, frame=None, description=None),
    ]

    # Limit OCR to first frame to ensure deterministic update
    yl.config.max_ocr_frames = 1

    ocr_words = await yl._extract_ocr_words(frames)

    # Expect only long tokens, lowercased by frequency logic in implementation
    # The implementation lowercases and counts; top 5 truncated
    assert isinstance(ocr_words, list)
    assert "helloworld" in ocr_words
    assert "pythonrocks" in ocr_words

    # Description of first frame should be enriched (max 200 chars)
    assert isinstance(frames[0].description, str)
    assert "HelloWorld" in frames[0].description or "PythonRocks" in frames[0].description

    # Second frame untouched because of max_ocr_frames=1
    assert frames[1].description is None
