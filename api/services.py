"""
Business logic services for the API.

This module contains the core service classes that handle
model inference and moderation logic.
"""

import logging
from typing import Dict, List
from pathlib import Path

from src.inference.bert_predict import BERTToxicityPredictor
from src.moderation import ContentModerator

logger = logging.getLogger(__name__)


class ModelService:
    """
    Service for managing ML models and predictions.
    
    This class handles model loading and inference operations.
    Models are loaded once during initialization and reused for all requests.
    """
    
    def __init__(self):
        """Initialize the model service."""
        self.predictor: BERTToxicityPredictor = None
        self.moderator: ContentModerator = None
        self._is_loaded = False
    
    def load_models(self, model_dir: str = "models/bert/final_model", preset: str = "moderate"):
        """
        Load BERT model and moderation engine.
        
        Parameters
        ----------
        model_dir : str
            Directory containing the trained BERT model
        preset : str
            Moderation preset to use
        
        Raises
        ------
        FileNotFoundError
            If model files are not found
        Exception
            If model loading fails
        """
        try:
            logger.info("Loading models...")
            
            # Check if model exists
            if not Path(model_dir).exists():
                raise FileNotFoundError(
                    f"Model not found at {model_dir}. "
                    f"Please train the model first using: python train_bert_10k.py"
                )
            
            # Load BERT predictor
            logger.info(f"Loading BERT model from {model_dir}")
            self.predictor = BERTToxicityPredictor(
                model_dir=model_dir,
                tokenizer_dir="models/bert/tokenizer"
            )
            logger.info("✓ BERT model loaded")
            
            # Load moderation engine
            logger.info(f"Loading moderation engine with preset: {preset}")
            self.moderator = ContentModerator.from_preset(preset)
            logger.info("✓ Moderation engine loaded")
            
            self._is_loaded = True
            logger.info("All models loaded successfully")
            
        except FileNotFoundError as e:
            logger.error(f"Model files not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading models: {e}", exc_info=True)
            raise
    
    def is_loaded(self) -> bool:
        """Check if models are loaded."""
        return self._is_loaded
    
    def predict(self, text: str) -> Dict:
        """
        Get toxicity predictions for text.
        
        Parameters
        ----------
        text : str
            Input text to analyze
        
        Returns
        -------
        dict
            Prediction results
        
        Raises
        ------
        RuntimeError
            If models are not loaded
        """
        if not self._is_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        try:
            # Get prediction
            result = self.predictor.predict(text)
            
            # Convert to dict
            return {
                'text': result.text,
                'is_toxic': result.is_toxic,
                'predictions': result.predictions,
                'toxic_labels': result.toxic_labels,
                'max_score': result.max_score,
                'confidence': result.max_score  # Use max_score as confidence
            }
        
        except Exception as e:
            logger.error(f"Prediction error: {e}", exc_info=True)
            raise
    
    def moderate(self, text: str) -> Dict:
        """
        Get moderation decision for text.
        
        Parameters
        ----------
        text : str
            Input text to analyze
        
        Returns
        -------
        dict
            Moderation results including prediction and decision
        
        Raises
        ------
        RuntimeError
            If models are not loaded
        """
        if not self._is_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        try:
            # Get prediction
            prediction = self.predictor.predict(text)
            
            # Get moderation decision
            moderation = self.moderator.moderate(
                predictions=prediction.predictions,
                text=text
            )
            
            # Combine results
            return {
                'text': prediction.text,
                'is_toxic': prediction.is_toxic,
                'predictions': prediction.predictions,
                'action': moderation.action,
                'severity': moderation.severity,
                'primary_label': moderation.primary_label,
                'confidence': moderation.confidence,
                'explanation': moderation.explanation
            }
        
        except Exception as e:
            logger.error(f"Moderation error: {e}", exc_info=True)
            raise
    
    def moderate_batch(self, texts: List[str]) -> Dict:
        """
        Get moderation decisions for multiple texts.
        
        Parameters
        ----------
        texts : List[str]
            List of input texts to analyze
        
        Returns
        -------
        dict
            Batch moderation results with statistics
        
        Raises
        ------
        RuntimeError
            If models are not loaded
        """
        if not self._is_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        try:
            results = []
            
            # Process each text
            for text in texts:
                result = self.moderate(text)
                results.append(result)
            
            # Calculate statistics
            toxic_count = sum(1 for r in results if r['is_toxic'])
            safe_count = len(results) - toxic_count
            
            action_counts = {}
            for result in results:
                action = result['action']
                action_counts[action] = action_counts.get(action, 0) + 1
            
            statistics = {
                'toxic_count': toxic_count,
                'safe_count': safe_count,
                'actions': action_counts
            }
            
            return {
                'total': len(results),
                'results': results,
                'statistics': statistics
            }
        
        except Exception as e:
            logger.error(f"Batch moderation error: {e}", exc_info=True)
            raise


# Global service instance (singleton)
model_service = ModelService()
