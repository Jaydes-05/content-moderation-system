"""
Production-grade inference pipeline for DistilBERT toxicity detection.

This module provides real-time inference capabilities for the trained
DistilBERT model with proper error handling, logging, and optimization.

Architecture:
    Input Text → Preprocessing → Tokenization → DistilBERT → Sigmoid → Probabilities

Usage:
    from inference.bert_predict import BERTToxicityPredictor
    
    predictor = BERTToxicityPredictor()
    result = predictor.predict("Your text here")
"""

import os
import sys
import json
import logging
from typing import Dict, List, Union, Optional
from dataclasses import dataclass

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Add parent directory to path
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
class BERTPredictionResult:
    """
    Result object for BERT toxicity prediction.
    
    Attributes
    ----------
    text : str
        Original input text
    is_toxic : bool
        Whether any toxicity was detected
    predictions : Dict[str, float]
        Probability scores for each label (0-1)
    toxic_labels : List[str]
        List of labels that exceeded threshold
    max_score : float
        Highest probability across all labels
    """
    text: str
    is_toxic: bool
    predictions: Dict[str, float]
    toxic_labels: List[str]
    max_score: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'text': self.text,
            'is_toxic': self.is_toxic,
            'predictions': self.predictions,
            'toxic_labels': self.toxic_labels,
            'max_score': self.max_score
        }
    
    def __repr__(self) -> str:
        lines = [
            f"Text: {self.text[:80]}{'...' if len(self.text) > 80 else ''}",
            f"Toxic: {'YES' if self.is_toxic else 'NO'}",
            f"Max Score: {self.max_score:.4f}"
        ]
        
        if self.toxic_labels:
            lines.append(f"Labels: {', '.join(self.toxic_labels)}")
            lines.append("Probabilities:")
            for label in self.toxic_labels:
                lines.append(f"  {label:15s}: {self.predictions[label]:.4f}")
        else:
            lines.append("Labels: None (clean)")
        
        return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# BERT Predictor Class
# ═══════════════════════════════════════════════════════════════════════════

