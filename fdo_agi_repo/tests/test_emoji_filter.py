#!/usr/bin/env python3
"""Tests for emoji filter utility."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from utils.emoji_filter import remove_emojis


class TestEmojiFilter:
    """Test cases for emoji removal functionality."""

    def test_basic_emojis(self):
        """Test removal of common emojis."""
        text = "Hello 😀 World 🌍!"
        assert remove_emojis(text) == "Hello  World !"
        
    def test_multiple_emojis(self):
        """Test removal of multiple consecutive emojis."""
        text = "Great work! 🎉🎊✨"
        assert remove_emojis(text) == "Great work! "
        
    def test_emojis_with_variation_selectors(self):
        """Test removal of emojis with variation selectors."""
        text = "Check this ✅ and that ❌"
        result = remove_emojis(text)
        assert "✅" not in result
        assert "❌" not in result
        
    def test_skin_tone_modifiers(self):
        """Test removal of emojis with skin tone modifiers."""
        text = "Wave 👋🏻 or 👋🏿"
        result = remove_emojis(text)
        assert "👋" not in result
        assert "🏻" not in result
        assert "🏿" not in result
        
    def test_flag_emojis(self):
        """Test removal of flag emojis (regional indicators)."""
        text = "USA 🇺🇸 and Korea 🇰🇷"
        result = remove_emojis(text)
        assert "🇺🇸" not in result
        assert "🇰🇷" not in result
        
    def test_composite_emojis(self):
        """Test removal of composite emojis with ZWJ."""
        text = "Family 👨‍👩‍👧‍👦 and couple 👨‍❤️‍👨"
        result = remove_emojis(text)
        assert "👨" not in result
        assert "👩" not in result
        assert "👧" not in result
        
    def test_plain_text_unchanged(self):
        """Test that plain text without emojis is unchanged."""
        text = "This is a normal sentence with no emojis."
        assert remove_emojis(text) == text
        
    def test_korean_text_preserved(self):
        """Test that Korean characters are preserved."""
        text = "안녕하세요 😊 반갑습니다 🎉"
        result = remove_emojis(text)
        assert "안녕하세요" in result
        assert "반갑습니다" in result
        assert "😊" not in result
        assert "🎉" not in result
        
    def test_empty_string(self):
        """Test handling of empty string."""
        assert remove_emojis("") == ""
        
    def test_none_input(self):
        """Test handling of None input."""
        assert remove_emojis(None) == ""
        
    def test_numbers_and_punctuation(self):
        """Test that numbers and punctuation are preserved."""
        text = "Score: 100! 🎯 Great job."
        result = remove_emojis(text)
        assert "100" in result
        assert "!" in result
        assert "." in result
        assert "🎯" not in result
        
    def test_mixed_content(self):
        """Test realistic mixed content."""
        text = "Task completed ✅ Performance: 95% 🚀 Next: optimization 💡"
        result = remove_emojis(text)
        assert "Task completed" in result
        assert "Performance: 95%" in result
        assert "Next: optimization" in result
        assert "✅" not in result
        assert "🚀" not in result
        assert "💡" not in result
        
    def test_emoticons_preserved(self):
        """Test that text emoticons are preserved (not Unicode emojis)."""
        text = "Happy :) and sad :("
        assert remove_emojis(text) == text
        
    def test_special_symbols_preserved(self):
        """Test that special symbols (non-emoji) are preserved."""
        text = "Copyright © and trademark ™ symbols"
        assert remove_emojis(text) == text
        
    def test_arrows_and_symbols(self):
        """Test handling of arrow and mathematical symbols."""
        # Some arrows might be in emoji range, adjust based on implementation
        text = "Arrow → and checkmark ✓"
        result = remove_emojis(text)
        # Allow either preservation or removal, document behavior
        assert "Arrow" in result
        assert "checkmark" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
