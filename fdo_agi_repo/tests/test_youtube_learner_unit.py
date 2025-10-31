"""
Unit tests for rpa.youtube_learner

These tests avoid network and heavy optional deps by only exercising
pure-Python parts: keyword extraction and summary generation.
"""

from rpa.youtube_learner import YouTubeLearner, Subtitle


def test_extract_keywords_basic():
    yl = YouTubeLearner()
    subtitles = [
        Subtitle(text="Python is great for programming", start=0.0, duration=2.0),
        Subtitle(text="Programming in Python with code samples", start=2.0, duration=2.0),
        Subtitle(text="Code, code, and more code in python!", start=4.0, duration=2.0),
    ]

    keywords = yl._extract_keywords(subtitles)

    # Should contain dominant tokens (3+ chars, lowercased)
    assert "python" in keywords
    assert "programming" in keywords or "code" in keywords
    assert len(keywords) <= 10


def test_extract_keywords_empty():
    yl = YouTubeLearner()
    keywords = yl._extract_keywords([])
    assert keywords == []


def test_generate_summary_with_no_subtitles():
    yl = YouTubeLearner()
    summary = yl._generate_summary([], ["python", "programming"])  # keywords ignored when no subs
    assert summary == "No subtitles available"


def test_extract_video_id_watch_url():
    yl = YouTubeLearner()
    vid = yl._extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstley")
    assert vid == "dQw4w9WgXcQ"


def test_extract_video_id_short_url():
    yl = YouTubeLearner()
    vid = yl._extract_video_id("https://youtu.be/dQw4w9WgXcQ?t=43")
    assert vid == "dQw4w9WgXcQ"