class BERTToxicityPredictor:
    """
    Production-grade inference interface for DistilBERT toxicity classifier.
    
    This class provides optimized real-time inference with:
    - Automatic model and tokenizer loading
    - Proper preprocessing
    - Sigmoid activation for multi-label classification
    - Configurable threshold
    - Batch prediction support
    - Error handling
    
    Parameters
    ----------
    model_dir : str, default='models/bert/final_model'
        Directory containing the trained model
    tokenizer_dir : str, default='models/bert/tokenizer'
        Directory containing the tokenizer
    threshold : float, default=0.5
        Probability threshold for positive predictions
    device : str, optional
        Device to run inference on ('cuda' or 'cpu')
        If None, automatically selects GPU if available
    max_length : int, default=128
        Maximum sequence length for tokenization
    
    Examples
    --------
    >>> predictor = BERTToxicityPredictor()
    >>> result = predictor.predict("You are an idiot!")
    >>> print(result.is_toxic)
    True
    >>> print(result.predictions)
    {'toxic': 0.97, 'insult': 0.91, ...}
    """
    
    def __init__(
        self,
        model_dir: str = 'models/bert/final_model',
        tokenizer_dir: str = 'models/bert/tokenizer',
        threshold: float = 0.5,
        device: Optional[str] = None,
        max_length: int = 128
    ):
        self.model_dir = model_dir
        self.tokenizer_dir = tokenizer_dir
        self.threshold = threshold
        self.max_length = max_length
        
        # Set device
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        # Load configuration
        self.config = self._load_config()
        self.label_cols = self.config.get('label_cols', [
            'toxic', 'severe_toxic', 'obscene', 'threat', 'insult', 'identity_hate'
        ])
        
        # Load model and tokenizer
        self.tokenizer = None
        self.model = None
        self._load_artifacts()
        
        logger.info(f"BERTToxicityPredictor initialized")
        logger.info(f"  Device: {self.device}")
        logger.info(f"  Threshold: {threshold}")
        logger.info(f"  Max length: {max_length}")
    
    def _load_config(self) -> Dict:
        """Load training configuration."""
        config_path = os.path.join(self.model_dir, 'training_config.json')
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"Config not found at {config_path}, using defaults")
            return {}
    
    def _load_artifacts(self):
        """Load model and tokenizer."""
        logger.info(f"Loading model artifacts...")
        
        # Load tokenizer
        if not os.path.exists(self.tokenizer_dir):
            raise FileNotFoundError(f"Tokenizer not found: {self.tokenizer_dir}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_dir)
        logger.info(f"✓ Loaded tokenizer from: {self.tokenizer_dir}")
        
        # Load model
        if not os.path.exists(self.model_dir):
            raise FileNotFoundError(f"Model not found: {self.model_dir}")
        
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_dir)
        self.model.to(self.device)
        self.model.eval()  # Set to evaluation mode
        logger.info(f"✓ Loaded model from: {self.model_dir}")
    
    def predict(
        self,
        text: str,
        return_dict: bool = False
    ) -> Union[BERTPredictionResult, Dict]:
        """
        Predict toxicity for a single text.
        
        Parameters
        ----------
        text : str
            Input text to classify
        return_dict : bool, default=False
            If True, return dictionary instead of BERTPredictionResult
        
        Returns
        -------
        BERTPredictionResult or dict
            Prediction result with probabilities for all labels
        
        Examples
        --------
        >>> predictor = BERTToxicityPredictor()
        >>> result = predictor.predict("You are an idiot!")
        >>> print(result.is_toxic)
        True
        >>> print(result.predictions['toxic'])
        0.9734
        """
        # Validate input
        if not text or not isinstance(text, str):
            logger.warning("Empty or invalid text provided")
            return self._empty_result(text, return_dict)
        
        # Preprocess (lightweight for transformers)
        text_clean = preprocess_pipeline(text, mode='transformer')
        
        if not text_clean or text_clean.strip() == '':
            logger.warning("Text is empty after preprocessing")
            return self._empty_result(text, return_dict)
        
        # Tokenize
        inputs = self.tokenizer(
            text_clean,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Predict
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            
            # Apply sigmoid for multi-label classification
            probs = torch.sigmoid(logits).cpu().numpy()[0]
        
        # Build predictions dictionary
        predictions = {
            label: float(prob)
            for label, prob in zip(self.label_cols, probs)
        }
        
        # Identify toxic labels (above threshold)
        toxic_labels = [
            label for label, prob in predictions.items()
            if prob > self.threshold
        ]
        
        # Create result
        result = BERTPredictionResult(
            text=text,
            is_toxic=len(toxic_labels) > 0,
            predictions=predictions,
            toxic_labels=toxic_labels,
            max_score=float(max(probs))
        )
        
        return result.to_dict() if return_dict else result
    
    def predict_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        return_dict: bool = False
    ) -> List[Union[BERTPredictionResult, Dict]]:
        """
        Predict toxicity for multiple texts (optimized batch processing).
        
        Parameters
        ----------
        texts : List[str]
            List of input texts to classify
        batch_size : int, default=32
            Batch size for processing
        return_dict : bool, default=False
            If True, return dictionaries instead of BERTPredictionResult objects
        
        Returns
        -------
        List[BERTPredictionResult] or List[dict]
            List of prediction results
        
        Examples
        --------
        >>> predictor = BERTToxicityPredictor()
        >>> texts = ["Great!", "You're stupid!"]
        >>> results = predictor.predict_batch(texts)
        >>> [r.is_toxic for r in results]
        [False, True]
        """
        logger.info(f"Predicting batch of {len(texts)} texts")
        
        results = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Preprocess
            batch_clean = [
                preprocess_pipeline(text, mode='transformer')
                for text in batch_texts
            ]
            
            # Tokenize batch
            inputs = self.tokenizer(
                batch_clean,
                truncation=True,
                padding='max_length',
                max_length=self.max_length,
                return_tensors='pt'
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Predict
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.sigmoid(logits).cpu().numpy()
            
            # Build results for batch
            for j, (text, prob_array) in enumerate(zip(batch_texts, probs)):
                predictions = {
                    label: float(prob)
                    for label, prob in zip(self.label_cols, prob_array)
                }
                
                toxic_labels = [
                    label for label, prob in predictions.items()
                    if prob > self.threshold
                ]
                
                result = BERTPredictionResult(
                    text=text,
                    is_toxic=len(toxic_labels) > 0,
                    predictions=predictions,
                    toxic_labels=toxic_labels,
                    max_score=float(max(prob_array))
                )
                
                results.append(result.to_dict() if return_dict else result)
        
        return results
    
    def _empty_result(
        self,
        text: str,
        return_dict: bool = False
    ) -> Union[BERTPredictionResult, Dict]:
        """Create empty result for invalid input."""
        predictions = {label: 0.0 for label in self.label_cols}
        
        result = BERTPredictionResult(
            text=text,
            is_toxic=False,
            predictions=predictions,
            toxic_labels=[],
            max_score=0.0
        )
        
        return result.to_dict() if return_dict else result
    
    def set_threshold(self, threshold: float):
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
    model_dir: str = 'models/bert/final_model',
    tokenizer_dir: str = 'models/bert/tokenizer',
    threshold: float = 0.5
) -> BERTPredictionResult:
    """
    Convenience function for single prediction.
    
    Parameters
    ----------
    text : str
        Input text to classify
    model_dir : str
        Directory containing the trained model
    tokenizer_dir : str
        Directory containing the tokenizer
    threshold : float
        Classification threshold
    
    Returns
    -------
    BERTPredictionResult
        Prediction result
    """
    predictor = BERTToxicityPredictor(
        model_dir=model_dir,
        tokenizer_dir=tokenizer_dir,
        threshold=threshold
    )
    return predictor.predict(text)


