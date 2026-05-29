"""
Inference utilities for toxicity detection.
"""

from .predict import ToxicityPredictor, predict_single, predict_batch

__all__ = ['ToxicityPredictor', 'predict_single', 'predict_batch']
