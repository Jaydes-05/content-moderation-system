"""
Full Pipeline Demo: BERT Model + Moderation Engine

This script demonstrates the complete content moderation pipeline:
1. Text input
2. BERT toxicity prediction
3. Moderation decision
4. Actionable output

NOTE: This requires a trained BERT model in models/bert/final_model/
      Run train_bert_10k.py or train_bert.py first to train the model.
"""

import sys
import os

# Check if model exists
model_path = "models/bert/final_model"
if not os.path.exists(model_path):
    print("="*70)
    print("⚠️  BERT MODEL NOT FOUND")
    print("="*70)
    print(f"\nThe trained BERT model is required but not found at: {model_path}")
    print("\nPlease train the model first:")
    print("  Option 1 (Quick - 30-45 min): python train_bert_10k.py")
    print("  Option 2 (Full - 3-4 hours):  python src/training/train_bert.py")
    print("\nAfter training, run this script again.")
    print("="*70)
    sys.exit(1)

from src.inference.bert_predict import BERTToxicityPredictor
from src.moderation import ContentModerator
import json


def print_separator(title=""):
    """Print a nice separator."""
    print("\n" + "="*70)
    if title:
        print(f"{title}")
        print("="*70)


def print_prediction(prediction):
    """Pretty print model prediction."""
    print("\nModel Predictions:")
    for label, prob in prediction.predictions.items():
        bar = '=' * int(prob * 30)
        print(f"  {label:15s}: {prob:.4f} {bar}")


def print_moderation(result):
    """Pretty print moderation result."""
    print("\nModeration Decision:")
    print(f"  Action:     {result.action}")
    print(f"  Severity:   {result.severity}")
    print(f"  Primary:    {result.primary_label}")
    print(f"  Confidence: {result.confidence:.4f}")
    print(f"\nExplanation:")
    print(f"  {result.explanation}")


def demo_single_text():
    """Demo with a single text."""
    print_separator("DEMO 1: SINGLE TEXT MODERATION")
    
    # Initialize
    print("\nInitializing pipeline...")
    predictor = BERTToxicityPredictor()
    moderator = ContentModerator.from_preset('moderate')
    print("✓ Pipeline ready")
    
    # Test text
    text = "You are a complete idiot and should be ashamed of yourself!"
    
    print(f"\nInput Text:")
    print(f"  \"{text}\"")
    
    # Step 1: Get model prediction
    print("\nStep 1: Running BERT model...")
    prediction = predictor.predict(text)
    print_prediction(prediction)
    
    # Step 2: Get moderation decision
    print("\nStep 2: Applying moderation rules...")
    result = moderator.moderate(
        predictions=prediction.predictions,
        text=text
    )
    print_moderation(result)
    
    # Step 3: Show what action to take
    print("\nRecommended Action:")
    if result.action == "ALLOW":
        print("  - Allow the comment to be posted")
    elif result.action == "WARNING":
        print("  - Show warning to user or flag for review")
    elif result.action == "HIDE":
        print("  - Hide comment from public view")
    elif result.action == "BLOCK":
        print("  - Block and remove the comment")


def demo_multiple_texts():
    """Demo with multiple texts."""
    print_separator("DEMO 2: BATCH MODERATION")
    
    # Initialize
    print("\nInitializing pipeline...")
    predictor = BERTToxicityPredictor()
    moderator = ContentModerator.from_preset('moderate')
    print("✓ Pipeline ready")
    
    # Test texts
    texts = [
        "This is a great article, thanks for sharing!",
        "I disagree with your opinion, but I respect it.",
        "You're being ridiculous and stupid.",
        "You're a complete idiot!",
        "I will hurt you if you don't stop!"
    ]
    
    print(f"\nProcessing {len(texts)} comments...")
    
    # Process batch
    results = []
    for i, text in enumerate(texts, 1):
        # Predict
        prediction = predictor.predict(text)
        
        # Moderate
        result = moderator.moderate(
            predictions=prediction.predictions,
            text=text
        )
        
        results.append((text, result))
        
        # Print result
        print(f"\n{i}. \"{text[:50]}{'...' if len(text) > 50 else ''}\"")
        print(f"   → {result.action} ({result.severity}) - {result.primary_label}")
    
    # Statistics
    print("\n" + "─"*70)
    print("BATCH STATISTICS")
    print("─"*70)
    
    stats = moderator.get_statistics([r for _, r in results])
    print(f"\nTotal processed: {stats['total_moderated']}")
    print(f"\nActions taken:")
    for action, data in stats['actions'].items():
        print(f"  {action:10s}: {data['count']:2d} ({data['percentage']:5.1f}%)")
    
    print(f"\nRequires action: {stats['requires_action_count']}")
    print(f"Critical cases:  {stats['critical_count']}")