def predict_batch(
    texts: List[str],
    model_dir: str = 'models/bert/final_model',
    tokenizer_dir: str = 'models/bert/tokenizer',
    threshold: float = 0.5,
    batch_size: int = 32
) -> List[BERTPredictionResult]:
    """
    Convenience function for batch prediction.
    
    Parameters
    ----------
    texts : List[str]
        List of input texts to classify
    model_dir : str
        Directory containing the trained model
    tokenizer_dir : str
        Directory containing the tokenizer
    threshold : float
        Classification threshold
    batch_size : int
        Batch size for processing
    
    Returns
    -------
    List[BERTPredictionResult]
        List of prediction results
    """
    predictor = BERTToxicityPredictor(
        model_dir=model_dir,
        tokenizer_dir=tokenizer_dir,
        threshold=threshold
    )
    return predictor.predict_batch(texts, batch_size=batch_size)


# ═══════════════════════════════════════════════════════════════════════════
# CLI Interface
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """CLI interface for BERT inference."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='DistilBERT Toxicity Detection Inference',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--text',
        type=str,
        help='Single text to classify'
    )
    parser.add_argument(
        '--model-dir',
        type=str,
        default='models/bert/final_model',
        help='Model directory'
    )
    parser.add_argument(
        '--tokenizer-dir',
        type=str,
        default='models/bert/tokenizer',
        help='Tokenizer directory'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.5,
        help='Classification threshold'
    )
    parser.add_argument(
        '--examples',
        action='store_true',
        help='Run example predictions'
    )
    
    args = parser.parse_args()
    
    # Initialize predictor
    predictor = BERTToxicityPredictor(
        model_dir=args.model_dir,
        tokenizer_dir=args.tokenizer_dir,
        threshold=args.threshold
    )
    
    if args.text:
        # Single prediction
        print("\n" + "=" * 70)
        result = predictor.predict(args.text)
        print(result)
        print("=" * 70)
    
    elif args.examples:
        # Example predictions
        print("\n" + "=" * 70)
        print("EXAMPLE PREDICTIONS")
        print("=" * 70)
        
        test_cases = [
            ("Toxic - Insult", "You are an idiot and should be ashamed!"),
            ("Toxic - Threat", "I will kill you!"),
            ("Toxic - Multi-label", "You stupid f***ing idiot!"),
            ("Clean - Positive", "This is a great article, thanks!"),
            ("Clean - Neutral", "I disagree with your opinion."),
        ]
        
        for i, (label, text) in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] {label}")
            print("-" * 70)
            result = predictor.predict(text)
            print(result)
        
        print("\n" + "=" * 70)
    
    else:
        print("Use --text 'your text' or --examples")


if __name__ == '__main__':
    main()
