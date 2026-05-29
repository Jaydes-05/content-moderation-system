"""
API Test Script

Quick test to verify the FastAPI backend works correctly.
Run this after starting the API server.

Usage:
    # Terminal 1: Start API
    uvicorn api.main:app --reload
    
    # Terminal 2: Run tests
    python test_api.py
"""

import requests
import time
import sys


def test_api(base_url="http://localhost:8000"):
    """Test all API endpoints."""
    print("="*70)
    print("API TEST SUITE")
    print("="*70)
    print(f"\nTesting API at: {base_url}")
    
    # Wait for API to be ready
    print("\nWaiting for API to be ready...")
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                print("+ API is ready")
                break
        except requests.exceptions.ConnectionError:
            if i < max_retries - 1:
                print(f"  Waiting... ({i+1}/{max_retries})")
                time.sleep(2)
            else:
                print("\n[FAIL] Could not connect to API")
                print("\nMake sure the API is running:")
                print("  uvicorn api.main:app --reload")
                sys.exit(1)
    
    # Test 1: Root endpoint
    print("\n" + "-"*70)
    print("Test 1: Root Endpoint")
    print("-"*70)
    try:
        response = requests.get(f"{base_url}/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        print(f"+ Status: {response.status_code}")
        print(f"+ Name: {data['name']}")
        print(f"+ Version: {data['version']}")
        print("[PASS] Root endpoint works")
    except Exception as e:
        print(f"[FAIL] {e}")
        return False
    
    # Test 2: Health check
    print("\n" + "-"*70)
    print("Test 2: Health Check")
    print("-"*70)
    try:
        response = requests.get(f"{base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] == True
        print(f"+ Status: {data['status']}")
        print(f"+ Model loaded: {data['model_loaded']}")
        print(f"+ Moderator loaded: {data['moderator_loaded']}")
        print("[PASS] Health check works")
    except Exception as e:
        print(f"[FAIL] {e}")
        return False
    
    # Test 3: Prediction endpoint
    print("\n" + "-"*70)
    print("Test 3: Prediction Endpoint")
    print("-"*70)
    try:
        response = requests.post(
            f"{base_url}/predict",
            json={"text": "You are an idiot!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "is_toxic" in data
        assert "predictions" in data
        assert data["is_toxic"] == True
        print(f"+ Text: {data['text']}")
        print(f"+ Is toxic: {data['is_toxic']}")
        print(f"+ Max score: {data['max_score']:.4f}")
        print(f"+ Toxic labels: {data['toxic_labels']}")
        print("[PASS] Prediction endpoint works")
    except Exception as e:
        print(f"[FAIL] {e}")
        return False
    
    # Test 4: Moderation endpoint
    print("\n" + "-"*70)
    print("Test 4: Moderation Endpoint")
    print("-"*70)
    try:
        response = requests.post(
            f"{base_url}/moderate",
            json={"text": "You are an idiot!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "action" in data
        assert "severity" in data
        assert data["is_toxic"] == True
        print(f"+ Text: {data['text']}")
        print(f"+ Action: {data['action']}")
        print(f"+ Severity: {data['severity']}")
        print(f"+ Primary label: {data['primary_label']}")
        print(f"+ Confidence: {data['confidence']:.4f}")
        print(f"+ Explanation: {data['explanation'][:60]}...")
        print("[PASS] Moderation endpoint works")
    except Exception as e:
        print(f"[FAIL] {e}")
        return False
    
    # Test 5: Batch moderation endpoint
    print("\n" + "-"*70)
    print("Test 5: Batch Moderation Endpoint")
    print("-"*70)
    try:
        response = requests.post(
            f"{base_url}/batch-moderate",
            json={
                "texts": [
                    "Great post!",
                    "You are stupid!",
                    "I disagree with your opinion."
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["results"]) == 3
        assert "statistics" in data
        print(f"+ Total processed: {data['total']}")
        print(f"+ Toxic count: {data['statistics']['toxic_count']}")
        print(f"+ Safe count: {data['statistics']['safe_count']}")
        print(f"+ Actions: {data['statistics']['actions']}")
        print("[PASS] Batch moderation endpoint works")
    except Exception as e:
        print(f"[FAIL] {e}")
        return False
    
    # Test 6: Validation (empty text)
    print("\n" + "-"*70)
    print("Test 6: Validation (Empty Text)")
    print("-"*70)
    try:
        response = requests.post(
            f"{base_url}/predict",
            json={"text": ""}
        )
        assert response.status_code == 422
        print(f"+ Status: {response.status_code}")
        print("[PASS] Validation works (empty text rejected)")
    except Exception as e:
        print(f"[FAIL] {e}")
        return False
    
    # Test 7: Validation (text too long)
    print("\n" + "-"*70)
    print("Test 7: Validation (Text Too Long)")
    print("-"*70)
    try:
        response = requests.post(
            f"{base_url}/predict",
            json={"text": "a" * 10001}
        )
        assert response.status_code == 422
        print(f"+ Status: {response.status_code}")
        print("[PASS] Validation works (long text rejected)")
    except Exception as e:
        print(f"[FAIL] {e}")
        return False
    
    # Test 8: Clean content
    print("\n" + "-"*70)
    print("Test 8: Clean Content")
    print("-"*70)
    try:
        response = requests.post(
            f"{base_url}/moderate",
            json={"text": "This is a great article, thanks for sharing!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_toxic"] == False
        assert data["action"] == "ALLOW"
        print(f"+ Text: {data['text'][:50]}...")
        print(f"+ Is toxic: {data['is_toxic']}")
        print(f"+ Action: {data['action']}")
        print("[PASS] Clean content handled correctly")
    except Exception as e:
        print(f"[FAIL] {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    try:
        success = test_api()
        
        print("\n" + "="*70)
        if success:
            print("[SUCCESS] ALL API TESTS PASSED")
            print("="*70)
            print("\nThe API is working correctly!")
            print("\nNext steps:")
            print("  1. Check interactive docs: http://localhost:8000/docs")
            print("  2. Try the API with your own data")
            print("  3. Integrate with frontend (Streamlit)")
            print("  4. Deploy to production")
        else:
            print("[FAIL] SOME TESTS FAILED")
            print("="*70)
        
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