def demo_different_presets():
    """Demo with different moderation presets."""
    print_separator("DEMO 3: DIFFERENT MODERATION PRESETS")
    
    # Initialize predictor
    print("\nInitializing BERT model...")
    predictor = BERTToxicityPredictor()
    print("✓ Model ready")
    
    # Test text
    text = "You're being stupid and ridiculous."
    
    print(f"\nInput Text:")
    print(f"  \"{text}\"")
    
    # Get prediction once
    print("\nGetting model prediction...")
    prediction = predictor.predict(text)
    print_prediction(prediction)
    
    # Try different presets
    presets = ['strict', 'moderate', 'lenient', 'zero_tolerance']
    
    print("\nApplying different moderation presets...")
    print("\n" + "-"*70)
    
    for preset in presets:
        moderator = ContentModerator.from_preset(preset)
        result = moderator.moderate(prediction.predictions)
        
        print(f"\n{preset.upper():15s}: {result.action:10s} (Severity: {result.severity})")
        print(f"                 {result.explanation}")


def demo_json_api_format():
    """Demo JSON output for API integration."""
    print_separator("DEMO 4: JSON OUTPUT (API Format)")
    
    # Initialize
    print("\nInitializing pipeline...")
    predictor = BERTToxicityPredictor()
    moderator = ContentModerator.from_preset('moderate')
    print("✓ Pipeline ready")
    
    # Test text
    text = "You are an idiot!"
    
    print(f"\nInput Text:")
    print(f"  \"{text}\"")
    
    # Process
    print("\nProcessing...")
    prediction = predictor.predict(text)
    result = moderator.moderate(
        predictions=prediction.predictions,
        text=text
    )
    
    # Create API response
    api_response = {
        'text': text,
        'model_prediction': prediction.to_dict(),
        'moderation': result.to_dict(),
        'timestamp': '2026-05-08T17:00:00Z',
        'version': '1.0'
    }
    
    print("\nAPI Response (JSON):")
    print(json.dumps(api_response, indent=2))


def demo_real_world_scenario():
    """Demo a real-world moderation scenario."""
    print_separator("DEMO 5: REAL-WORLD SCENARIO")
    
    print("\nScenario: Social media comment moderation")
    print("Platform: General social media (moderate rules)")
    
    # Initialize
    print("\nInitializing pipeline...")
    predictor = BERTToxicityPredictor()
    moderator = ContentModerator.from_preset('moderate')
    print("✓ Pipeline ready")
    
    # Simulate incoming comments
    comments = [
        {
            'id': 'comment_001',
            'user_id': 'user_123',
            'text': 'Great post! Very informative.',
            'timestamp': '2026-05-08 10:00:00'
        },
        {
            'id': 'comment_002',
            'user_id': 'user_456',
            'text': 'This is complete garbage and you should delete your account.',
            'timestamp': '2026-05-08 10:05:00'
        },
        {
            'id': 'comment_003',
            'user_id': 'user_789',
            'text': 'I will find you and hurt you!',
            'timestamp': '2026-05-08 10:10:00'
        }
    ]
    
    print(f"\nProcessing {len(comments)} incoming comments...")
    
    for comment in comments:
        print("\n" + "-"*70)
        print(f"Comment ID: {comment['id']}")
        print(f"User ID:    {comment['user_id']}")
        print(f"Text:       \"{comment['text']}\"")
        print(f"Time:       {comment['timestamp']}")
        
        # Process
        prediction = predictor.predict(comment['text'])
        result = moderator.moderate(
            predictions=prediction.predictions,
            text=comment['text'],
            user_id=comment['user_id']
        )
        
        # Decision
        print(f"\nDecision: {result.action}")
        print(f"   Severity: {result.severity}")
        print(f"   Reason:   {result.explanation}")
        
        # Action taken
        print(f"\nSystem Action:")
        if result.action == "ALLOW":
            print("   - Comment published")
        elif result.action == "WARNING":
            print("   - Comment flagged for manual review")
            print("   - Notification sent to moderators")
        elif result.action == "HIDE":
            print("   - Comment hidden from public")
            print("   - Visible only to author")
            print("   - Warning sent to user")
        elif result.action == "BLOCK":
            print("   - Comment blocked and removed")
            print("   - User account flagged")
            print("   - Notification sent to user")
            if result.is_critical():
                print("   - CRITICAL: Escalated to security team")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("FULL PIPELINE DEMO: BERT + MODERATION ENGINE")
    print("="*70)
    print("\nThis demo shows the complete content moderation pipeline:")
    print("  1. BERT model predicts toxicity probabilities")
    print("  2. Moderation engine converts predictions to actions")
    print("  3. System takes appropriate action")
    
    try:
        demo_single_text()
        demo_multiple_texts()
        demo_different_presets()
        demo_json_api_format()
        demo_real_world_scenario()
        
        print("\n" + "="*70)
        print("DEMO COMPLETE")
        print("="*70)
        print("\nThe full pipeline is working correctly!")
        print("\nNext steps:")
        print("  1. Integrate into your application")
        print("  2. Build FastAPI endpoints")
        print("  3. Add database logging")
        print("  4. Deploy to production")
        print("\nFor more examples:")
        print("  - Moderation only: python src/moderation/demo.py")
        print("  - BERT inference: python src/inference/bert_predict.py --examples")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
