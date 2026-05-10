"""
Inference pipeline for baseline toxicity detection model.

This module provides a clean interface for making predictions with the trained
baseline model. It's designed to be reusable for both CLI and API deployments.

Architecture:
    - ToxicityPredictor: Main class for loading model and making predictions
    - predict_single: Convenience function for single text prediction
    - predict_batch: Convenience function for batch predictions

Usage:
    # CLI
    python src/inference/predict.py
    
    # Programmatic
    from inference.predict import ToxicityPredictor
    predictor = ToxicityPredictor()
    result = predictor.predict("Your text here")
"""

import os
import sys
import pickle
import logging
from typing import Dict, List, Union, Optional
from dataclasses import dataclass, asdict

import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from preprocessing import preprocess_pipeline

# ── Configure logging ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class LabelPrediction:
    """Prediction for a single toxicity label."""
    label: str
    predicted: bool
    probability: float
    
    def __repr__(self):
        status = "✓" if self.predicted else "✗"
        return f"{status} {self.label:15s}: {self.probability:.4f}"


@dataclass
class ToxicityResult:
    """Complete toxicity prediction result."""
    text: str
    is_toxic: bool
    toxic_labels: List[str]
    predictions: List[LabelPrediction]
    max_toxicity_score: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary (useful for JSON serialization)."""
        return {
            'text': self.text,
            'is_toxic': self.is_toxic,
            'toxic_labels': self.toxic_labels,
            'max_toxicity_score': self.max_toxicity_score,
            'predictions': [
                {
                    'label': p.label,
                    'predicted': p.predicted,
                    'probability': p.probability
                }
                for p in self.predictions
            ]
        }
    
    def __repr__(self):
        lines = [
            f"Text: {self.text[:80]}{'...' if len(self.text) > 80 else ''}",
            f"Toxic: {'YES' if self.is_toxic else 'NO'}",
            f"Max Score: {self.max_toxicity_score:.4f}"
        ]
        
        if self.toxic_labels:
            lines.append(f"Labels: {', '.join(self.toxic_labels)}")
            lines.append("Predictions:")
            for pred in self.predictions:
                if pred.predicted:
                    lines.append(f"  {pred}")
        else:
            lines.append("Labels: None (clean)")
        
        return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# Main Predictor Class
# ═══════════════════════════════════════════════════════════════════════════

class ToxicityPredictor:
    """
    Toxicity prediction interface for the baseline model.
    
    This class provides a clean, reusable interface for making predictions
    with the trained TF-IDF + Logistic Regression model.
    
    Attributes
    ----------
    vectorizer : TfidfVectorizer
        Loaded TF-IDF vectorizer
    model : OneVsRestClassifier
        Loaded multi-label classifier
    label_cols : List[str]
        Names of toxicity labels
    threshold : float
        Probability threshold for positive predictions (default: 0.5)
    
    Parameters
    ----------
    model_dir : str, default='models/baseline'
        Directory containing model artifacts
    threshold : float, default=0.5
        Probability threshold for classification
    """
    
    def __init__(
        self,
        model_dir: str = 'models/baseline',
        threshold: float = 0.5
    ):
        self.model_dir = model_dir
        self.threshold = threshold
        self.label_cols = [
            'toxic', 'severe_toxic', 'obscene',
            'threat', 'insult', 'identity_hate'
        ]
        
        # Load artifacts
        self.vectorizer = None
        self.model = None
        self._load_artifacts()
        
        logger.info(f"ToxicityPredictor initialized (threshold={threshold})")
    
    def _load_artifacts(self) -> None:
        """Load trained model artifacts."""
        logger.info(f"Loading model artifacts from: {self.model_dir}")
        
        # Load vectorizer
        vectorizer_path = os.path.join(self.model_dir, 'tfidf_vectorizer.pkl')
        if not os.path.exists(vectorizer_path):
            raise FileNotFoundError(f"Vectorizer not found: {vectorizer_path}")
        
        with open(vectorizer_path, 'rb') as f:
            self.vectorizer = pickle.load(f)
        logger.info("✓ Loaded TF-IDF vectorizer")
        
        # Load model
        model_path = os.path.join(self.model_dir, 'logistic_model.pkl')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        logger.info("✓ Loaded Logistic Regression model")
    
    def predict(
        self,
        text: str,
        return_dict: bool = False
    ) -> Union[ToxicityResult, Dict]:
        """
        Predict toxicity for a single text sample.
        
        Parameters
        ----------
        text : str
            Input text to classify
        return_dict : bool, default=False
            If True, return dictionary instead of ToxicityResult object
        
        Returns
        -------
        result : ToxicityResult or Dict
            Prediction result with labels and probabilities
        
        Examples
        --------
        >>> predictor = ToxicityPredictor()
        >>> result = predictor.predict("You are an idiot!")
        >>> print(result.is_toxic)
        True
        >>> print(result.toxic_labels)
        ['toxic', 'insult']
        """
        # Preprocess text
        text_clean = preprocess_pipeline(text, mode='ml')
        
        # Handle empty text after preprocessing
        if not text_clean or text_clean.strip() == '':
            logger.warning("Text is empty after preprocessing")
            return self._empty_result(text, return_dict)
        
        # Vectorize
        X_tfidf = self.vectorizer.transform([text_clean])
        
        # Get predictions and probabilities
        predictions = self.model.predict(X_tfidf)[0]
        
        # Get probabilities using decision function + sigmoid
        from scipy.special import expit
        decision_scores = self.model.decision_function(X_tfidf)[0]
        probabilities = expit(decision_scores)
        
        # Build result
        label_predictions = []
        toxic_labels = []
        
        for i, label in enumerate(self.label_cols):
            is_predicted = bool(predictions[i])
            prob = float(probabilities[i])
            
            label_pred = LabelPrediction(
                label=label,
                predicted=is_predicted,
                probability=prob
            )
            label_predictions.append(label_pred)
            
            if is_predicted:
                toxic_labels.append(label)
        
        result = ToxicityResult(
            text=text,
            is_toxic=len(toxic_labels) > 0,
            toxic_labels=toxic_labels,
            predictions=label_predictions,
            max_toxicity_score=float(probabilities.max())
        )
        
        return result.to_dict() if return_dict else result
    
    def predict_batch(
        self,
        texts: List[str],
        return_dict: bool = False
    ) -> List[Union[ToxicityResult, Dict]]:
        """
        Predict toxicity for multiple text samples.
        
        Parameters
        ----------
        texts : List[str]
            List of input texts to classify
        return_dict : bool, default=False
            If True, return dictionaries instead of ToxicityResult objects
        
        Returns
        -------
        results : List[ToxicityResult] or List[Dict]
            List of prediction results
        
        Examples
        --------
        >>> predictor = ToxicityPredictor()
        >>> texts = ["You're great!", "You're an idiot!"]
        >>> results = predictor.predict_batch(texts)
        >>> [r.is_toxic for r in results]
        [False, True]
        """
        logger.info(f"Predicting batch of {len(texts)} texts")
        
        results = []
        for text in texts:
            result = self.predict(text, return_dict=return_dict)
            results.append(result)
        
        return results
    
    def _empty_result(
        self,
        text: str,
        return_dict: bool = False
    ) -> Union[ToxicityResult, Dict]:
        """Create empty result for invalid input."""
        label_predictions = [
            LabelPrediction(label=label, predicted=False, probability=0.0)
            for label in self.label_cols
        ]
        
        result = ToxicityResult(
            text=text,
            is_toxic=False,
            toxic_labels=[],
            predictions=label_predictions,
            max_toxicity_score=0.0
        )
        
        return result.to_dict() if return_dict else result
    
    def set_threshold(self, threshold: float) -> None:
        """
        Update the classification threshold.
        
        Parameters
        ----------
        threshold : float
            New threshold value (0.0 to 1.0)
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        
        self.threshold = threshold
        logger.info(f"Updated threshold to {threshold}")


