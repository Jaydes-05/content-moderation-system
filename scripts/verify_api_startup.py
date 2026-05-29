"""
Verify API Startup

Quick script to verify the API can start without errors.
This tests model loading without starting the full server.
"""

import sys
import os
from pathlib import Path


def verify_model_exists():
    """Check if model files exist."""
    print("Checking model files...")
    
    model_dir = Path("models/bert/final_model")
    tokenizer_dir = Path("models/bert/tokenizer")
    
    if not model_dir.exists():
        print(f"[FAIL] Model directory not found: {model_dir}")
        print("\nTrain the model first:")
        print("  python train_bert_10k.py")
        return False
    
    if not tokenizer_dir.exists():
        print(f"[FAIL] Tokenizer directory not found: {tokenizer_dir}")
        return False
    
    print(f"+ Model directory exists: {model_dir}")
    print(f"+ Tokenizer directory exists: {tokenizer_dir}")
    return True


def verify_imports():
    """Check if all required modules can be imported."""
    print("\nChecking imports...")
    
    try:
        from api.services import ModelService
        print("+ api.services imported")
        
        from api.schemas import HealthResponse
        print("+ api.schemas imported")
        
        from src.inference.bert_predict import BERTToxicityPredictor
        print("+ BERTToxicityPredictor imported")
        
        from src.moderation import ContentModerator
        print("+ ContentModerator imported")
        
        return True
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False


def verify_model_loading():
    """Test model loading."""
    print("\nTesting model loading...")
    
    try:
        from api.services import ModelService
        
        service = ModelService()
        print("+ ModelService created")
        
        # Try to load models
        service.load_models()
        print("+ Models loaded successfully")
        
        # Check if loaded
        if service.is_loaded():
            print("+ Service reports models are loaded")
        else:
            print("[FAIL] Service reports models are NOT loaded")
            return False
        
        return True
    
    except TypeError as e:
        print(f"[FAIL] TypeError during model loading: {e}")
        print("\nThis usually means constructor arguments are wrong.")
        return False
    except Exception as e:
        print(f"[FAIL] Error during model loading: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_prediction():
    """Test a simple prediction."""
    print("\nTesting prediction...")
    
    try:
        from api.services import ModelService
        
        service = ModelService()
        service.load_models()
        
        # Test prediction
        result = service.predict("You are an idiot!")
        print(f"+ Prediction successful")
        print(f"  - Is toxic: {result['is_toxic']}")
        print(f"  - Confidence: {result['confidence']:.4f}")
        
        # Test moderation
        result = service.moderate("You are an idiot!")
        print(f"+ Moderation successful")
        print(f"  - Action: {result['action']}")
        print(f"  - Severity: {result['severity']}")
        
        return True
    
    except Exception as e:
        print(f"[FAIL] Error during prediction: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_pydantic_schemas():
    """Test Pydantic schemas."""
    print("\nTesting Pydantic schemas...")
    
    try:
        from api.schemas import HealthResponse, PredictionResponse, ModerationResponse
        
        # Test HealthResponse (should not have protected namespace warning)
        health = HealthResponse(
            status="healthy",
            model_loaded=True,
            moderator_loaded=True,
            version="1.0.0"
        )
        print("+ HealthResponse created without warnings")
        
        return True
    
    except Exception as e:
        print(f"[FAIL] Error with Pydantic schemas: {e}")
        return False


def main():
    """Run all verification checks."""
    print("="*70)
    print("API STARTUP VERIFICATION")
    print("="*70)
    
    checks = [
        ("Model files exist", verify_model_exists),
        ("Imports work", verify_imports),
        ("Model loading works", verify_model_loading),
        ("Prediction works", verify_prediction),
        ("Pydantic schemas work", verify_pydantic_schemas)
    ]
    
    results = []
    for name, check_func in checks:
        print("\n" + "-"*70)
        print(f"CHECK: {name}")
        print("-"*70)
        try:
            success = check_func()
            results.append((name, success))
        except Exception as e:
            print(f"[FAIL] Unexpected error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    
    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {name}")
    
    all_passed = all(success for _, success in results)
    
    print("\n" + "="*70)
    if all_passed:
        print("[SUCCESS] ALL CHECKS PASSED")
        print("="*70)
        print("\nThe API is ready to start!")
        print("\nRun the API:")
        print("  uvicorn api.main:app --reload")
        print("\nThen test it:")
        print("  python test_api.py")
    else:
        print("[FAIL] SOME CHECKS FAILED")
        print("="*70)
        print("\nFix the issues above before starting the API.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
