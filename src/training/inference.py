"""
Inference script for baseline toxicity classifier.

This script demonstrates how to load the trained baseline model
and make predictions on new text samples.

Usage:
    python src/training/inference.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from preprocessing import preprocess_pipeline
from training.baseline_model import BaselineClassifier
import pandas as pd


def predict_toxicity(text: str, classifier: BaselineClassifier) -> dict:
    """
    Predict toxicity for a single text sample.
    
    Parameters
    ----------
    text : str
        Input text to classify
    classifier : BaselineClassifier
        Trained classifier instance
    
    Returns
    -------
    results : dict
        Dictionary with predictions and probabilities for each label
    """
    # Preprocess text
    text_clean = preprocess_pipeline(text, mode='ml')
    
    # Get predictions (returns 2D array: [n_samples, n_labels])
    predictions = classifier.predict(pd.Series([text_clean]))[0]  # Get first sample
    probabilities = classifier.predict_proba(pd.Series([text_clean]))[0]  # Get first sample
    
    # Format results
    results = {
        'text': text,
        'predictions': {},
        'is_toxic': bool(predictions.any())
    }
    
    for i, label in enumerate(classifier.label_cols):
        results['predictions'][label] = {
            'predicted': bool(predictions[i]),
            'probability': float(probabilities[i])
        }
    
    return results


def main():
    """Main inference demo."""
    print("=" * 70)
    print("BASELINE TOXICITY CLASSIFIER - INFERENCE DEMO")
    print("=" * 70)
    
    # Load trained model
    print("\n[1/3] Loading trained model...")
    classifier = BaselineClassifier.load_artifacts('models/baseline')
    print("✓ Model loaded successfully")
    
    # Test samples
    test_samples = [
        "You are an idiot and should be ashamed!",
        "This is a great article, thanks for sharing.",
        "I disagree with your opinion, but I respect it.",
        "Go kill yourself, nobody likes you.",
        "What a stupid waste of time.",
        "I found this very helpful and informative."
    ]
    
    print("\n[2/3] Running predictions...")
    print("-" * 70)
    
    results = []
    for text in test_samples:
        result = predict_toxicity(text, classifier)
        results.append(result)
        
        # Display result
        print(f"\nText: {text}")
        print(f"Toxic: {'YES' if result['is_toxic'] else 'NO'}")
        
        # Show predicted labels
        predicted_labels = [
            label for label, pred in result['predictions'].items()
            if pred['predicted']
        ]
        
        if predicted_labels:
            print(f"Labels: {', '.join(predicted_labels)}")
            print("Probabilities:")
            for label in predicted_labels:
                prob = result['predictions'][label]['probability']
                print(f"  {label:15s}: {prob:.4f}")
        else:
            print("Labels: None (clean)")
    
    print("\n" + "-" * 70)
    print("\n[3/3] Summary")
    print(f"Total samples: {len(test_samples)}")
    print(f"Toxic: {sum(r['is_toxic'] for r in results)}")
    print(f"Clean: {sum(not r['is_toxic'] for r in results)}")
    
    print("\n" + "=" * 70)
    print("INFERENCE COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()