# ═══════════════════════════════════════════════════════════════════════════
# Convenience Functions
# ═══════════════════════════════════════════════════════════════════════════

def predict_single(
    text: str,
    model_dir: str = 'models/baseline',
    threshold: float = 0.5
) -> ToxicityResult:
    """
    Convenience function for single prediction.
    
    Parameters
    ----------
    text : str
        Input text to classify
    model_dir : str, default='models/baseline'
        Directory containing model artifacts
    threshold : float, default=0.5
        Classification threshold
    
    Returns
    -------
    result : ToxicityResult
        Prediction result
    """
    predictor = ToxicityPredictor(model_dir=model_dir, threshold=threshold)
    return predictor.predict(text)


def predict_batch(
    texts: List[str],
    model_dir: str = 'models/baseline',
    threshold: float = 0.5
) -> List[ToxicityResult]:
    """
    Convenience function for batch prediction.
    
    Parameters
    ----------
    texts : List[str]
        List of input texts to classify
    model_dir : str, default='models/baseline'
        Directory containing model artifacts
    threshold : float, default=0.5
        Classification threshold
    
    Returns
    -------
    results : List[ToxicityResult]
        List of prediction results
    """
    predictor = ToxicityPredictor(model_dir=model_dir, threshold=threshold)
    return predictor.predict_batch(texts)


# ═══════════════════════════════════════════════════════════════════════════
# CLI Interface
# ═══════════════════════════════════════════════════════════════════════════

