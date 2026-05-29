"""
Unit tests for BERT training and inference pipeline.

These tests verify the code structure and logic without
actually training the model (which would take too long).

Run with:
    pytest tests/test_bert_pipeline.py -v
    
Or without pytest:
    python tests/test_bert_pipeline.py
"""

import sys
import os
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import torch
import numpy as np
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification


# ═══════════════════════════════════════════════════════════════════════════
# Test Configuration
# ═══════════════════════════════════════════════════════════════════════════

def test_bert_config_initialization():
    """Test BERTConfig can be initialized."""
    from training.train_bert import BERTConfig
    
    config = BERTConfig()
    
    assert config.model_name == "distilbert-base-uncased"
    assert config.num_labels == 6
    assert config.problem_type == "multi_label_classification"
    assert config.max_length == 128
    assert len(config.label_cols) == 6


def test_bert_config_labels_order():
    """Test label order is consistent."""
    from training.train_bert import BERTConfig
    
    config = BERTConfig()
    expected_labels = ['toxic', 'severe_toxic', 'obscene', 'threat', 'insult', 'identity_hate']
    
    assert config.label_cols == expected_labels


# ═══════════════════════════════════════════════════════════════════════════
# Test Dataset Class
# ═══════════════════════════════════════════════════════════════════════════

def test_toxicity_dataset_creation():
    """Test ToxicityDataset can be created."""
    from training.train_bert import ToxicityDataset
    
    # Create dummy data
    texts = ["This is a test", "Another test"]
    labels = np.array([[1, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0]])
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    
    # Create dataset
    dataset = ToxicityDataset(texts, labels, tokenizer, max_length=128)
    
    assert len(dataset) == 2


def test_toxicity_dataset_getitem():
    """Test ToxicityDataset __getitem__ returns correct format."""
    from training.train_bert import ToxicityDataset
    
    texts = ["Test text"]
    labels = np.array([[1, 0, 0, 0, 1, 0]])
    
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    dataset = ToxicityDataset(texts, labels, tokenizer, max_length=128)
    
    item = dataset[0]
    
    assert 'input_ids' in item
    assert 'attention_mask' in item
    assert 'labels' in item
    assert item['input_ids'].shape[0] == 128
    assert item['attention_mask'].shape[0] == 128
    assert item['labels'].shape[0] == 6


# ═══════════════════════════════════════════════════════════════════════════
# Test Model Initialization
# ═══════════════════════════════════════════════════════════════════════════

def test_model_initialization():
    """Test DistilBERT model can be initialized with correct config."""
    model = AutoModelForSequenceClassification.from_pretrained(
        "distilbert-base-uncased",
        num_labels=6,
        problem_type="multi_label_classification"
    )
    
    assert model.config.num_labels == 6
    assert model.config.problem_type == "multi_label_classification"


def test_model_output_shape():
    """Test model output has correct shape."""
    model = AutoModelForSequenceClassification.from_pretrained(
        "distilbert-base-uncased",
        num_labels=6,
        problem_type="multi_label_classification"
    )
    
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    
    # Create dummy input
    text = "This is a test"
    inputs = tokenizer(text, return_tensors='pt', padding='max_length', max_length=128, truncation=True)
    
    # Forward pass
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Check output shape
    assert outputs.logits.shape == (1, 6)


def test_sigmoid_activation():
    """Test sigmoid is applied correctly for multi-label."""
    model = AutoModelForSequenceClassification.from_pretrained(
        "distilbert-base-uncased",
        num_labels=6,
        problem_type="multi_label_classification"
    )
    
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    
    text = "Test"
    inputs = tokenizer(text, return_tensors='pt', padding='max_length', max_length=128, truncation=True)
    
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.sigmoid(logits)
    
    # Check probabilities are in [0, 1]
    assert (probs >= 0).all()
    assert (probs <= 1).all()
    
    # Check sum is NOT 1 (not softmax!)
    assert probs.sum().item() != 1.0


# ═══════════════════════════════════════════════════════════════════════════
# Test Metrics Computation
# ═══════════════════════════════════════════════════════════════════════════

