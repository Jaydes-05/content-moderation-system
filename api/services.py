"""
Business logic services for the API.

This module contains the core service classes that handle
model inference and moderation logic.
"""

import logging
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Note: BERT model classes are optional - API runs in demo mode if not available
try:
    from src.inference.bert_predict import BERTToxicityPredictor
    from src.moderation import ContentModerator
    MODELS_AVAILABLE = True
except ImportError:
    logger.warning("Model modules not found - API will run in DEMO MODE")
    BERTToxicityPredictor = None
    ContentModerator = None
    MODELS_AVAILABLE = False


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
        self._demo_mode = False
    
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
            
            # Check if model classes are available
            if not MODELS_AVAILABLE:
                logger.warning("Model modules not available")
                logger.warning("Enabling DEMO MODE with mock predictions")
                self._demo_mode = True
                self._is_loaded = True
                return
            
            # Check if model exists
            if not Path(model_dir).exists():
                logger.warning(f"Model not found at {model_dir}")
                logger.warning("Enabling DEMO MODE with mock predictions")
                self._demo_mode = True
                self._is_loaded = True
                return
            
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
            logger.warning(f"Model files not found: {e}")
            logger.warning("Enabling DEMO MODE with mock predictions")
            self._demo_mode = True
            self._is_loaded = True
        except Exception as e:
            logger.warning(f"Error loading models: {e}")
            logger.warning("Enabling DEMO MODE with mock predictions")
            self._demo_mode = True
            self._is_loaded = True
    
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
        
        # Demo mode: return mock predictions based on simple keyword matching
        if self._demo_mode:
            return self._demo_predict(text)
        
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
    
    def _demo_predict(self, text: str) -> Dict:
        """Generate demo predictions based on simple keyword matching."""
        import re
        
        text_lower = text.lower()
        
        # Simple toxic keyword detection
        toxic_keywords = ['idiot', 'stupid', 'hate', 'kill', 'die', 'fuck', 'shit', 'damn', 'ass', 'bitch']
        insult_keywords = ['idiot', 'stupid', 'dumb', 'moron', 'loser']
        threat_keywords = ['kill', 'die', 'hurt', 'attack']
        obscene_keywords = ['fuck', 'shit', 'damn', 'ass', 'bitch']
        
        # Calculate scores
        toxic_score = 0.1
        insult_score = 0.05
        threat_score = 0.02
        obscene_score = 0.03
        
        for keyword in toxic_keywords:
            if keyword in text_lower:
                toxic_score = min(0.95, toxic_score + 0.3)
        
        for keyword in insult_keywords:
            if keyword in text_lower:
                insult_score = min(0.90, insult_score + 0.4)
        
        for keyword in threat_keywords:
            if keyword in text_lower:
                threat_score = min(0.85, threat_score + 0.5)
        
        for keyword in obscene_keywords:
            if keyword in text_lower:
                obscene_score = min(0.88, obscene_score + 0.4)
        
        predictions = {
            'toxic': round(toxic_score, 2),
            'severe_toxic': round(max(threat_score, obscene_score) * 0.6, 2),
            'obscene': round(obscene_score, 2),
            'threat': round(threat_score, 2),
            'insult': round(insult_score, 2),
            'identity_hate': 0.02
        }
        
        max_score = max(predictions.values())
        is_toxic = max_score > 0.5
        toxic_labels = [k for k, v in predictions.items() if v > 0.5]
        
        return {
            'text': text,
            'is_toxic': is_toxic,
            'predictions': predictions,
            'toxic_labels': toxic_labels,
            'max_score': max_score,
            'confidence': max_score
        }
    
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
            # Get prediction (works in both demo and real mode)
            prediction_dict = self.predict(text)
            
            # Demo mode: simple moderation logic
            if self._demo_mode:
                max_score = prediction_dict['max_score']
                is_toxic = prediction_dict['is_toxic']
                
                if max_score >= 0.8:
                    action = "BLOCK"
                    severity = "HIGH"
                elif max_score >= 0.5:
                    action = "HIDE"
                    severity = "MEDIUM"
                elif max_score >= 0.3:
                    action = "WARNING"
                    severity = "LOW"
                else:
                    action = "ALLOW"
                    severity = "NONE"
                
                primary_label = prediction_dict['toxic_labels'][0] if prediction_dict['toxic_labels'] else 'none'
                
                return {
                    'text': text,
                    'is_toxic': is_toxic,
                    'predictions': prediction_dict['predictions'],
                    'action': action,
                    'severity': severity,
                    'primary_label': primary_label,
                    'confidence': max_score,
                    'explanation': f"Content analyzed in demo mode. Action: {action}"
                }
            
            # Real mode: use actual predictor and moderator
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
