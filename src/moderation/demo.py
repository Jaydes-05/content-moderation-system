"""
Moderation Engine Demo

This script demonstrates the content moderation engine with various test cases.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.moderation import ContentModerator, ModerationRules
from src.moderation.rules import PresetRules
import json


def print_result(result, title=""):
    """Pretty print moderation result."""
    if title:
        print(f"\n{'='*70}")
        print(f"{title}")
        print('='*70)
    
    print(f"\nAction: {result.action}")
    print(f"Severity: {result.severity}")
    print(f"Primary Label: {result.primary_label}")
    print(f"Confidence: {result.confidence:.4f}")
    print(f"\nExplanation:")
    print(f"   {result.explanation}")
    print(f"\nAll Predictions:")
    for label, score in result.all_predictions.items():
        bar = '=' * int(score * 20)
        print(f"   {label:15s}: {score:.4f} {bar}")


def demo_basic_cases():
    """Demonstrate basic moderation cases."""
    print("\n" + "="*70)
    print("DEMO 1: BASIC MODERATION CASES")
    print("="*70)
    
    moderator = ContentModerator()
    
    # Test Case 1: Clean content
    print_result(
        moderator.moderate({
            'toxic': 0.05,
            'severe_toxic': 0.01,
            'obscene': 0.02,
            'threat': 0.01,
            'insult': 0.03,
            'identity_hate': 0.01
        }),
        title="Test 1: Clean Content (No Toxicity)"
    )
    
    # Test Case 2: Mild toxicity
    print_result(
        moderator.moderate({
            'toxic': 0.45,
            'severe_toxic': 0.10,
            'obscene': 0.35,
            'threat': 0.05,
            'insult': 0.40,
            'identity_hate': 0.08
        }),
        title="Test 2: Mild Toxicity (WARNING)"
    )
    
    # Test Case 3: Moderate toxicity
    print_result(
        moderator.moderate({
            'toxic': 0.72,
            'severe_toxic': 0.25,
            'obscene': 0.68,
            'threat': 0.15,
            'insult': 0.70,
            'identity_hate': 0.20
        }),
        title="Test 3: Moderate Toxicity (HIDE)"
    )
    
    # Test Case 4: Severe toxicity
    print_result(
        moderator.moderate({
            'toxic': 0.92,
            'severe_toxic': 0.85,
            'obscene': 0.88,
            'threat': 0.30,
            'insult': 0.90,
            'identity_hate': 0.40
        }),
        title="Test 4: Severe Toxicity (BLOCK)"
    )


def demo_critical_labels():
    """Demonstrate critical label handling."""
    print("\n" + "="*70)
    print("DEMO 2: CRITICAL LABELS (THREATS & HATE SPEECH)")
    print("="*70)
    
    moderator = ContentModerator()
    
    # Test Case 5: Threat
    print_result(
        moderator.moderate({
            'toxic': 0.65,
            'severe_toxic': 0.50,
            'obscene': 0.30,
            'threat': 0.85,  # Critical label
            'insult': 0.55,
            'identity_hate': 0.20
        }),
        title="Test 5: Threat Detected (CRITICAL)"
    )
    
    # Test Case 6: Hate speech
    print_result(
        moderator.moderate({
            'toxic': 0.70,
            'severe_toxic': 0.60,
            'obscene': 0.40,
            'threat': 0.25,
            'insult': 0.65,
            'identity_hate': 0.88  # Critical label
        }),
        title="Test 6: Hate Speech Detected (CRITICAL)"
    )
    
    # Test Case 7: Multiple critical labels
    print_result(
        moderator.moderate({
            'toxic': 0.85,
            'severe_toxic': 0.78,  # Critical label
            'obscene': 0.70,
            'threat': 0.82,  # Critical label
            'insult': 0.75,
            'identity_hate': 0.80  # Critical label
        }),
        title="Test 7: Multiple Critical Labels (EXTREME)"
    )


def demo_multi_label():
    """Demonstrate multi-label handling."""
    print("\n" + "="*70)
    print("DEMO 3: MULTI-LABEL TOXICITY")
    print("="*70)
    
    moderator = ContentModerator()
    
    # Test Case 8: Multiple moderate labels
    print_result(
        moderator.moderate({
            'toxic': 0.55,
            'severe_toxic': 0.20,
            'obscene': 0.60,
            'threat': 0.10,
            'insult': 0.58,
            'identity_hate': 0.15
        }),
        title="Test 8: Multiple Moderate Labels"
    )
    
    # Test Case 9: One dominant label
    print_result(
        moderator.moderate({
            'toxic': 0.30,
            'severe_toxic': 0.10,
            'obscene': 0.25,
            'threat': 0.05,
            'insult': 0.85,  # Dominant
            'identity_hate': 0.08
        }),
        title="Test 9: One Dominant Label (Insult)"
    )


def demo_presets():
    """Demonstrate different preset configurations."""
    print("\n" + "="*70)
    print("DEMO 4: DIFFERENT MODERATION PRESETS")
    print("="*70)
    
    # Same predictions, different presets
    predictions = {
        'toxic': 0.50,
        'severe_toxic': 0.20,
        'obscene': 0.45,
        'threat': 0.15,
        'insult': 0.48,
        'identity_hate': 0.18
    }
    
    presets = ['strict', 'moderate', 'lenient', 'zero_tolerance']
    
    for preset in presets:
        moderator = ContentModerator.from_preset(preset)
        result = moderator.moderate(predictions)
        print(f"\n{'─'*70}")
        print(f"Preset: {preset.upper()}")
        print(f"Action: {result.action} | Severity: {result.severity} | Confidence: {result.confidence:.4f}")
        print(f"Explanation: {result.explanation}")


def demo_batch_processing():
    """Demonstrate batch processing."""
    print("\n" + "="*70)
    print("DEMO 5: BATCH PROCESSING")
    print("="*70)
    
    moderator = ContentModerator()
    
    # Batch of predictions
    predictions_batch = [
        {'toxic': 0.05, 'severe_toxic': 0.01, 'obscene': 0.02, 'threat': 0.01, 'insult': 0.03, 'identity_hate': 0.01},
        {'toxic': 0.45, 'severe_toxic': 0.10, 'obscene': 0.35, 'threat': 0.05, 'insult': 0.40, 'identity_hate': 0.08},
        {'toxic': 0.72, 'severe_toxic': 0.25, 'obscene': 0.68, 'threat': 0.15, 'insult': 0.70, 'identity_hate': 0.20},
        {'toxic': 0.92, 'severe_toxic': 0.85, 'obscene': 0.88, 'threat': 0.30, 'insult': 0.90, 'identity_hate': 0.40},
        {'toxic': 0.65, 'severe_toxic': 0.50, 'obscene': 0.30, 'threat': 0.85, 'insult': 0.55, 'identity_hate': 0.20},
    ]
    
    texts = [
        "This is a great article!",
        "I disagree with your opinion.",
        "You're being ridiculous.",
        "You're a complete idiot!",
        "I will hurt you!"
    ]
    
    results = moderator.moderate_batch(predictions_batch, texts=texts)
    
    print("\nBatch Results:")
    print(f"{'#':<5} {'Text':<35} {'Action':<10} {'Severity':<10} {'Confidence':<12}")
    print("─"*70)
    
    for i, (result, text) in enumerate(zip(results, texts), 1):
        text_short = text[:32] + "..." if len(text) > 32 else text
        print(f"{i:<5} {text_short:<35} {result.action:<10} {result.severity:<10} {result.confidence:<12.4f}")
    
    # Statistics
    stats = moderator.get_statistics(results)
    print("\n" + "─"*70)
    print("BATCH STATISTICS")
    print("─"*70)
    print(json.dumps(stats, indent=2))


def demo_custom_rules():
    """Demonstrate custom rule configuration."""
    print("\n" + "="*70)
    print("DEMO 6: CUSTOM RULES CONFIGURATION")
    print("="*70)
    
    # Create custom rules
    custom_rules = ModerationRules()
    
    # Modify thresholds
    from src.moderation import ModerationAction
    custom_rules.thresholds[ModerationAction.BLOCK] = (0.7, 1.0)  # Lower block threshold
    
    # Modify label weights
    custom_rules.label_weights['obscene'] = 1.2  # Increase obscenity weight
    
    # Change aggregation strategy
    custom_rules.aggregation_strategy = "max"
    
    moderator = ContentModerator(rules=custom_rules)
    
    predictions = {
        'toxic': 0.60,
        'severe_toxic': 0.30,
        'obscene': 0.75,  # Will be weighted higher
        'threat': 0.20,
        'insult': 0.55,
        'identity_hate': 0.25
    }
    
    print("\nCustom Rules Applied:")
    print(f"  - Block threshold lowered to 0.7")
    print(f"  - Obscenity weight increased to 1.2")
    print(f"  - Aggregation strategy: max")
    
    result = moderator.moderate(predictions)
    print_result(result, title="Result with Custom Rules")
    
    # Export configuration
    print("\n" + "─"*70)
    print("Exported Configuration:")
    print(json.dumps(moderator.export_config(), indent=2))


def demo_json_output():
    """Demonstrate JSON output format."""
    print("\n" + "="*70)
    print("DEMO 7: JSON OUTPUT FORMAT (for API integration)")
    print("="*70)
    
    moderator = ContentModerator()
    
    result = moderator.moderate({
        'toxic': 0.85,
        'severe_toxic': 0.60,
        'obscene': 0.75,
        'threat': 0.30,
        'insult': 0.80,
        'identity_hate': 0.40
    })
    
    print("\nJSON Output:")
    print(result.to_json())


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("CONTENT MODERATION ENGINE - COMPREHENSIVE DEMO")
    print("="*70)
    
    demo_basic_cases()
    demo_critical_labels()
    demo_multi_label()
    demo_presets()
    demo_batch_processing()
    demo_custom_rules()
    demo_json_output()
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nThe moderation engine is ready for production use!")
    print("Integration examples:")
    print("  - FastAPI: Use moderator.moderate() in API endpoints")
    print("  - Batch processing: Use moderator.moderate_batch()")
    print("  - Custom rules: Create ModerationRules() and customize")
    print("  - Presets: Use ContentModerator.from_preset('strict')")


if __name__ == '__main__':
    main()
