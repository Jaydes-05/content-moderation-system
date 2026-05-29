"""
API Client Example

Simple examples of how to use the Content Moderation API.

Prerequisites:
    1. Start the API: uvicorn api.main:app --reload
    2. Run this script: python api_client_example.py
"""

import requests
import json


# API base URL
BASE_URL = "http://localhost:8000"


def example_health_check():
    """Example: Health check."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Health Check")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/health")
    data = response.json()
    
    print(f"\nStatus: {data['status']}")
    print(f"Model loaded: {data['model_loaded']}")
    print(f"Version: {data['version']}")


def example_single_prediction():
    """Example: Single text prediction."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Single Text Prediction")
    print("="*70)
    
    text = "You are an idiot!"
    print(f"\nInput: \"{text}\"")
    
    response = requests.post(
        f"{BASE_URL}/predict",
        json={"text": text}
    )
    data = response.json()
    
    print(f"\nIs toxic: {data['is_toxic']}")
    print(f"Confidence: {data['confidence']:.4f}")
    print(f"Toxic labels: {data['toxic_labels']}")
    print(f"\nPredictions:")
    for label, score in data['predictions'].items():
        print(f"  {label:15s}: {score:.4f}")


def example_moderation():
    """Example: Content moderation."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Content Moderation")
    print("="*70)
    
    text = "You are an idiot!"
    print(f"\nInput: \"{text}\"")
    
    response = requests.post(
        f"{BASE_URL}/moderate",
        json={"text": text}
    )
    data = response.json()
    
    print(f"\nAction: {data['action']}")
    print(f"Severity: {data['severity']}")
    print(f"Primary label: {data['primary_label']}")
    print(f"Confidence: {data['confidence']:.4f}")
    print(f"\nExplanation:")
    print(f"  {data['explanation']}")


def example_batch_moderation():
    """Example: Batch moderation."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Batch Moderation")
    print("="*70)
    
    texts = [
        "This is a great article, thanks!",
        "You are stupid!",
        "I disagree with your opinion.",
        "I will hurt you!",
        "Great post!"
    ]
    
    print(f"\nProcessing {len(texts)} texts...")
    
    response = requests.post(
        f"{BASE_URL}/batch-moderate",
        json={"texts": texts}
    )
    data = response.json()
    
    print(f"\nTotal processed: {data['total']}")
    print(f"Toxic: {data['statistics']['toxic_count']}")
    print(f"Safe: {data['statistics']['safe_count']}")
    print(f"\nActions: {data['statistics']['actions']}")
    
    print(f"\nResults:")
    for i, result in enumerate(data['results'], 1):
        text_short = result['text'][:40] + "..." if len(result['text']) > 40 else result['text']
        print(f"  {i}. \"{text_short}\"")
        print(f"     → {result['action']} ({result['severity']})")


def example_clean_content():
    """Example: Clean content."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Clean Content")
    print("="*70)
    
    text = "This is a great article, thanks for sharing!"
    print(f"\nInput: \"{text}\"")
    
    response = requests.post(
        f"{BASE_URL}/moderate",
        json={"text": text}
    )
    data = response.json()
    
    print(f"\nIs toxic: {data['is_toxic']}")
    print(f"Action: {data['action']}")
    print(f"Severity: {data['severity']}")
    print(f"Explanation: {data['explanation']}")


def example_error_handling():
    """Example: Error handling."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Error Handling")
    print("="*70)
    
    # Empty text
    print("\nTrying empty text...")
    response = requests.post(
        f"{BASE_URL}/predict",
        json={"text": ""}
    )
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        error = response.json()
        print(f"Error: {error['error']}")
        print(f"Message: {error['message']}")
    
    # Text too long
    print("\nTrying text too long...")
    response = requests.post(
        f"{BASE_URL}/predict",
        json={"text": "a" * 10001}
    )
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        error = response.json()
        print(f"Error: {error['error']}")
        print(f"Message: {error['message']}")


def example_json_output():
    """Example: JSON output."""
    print("\n" + "="*70)
    print("EXAMPLE 7: JSON Output (for logging/storage)")
    print("="*70)
    
    text = "You are an idiot!"
    
    response = requests.post(
        f"{BASE_URL}/moderate",
        json={"text": text}
    )
    data = response.json()
    
    print("\nJSON output:")
    print(json.dumps(data, indent=2))


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("CONTENT MODERATION API - CLIENT EXAMPLES")
    print("="*70)
    print("\nMake sure the API is running:")
    print("  uvicorn api.main:app --reload")
    
    try:
        # Check if API is running
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("\n[ERROR] API is not healthy")
            return
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Could not connect to API")
        print("\nStart the API first:")
        print("  uvicorn api.main:app --reload")
        return
    
    # Run examples
    example_health_check()
    example_single_prediction()
    example_moderation()
    example_batch_moderation()
    example_clean_content()
    example_error_handling()
    example_json_output()
    
    print("\n" + "="*70)
    print("EXAMPLES COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("  1. Try the interactive docs: http://localhost:8000/docs")
    print("  2. Modify these examples for your use case")
    print("  3. Integrate into your application")


if __name__ == "__main__":
    main()
