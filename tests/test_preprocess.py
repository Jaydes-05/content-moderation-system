"""
Unit tests for preprocessing module.

Run with:
    pytest tests/test_preprocess.py -v
    
Or without pytest:
    python tests/test_preprocess.py
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from preprocessing.preprocess import clean_text, preprocess_pipeline


# ═══════════════════════════════════════════════════════════════════════════
# Test clean_text function
# ═══════════════════════════════════════════════════════════════════════════

def test_clean_text_basic():
    """Test basic text cleaning."""
    text = "Hello World"
    result = clean_text(text)
    assert result == "hello world"


def test_clean_text_urls():
    """Test URL removal."""
    text = "Check this https://example.com and www.spam.com"
    result = clean_text(text)
    assert "https://" not in result
    assert "www." not in result
    assert "check this" in result


def test_clean_text_whitespace():
    """Test whitespace normalization."""
    text = "Hello    World\n\n\nTest"
    result = clean_text(text)
    assert result == "hello world test"


def test_clean_text_null():
    """Test null input handling."""
    assert clean_text(None) == ""
    assert clean_text("") == ""
    assert clean_text("   ") == ""


def test_clean_text_preserve_punctuation():
    """Test punctuation preservation."""
    text = "Hello! How are you?"
    result = clean_text(text, preserve_punctuation=True)
    assert "!" in result
    assert "?" in result


def test_clean_text_remove_punctuation():
    """Test punctuation removal."""
    text = "Hello! How are you?"
    result = clean_text(text, preserve_punctuation=False)
    assert "!" not in result
    assert "?" not in result


def test_clean_text_lowercase_off():
    """Test with lowercase disabled."""
    text = "HELLO World"
    result = clean_text(text, lowercase=False)
    assert result == "HELLO World"


def test_clean_text_emojis():
    """Test emoji preservation."""
    text = "I'm angry 😡😡😡"
    result = clean_text(text)
    assert "😡" in result


def test_clean_text_control_chars():
    """Test control character removal."""
    text = "Hello\x00World\t\twith\rchars"
    result = clean_text(text)
    assert "\x00" not in result
    # Tabs and carriage returns are converted to spaces then collapsed
    assert "hello" in result and "world" in result and "chars" in result


# ═══════════════════════════════════════════════════════════════════════════
# Test preprocess_pipeline function
# ═══════════════════════════════════════════════════════════════════════════

def test_pipeline_default():
    """Test default pipeline mode."""
    text = "HELLO WORLD!!!"
    result = preprocess_pipeline(text, mode='default')
    assert result == "hello world!!!"


def test_pipeline_ml():
    """Test ML pipeline mode."""
    text = "HELLO WORLD!!!"
    result = preprocess_pipeline(text, mode='ml')
    assert "!" not in result
    assert result.islower()


def test_pipeline_transformer():
    """Test transformer pipeline mode."""
    text = "HELLO WORLD!!!"
    result = preprocess_pipeline(text, mode='transformer')
    assert "HELLO" in result  # Case preserved
    assert "!" in result      # Punctuation preserved


def test_pipeline_invalid_mode():
    """Test invalid mode raises error."""
    try:
        preprocess_pipeline("test", mode='invalid')
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "mode must be one of" in str(e)


def test_pipeline_with_urls():
    """Test that all modes remove URLs."""
    text = "Check https://example.com for info"
    
    for mode in ['default', 'ml', 'transformer']:
        result = preprocess_pipeline(text, mode=mode)
        assert "https://" not in result


# ═══════════════════════════════════════════════════════════════════════════
# Real-world test cases
# ═══════════════════════════════════════════════════════════════════════════

def test_toxic_comment_realistic():
    """Test with realistic toxic comment."""
    text = "You're an IDIOT!!! Go to https://spam.com    😡😡"
    result = clean_text(text)
    
    assert result.islower()
    assert "https://" not in result
    assert "idiot" in result
    assert "!" in result  # Punctuation preserved
    assert "😡" in result  # Emoji preserved


def test_nontoxic_comment_realistic():
    """Test with realistic non-toxic comment."""
    text = "Great article!   Thanks for sharing.  \n\nSee more at www.example.com"
    result = clean_text(text)
    
    assert "great article" in result
    assert "www." not in result
    assert "thanks for sharing" in result


def test_empty_after_cleaning():
    """Test text that becomes empty after cleaning."""
    text = "https://example.com"
    result = clean_text(text)
    assert result == ""


def test_multilingual():
    """Test with non-English characters."""
    text = "Bonjour! ¿Cómo estás? 你好"
    result = clean_text(text)
    
    # Should preserve non-ASCII letters
    assert "bonjour" in result
    assert "cómo" in result or "como" in result
    assert "你好" in result


# ═══════════════════════════════════════════════════════════════════════════
# Run tests without pytest
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 70)
    print("RUNNING UNIT TESTS")
    print("=" * 70)
    
    test_functions = [
        test_clean_text_basic,
        test_clean_text_urls,
        test_clean_text_whitespace,
        test_clean_text_null,
        test_clean_text_preserve_punctuation,
        test_clean_text_remove_punctuation,
        test_clean_text_lowercase_off,
        test_clean_text_emojis,
        test_clean_text_control_chars,
        test_pipeline_default,
        test_pipeline_ml,
        test_pipeline_transformer,
        test_pipeline_invalid_mode,
        test_pipeline_with_urls,
        test_toxic_comment_realistic,
        test_nontoxic_comment_realistic,
        test_empty_after_cleaning,
        test_multilingual
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: {type(e).__name__}: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed > 0:
        sys.exit(1)