def run_interactive_mode():
    """Run interactive prediction mode."""
    print("=" * 70)
    print("TOXICITY DETECTION - INTERACTIVE MODE")
    print("=" * 70)
    print("\nType 'quit' or 'exit' to stop")
    print("Type 'examples' to see test cases")
    print("-" * 70)
    
    # Initialize predictor
    predictor = ToxicityPredictor()
    
    while True:
        print("\n" + "=" * 70)
        user_input = input("Enter text to analyze: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break
        
        if user_input.lower() == 'examples':
            run_examples()
            continue
        
        if not user_input:
            print("⚠️  Please enter some text")
            continue
        
        # Make prediction
        print("\n" + "-" * 70)
        result = predictor.predict(user_input)
        print(result)
        print("-" * 70)


def run_examples():
    """Run prediction on example test cases."""
    print("\n" + "=" * 70)
    print("EXAMPLE TEST CASES")
    print("=" * 70)
    
    # Initialize predictor
    predictor = ToxicityPredictor()
    
    # Test cases
    test_cases = [
        # Toxic examples
        {
            'category': 'Toxic - Insult',
            'text': 'You are an idiot and should be ashamed of yourself!'
        },
        {
            'category': 'Toxic - Threat',
            'text': 'Go kill yourself, nobody likes you anyway.'
        },
        {
            'category': 'Toxic - Obscene',
            'text': 'What the f*** is wrong with you, you stupid piece of s***?'
        },
        {
            'category': 'Toxic - Identity Hate',
            'text': 'All [group] are terrible people and should leave.'
        },
        {
            'category': 'Toxic - Severe',
            'text': 'I hope you die in a fire, you worthless scum.'
        },
        
        # Non-toxic examples
        {
            'category': 'Non-Toxic - Positive',
            'text': 'This is a great article, thanks for sharing!'
        },
        {
            'category': 'Non-Toxic - Neutral',
            'text': 'I disagree with your opinion, but I respect your perspective.'
        },
        {
            'category': 'Non-Toxic - Question',
            'text': 'Can you please explain this concept in more detail?'
        },
        {
            'category': 'Non-Toxic - Constructive',
            'text': 'I think there might be a better approach to this problem.'
        },
        {
            'category': 'Non-Toxic - Informative',
            'text': 'According to recent studies, this method has proven effective.'
        },
        
        # Edge cases
        {
            'category': 'Edge Case - Borderline',
            'text': 'This is stupid and a waste of time.'
        },
        {
            'category': 'Edge Case - Sarcasm',
            'text': 'Oh great, another brilliant idea from the genius over here.'
        }
    ]
    
    # Run predictions
    for i, case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {case['category']}")
        print("-" * 70)
        
        result = predictor.predict(case['text'])
        print(result)
    
    print("\n" + "=" * 70)
    print("EXAMPLES COMPLETE")
    print("=" * 70)


def run_batch_mode():
    """Run batch prediction from file or list."""
    print("=" * 70)
    print("TOXICITY DETECTION - BATCH MODE")
    print("=" * 70)
    
    # Sample batch
    texts = [
        "You are an idiot!",
        "This is a great article.",
        "I disagree with you.",
        "Go kill yourself!",
        "Thanks for the helpful information.",
        "What a stupid waste of time."
    ]
    
    print(f"\nProcessing {len(texts)} texts...")
    print("-" * 70)
    
    # Initialize predictor
    predictor = ToxicityPredictor()
    
    # Predict batch
    results = predictor.predict_batch(texts)
    
    # Display results
    for i, result in enumerate(results, 1):
        print(f"\n[{i}/{len(results)}]")
        print(result)
        print("-" * 70)
    
    # Summary
    toxic_count = sum(r.is_toxic for r in results)
    clean_count = len(results) - toxic_count
    
    print(f"\nSummary:")
    print(f"  Total: {len(results)}")
    print(f"  Toxic: {toxic_count} ({toxic_count/len(results)*100:.1f}%)")
    print(f"  Clean: {clean_count} ({clean_count/len(results)*100:.1f}%)")
    
    print("\n" + "=" * 70)


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Toxicity Detection Inference Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python src/inference/predict.py
  
  # Run example test cases
  python src/inference/predict.py --examples
  
  # Batch mode
  python src/inference/predict.py --batch
  
  # Single prediction
  python src/inference/predict.py --text "Your text here"
        """
    )
    
    parser.add_argument(
        '--text',
        type=str,
        help='Single text to classify'
    )
    parser.add_argument(
        '--examples',
        action='store_true',
        help='Run example test cases'
    )
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Run batch prediction demo'
    )
    parser.add_argument(
        '--model-dir',
        type=str,
        default='models/baseline',
        help='Directory containing model artifacts (default: models/baseline)'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.5,
        help='Classification threshold (default: 0.5)'
    )
    
    args = parser.parse_args()
    
    # Single prediction
    if args.text:
        predictor = ToxicityPredictor(
            model_dir=args.model_dir,
            threshold=args.threshold
        )
        result = predictor.predict(args.text)
        print("\n" + "=" * 70)
        print(result)
        print("=" * 70)
    
    # Examples mode
    elif args.examples:
        run_examples()
    
    # Batch mode
    elif args.batch:
        run_batch_mode()
    
    # Interactive mode (default)
    else:
        run_interactive_mode()


if __name__ == '__main__':
    main()
