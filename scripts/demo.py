"""
Simple demo script to test the toxicity detection model.

Just run: python demo.py
"""

import sys
sys.path.insert(0, 'src')

from inference.predict import ToxicityPredictor

def print_header(text):
    """Print a nice header."""
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)

def print_result(text, result):
    """Print prediction result in a nice format."""
    print(f"\n📝 Text: {text}")
    print("-" * 70)
    
    if result.is_toxic:
        print(f"🔴 TOXIC (confidence: {result.max_toxicity_score:.2%})")
        print(f"   Labels detected: {', '.join(result.toxic_labels)}")
        print("\n   Probabilities:")
        for pred in result.predictions:
            if pred.predicted:
                print(f"      • {pred.label:15s}: {pred.probability:.2%}")
    else:
        print(f"🟢 CLEAN (max score: {result.max_toxicity_score:.2%})")
    
    print("-" * 70)

def main():
    print_header("🛡️  TOXICITY DETECTION DEMO")
    
    print("\nInitializing model...")
    predictor = ToxicityPredictor()
    print("✓ Model loaded successfully!\n")
    
    # Test cases
    test_cases = [
        ("Toxic Example 1", "You are an idiot and should be ashamed!"),
        ("Toxic Example 2", "Go kill yourself, nobody likes you."),
        ("Toxic Example 3", "What a stupid waste of time."),
        ("Clean Example 1", "This is a great article, thanks for sharing!"),
        ("Clean Example 2", "I disagree with your opinion, but I respect it."),
        ("Clean Example 3", "Can you please explain this in more detail?"),
        ("Edge Case", "This is stupid."),
    ]
    
    print_header("RUNNING TEST CASES")
    
    for i, (label, text) in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {label}")
        result = predictor.predict(text)
        print_result(text, result)
    
    print_header("SUMMARY")
    
    results = [predictor.predict(text) for _, text in test_cases]
    toxic_count = sum(1 for r in results if r.is_toxic)
    clean_count = len(results) - toxic_count
    
    print(f"\n✓ Tested {len(test_cases)} examples")
    print(f"  • Toxic:  {toxic_count} ({toxic_count/len(results)*100:.0f}%)")
    print(f"  • Clean:  {clean_count} ({clean_count/len(results)*100:.0f}%)")
    
    print_header("TRY YOUR OWN TEXT")
    print("\nYou can now test your own text!")
    print("Type 'quit' to exit\n")
    
    while True:
        try:
            user_input = input("Enter text to analyze: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                print("⚠️  Please enter some text\n")
                continue
            
            result = predictor.predict(user_input)
            print_result(user_input, result)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == '__main__':
    main()