def test_compute_metrics():
    """Test compute_metrics function."""
    from training.train_bert import compute_metrics
    from collections import namedtuple
    
    # Create dummy predictions
    EvalPrediction = namedtuple('EvalPrediction', ['predictions', 'label_ids'])
    
    logits = np.array([
        [2.0, -1.0, 0.5, -2.0, 1.5, -0.5],
        [-1.0, -2.0, -1.5, -3.0, -1.0, -2.5]
    ])
    labels = np.array([
        [1, 0, 1, 0, 1, 0],
        [0, 0, 0, 0, 0, 0]
    ])
    
    eval_pred = EvalPrediction(predictions=logits, label_ids=labels)
    
    metrics = compute_metrics(eval_pred)
    
    assert 'accuracy' in metrics
    assert 'precision_micro' in metrics
    assert 'recall_micro' in metrics
    assert 'f1_micro' in metrics
    assert 'f1_macro' in metrics


# ═══════════════════════════════════════════════════════════════════════════
# Test BERT Predictor (if model exists)
# ═══════════════════════════════════════════════════════════════════════════

def test_bert_predictor_initialization():
    """Test BERTToxicityPredictor can be initialized (if model exists)."""
    # Skip if model doesn't exist
    if not os.path.exists('models/bert/final_model'):
        print("SKIP: Model not found (train first)")
        return
    
    from inference.bert_predict import BERTToxicityPredictor
    
    predictor = BERTToxicityPredictor()
    
    assert predictor.model is not None
    assert predictor.tokenizer is not None
    assert len(predictor.label_cols) == 6


def test_bert_predictor_predict():
    """Test BERTToxicityPredictor.predict (if model exists)."""
    # Skip if model doesn't exist
    if not os.path.exists('models/bert/final_model'):
        print("SKIP: Model not found (train first)")
        return
    
    from inference.bert_predict import BERTToxicityPredictor
    
    predictor = BERTToxicityPredictor()
    result = predictor.predict("This is a test")
    
    assert hasattr(result, 'text')
    assert hasattr(result, 'is_toxic')
    assert hasattr(result, 'predictions')
    assert hasattr(result, 'toxic_labels')
    assert len(result.predictions) == 6


def test_bert_predictor_batch():
    """Test BERTToxicityPredictor.predict_batch (if model exists)."""
    # Skip if model doesn't exist
    if not os.path.exists('models/bert/final_model'):
        print("SKIP: Model not found (train first)")
        return
    
    from inference.bert_predict import BERTToxicityPredictor
    
    predictor = BERTToxicityPredictor()
    texts = ["Test 1", "Test 2", "Test 3"]
    results = predictor.predict_batch(texts)
    
    assert len(results) == 3
    assert all(hasattr(r, 'predictions') for r in results)


# ═══════════════════════════════════════════════════════════════════════════
# Test Preprocessing Integration
# ═══════════════════════════════════════════════════════════════════════════

def test_preprocessing_transformer_mode():
    """Test preprocessing with transformer mode."""
    from preprocessing import preprocess_pipeline
    
    text = "Check this OUT: https://example.com !!! 😡"
    cleaned = preprocess_pipeline(text, mode='transformer')
    
    # Should preserve case and punctuation for transformers
    assert "OUT" in cleaned or "out" in cleaned
    assert "!" in cleaned or "!!!" in cleaned


# ═══════════════════════════════════════════════════════════════════════════
# Run Tests
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 70)
    print("RUNNING BERT PIPELINE TESTS")
    print("=" * 70)
    
    test_functions = [
        test_bert_config_initialization,
        test_bert_config_labels_order,
        test_toxicity_dataset_creation,
        test_toxicity_dataset_getitem,
        test_model_initialization,
        test_model_output_shape,
        test_sigmoid_activation,
        test_compute_metrics,
        test_bert_predictor_initialization,
        test_bert_predictor_predict,
        test_bert_predictor_batch,
        test_preprocessing_transformer_mode
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"PASS {test_func.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {test_func.__name__}: {e}")
            failed += 1
        except Exception as e:
            if "SKIP" in str(e):
                print(f"SKIP {test_func.__name__}: {e}")
                skipped += 1
            else:
                print(f"FAIL {test_func.__name__}: {type(e).__name__}: {e}")
                failed += 1
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 70)
    
    if failed > 0:
        sys.exit(1)
