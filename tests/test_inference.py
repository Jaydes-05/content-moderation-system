"""
Unit tests for inference module.

Run with:
    pytest tests/test_inference.py -v
    
Or without pytest:
    python tests/test_inference.py
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from inference.predict import ToxicityPredictor, predict_single, predict_batch


# ═══════════════════════════════════════════════════════════════════════════
# Test ToxicityPredictor
# ═══════════════════════════════════════════════════════════════════════════

def test_predictor_initialization():
    """Test predictor can be initialized."""
    predictor = ToxicityPredictor()
    assert predictor is not None
    assert predictor.vectorizer is not None
    assert predictor.model is not None
    assert len(predictor.label_cols) == 6


def test_predict_toxic_text():
    """Test prediction on toxic text."""
    predictor = ToxicityPredictor()
    result = predictor.predict("You are an idiot!")
    
    assert result.is_toxic == True
    assert len(result.toxic_labels) > 0
    assert 'toxic' in result.toxic_labels or 'insult' in result.toxic_labels
    assert result.max_toxicity_score > 0.5


def test_predict_clean_text():
    """Test prediction on clean text."""
    predictor = ToxicityPredictor()
    result = predictor.predict("This is a great article, thanks!")
    
    assert result.is_toxic == False
    assert len(result.toxic_labels) == 0
    assert result.max_toxicity_score < 0.5


def test_predict_empty_text():
    """Test prediction on empty text."""
    predictor = ToxicityPredictor()
    result = predictor.predict("")
    
    assert result.is_toxic == False
    assert len(result.toxic_labels) == 0
    assert result.max_toxicity_score == 0.0


def test_predict_return_dict():
    """Test prediction returns dictionary when requested."""
    predictor = ToxicityPredictor()
    result = predictor.predict("Test text", return_dict=True)
    
    assert isinstance(result, dict)
    assert 'text' in result
    assert 'is_toxic' in result
    assert 'toxic_labels' in result
    assert 'predictions' in result
    assert 'max_toxicity_score' in result


def test_predict_batch():
    """Test batch prediction."""
    predictor = ToxicityPredictor()
    texts = [
        "This is a great article!",
        "You are stupid!",
        "I disagree with you."
    ]
    
    results = predictor.predict_batch(texts)
    
    assert len(results) == 3
    assert results[0].is_toxic == False  # "This is a great article!"
    assert results[1].is_toxic == True   # "You are stupid!"
    assert results[2].is_toxic == False  # "I disagree with you."


def test_threshold_adjustment():
    """Test threshold can be adjusted."""
    predictor = ToxicityPredictor(threshold=0.5)
    
    # Change threshold
    predictor.set_threshold(0.7)
    assert predictor.threshold == 0.7
    
    # Invalid threshold should raise error
    try:
        predictor.set_threshold(1.5)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_result_to_dict():
    """Test ToxicityResult can be converted to dict."""
    predictor = ToxicityPredictor()
    result = predictor.predict("Test text")
    
    result_dict = result.to_dict()
    
    assert isinstance(result_dict, dict)
    assert 'text' in result_dict
    assert 'is_toxic' in result_dict
    assert 'toxic_labels' in result_dict


# ═══════════════════════════════════════════════════════════════════════════
# Test Convenience Functions
# ═══════════════════════════════════════════════════════════════════════════

def test_predict_single_function():
    """Test predict_single convenience function."""
    result = predict_single("You are an idiot!")
    
    assert result.is_toxic == True
    assert len(result.toxic_labels) > 0


def test_predict_batch_function():
    """Test predict_batch convenience function."""
    texts = ["Great!", "Stupid!"]
    results = predict_batch(texts)
    
    assert len(results) == 2
    assert results[0].is_toxic == False
    assert results[1].is_toxic == True


# ═══════════════════════════════════════════════════════════════════════════
# Test Edge Cases
# ═══════════════════════════════════════════════════════════════════════════

def test_predict_long_text():
    """Test prediction on very long text."""
    predictor = ToxicityPredictor()
    long_text = "This is a test. " * 1000  # 1000 repetitions
    
    result = predictor.predict(long_text)
    
    assert result is not None
    assert isinstance(result.is_toxic, bool)


def test_predict_special_characters():
    """Test prediction with special characters."""
    predictor = ToxicityPredictor()
    text = "Hello!!! @#$%^&*() 😀😃😄"
    
    result = predictor.predict(text)
    
    assert result is not None
    assert isinstance(result.is_toxic, bool)


def test_predict_urls():
    """Test prediction with URLs."""
    predictor = ToxicityPredictor()
    text = "Check this out: https://example.com"
    
    result = predictor.predict(text)
    
    assert result is not None
    assert isinstance(result.is_toxic, bool)


def test_predict_multilingual():
    """Test prediction with non-English text."""
    predictor = ToxicityPredictor()
    text = "Bonjour! ¿Cómo estás?"
    
    result = predictor.predict(text)
    
    assert result is not None
    assert isinstance(result.is_toxic, bool)


# ═══════════════════════════════════════════════════════════════════════════
# Test Label Predictions
# ═══════════════════════════════════════════════════════════════════════════

def test_all_labels_present():
    """Test that all 6 labels are in predictions."""
    predictor = ToxicityPredictor()
    result = predictor.predict("Test text")
    
    assert len(result.predictions) == 6
    
    expected_labels = {'toxic', 'severe_toxic', 'obscene', 'threat', 'insult', 'identity_hate'}
    actual_labels = {pred.label for pred in result.predictions}
    
    assert expected_labels == actual_labels


def test_probability_range():
    """Test that probabilities are in valid range."""
    predictor = ToxicityPredictor()
    result = predictor.predict("You are an idiot!")
    
    for pred in result.predictions:
        assert 0.0 <= pred.probability <= 1.0


# ═══════════════════════════════════════════════════════════════════════════
# Run tests without pytest
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 70)
    print("RUNNING INFERENCE TESTS")
    print("=" * 70)
    
    test_functions = [
        test_predictor_initialization,
        test_predict_toxic_text,
        test_predict_clean_text,
        test_predict_empty_text,
        test_predict_return_dict,
        test_predict_batch,
        test_threshold_adjustment,
        test_result_to_dict,
        test_predict_single_function,
        test_predict_batch_function,
        test_predict_long_text,
        test_predict_special_characters,
        test_predict_urls,
        test_predict_multilingual,
        test_all_labels_present,
        test_probability_range
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"PASS {test_func.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {test_func.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"FAIL {test_func.__name__}: {type(e).__name__}: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed > 0:
        sys.exit(1)
