"""
Quick integration test to verify BERT + Moderation pipeline works.

This tests that the prediction result from BERT can be properly
passed to the moderation engine.
"""

import sys
import os

# Check if model exists
model_path = "models/bert/final_model"
if not os.path.exists(model_path):
    print("="*70)
    print("BERT MODEL NOT FOUND")
    print("="*70)
    print(f"\nModel not found at: {model_path}")
    print("\nTrain the model first:")
    print("  python train_bert_10k.py")
    print("\nSkipping integration test.")
    print("="*70)
    sys.exit(0)

from src.inference.bert_predict import BERTToxicityPredictor
from src.moderation import ContentModerator


def test_integration():
    """Test BERT + Moderation integration."""
    print("="*70)
    print("INTEGRATION TEST: BERT + MODERATION")
    print("="*70)
    
    # Initialize
    print("\nInitializing...")
    predictor = BERTToxicityPredictor()
    moderator = ContentModerator()
    print("- Predictor ready")
    print("- Moderator ready")
    
    # Test text
    text = "You are an idiot!"
    print(f"\nTest text: \"{text}\"")
    
    # Step 1: BERT prediction
    print("\nStep 1: BERT prediction...")
    prediction = predictor.predict(text)
    print(f"- Type: {type(prediction).__name__}")
    print(f"- Has predictions attr: {hasattr(prediction, 'predictions')}")
    print(f"- Is toxic: {prediction.is_toxic}")
    print(f"- Max score: {prediction.max_score:.4f}")
    
    # Step 2: Access predictions
    print("\nStep 2: Accessing predictions...")
    try:
        probs = prediction.predictions
        print(f"- Successfully accessed predictions")
        print(f"- Type: {type(probs).__name__}")
        print(f"- Keys: {list(probs.keys())}")
    except Exception as e:
        print(f"- ERROR: {e}")
        return False
    
    # Step 3: Moderation
    print("\nStep 3: Moderation...")
    try:
        result = moderator.moderate(prediction.predictions)
        print(f"- Action: {result.action}")
        print(f"- Severity: {result.severity}")
        print(f"- Confidence: {result.confidence:.4f}")
    except Exception as e:
        print(f"- ERROR: {e}")
        return False
    
    print("\n" + "="*70)
    print("INTEGRATION TEST PASSED")
    print("="*70)
    print("\nThe pipeline works correctly!")
    print("You can now run: python demo_full_pipeline.py")
    
    return True


if __name__ == '__main__':
    try:
        success = test_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
