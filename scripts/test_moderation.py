"""
Quick test script for the moderation engine.

Run this to verify the moderation engine works correctly.
"""

from src.moderation import ContentModerator, ModerationAction, SeverityLevel
import json


def test_basic_functionality():
    """Test basic moderation functionality."""
    print("Testing basic functionality...")
    
    moderator = ContentModerator()
    
    # Test 1: Clean content
    result = moderator.moderate({
        'toxic': 0.05,
        'severe_toxic': 0.01,
        'obscene': 0.02,
        'threat': 0.01,
        'insult': 0.03,
        'identity_hate': 0.01
    })
    assert result.action == ModerationAction.ALLOW.value
    assert result.is_safe()
    print("+ Test 1 passed: Clean content -> ALLOW")
    
    # Test 2: Severe toxicity
    result = moderator.moderate({
        'toxic': 0.92,
        'severe_toxic': 0.85,
        'obscene': 0.88,
        'threat': 0.30,
        'insult': 0.90,
        'identity_hate': 0.40
    })
    assert result.action == ModerationAction.BLOCK.value
    assert result.requires_action()
    print("+ Test 2 passed: Severe toxicity -> BLOCK")
    
    # Test 3: Critical label (threat)
    result = moderator.moderate({
        'toxic': 0.65,
        'severe_toxic': 0.50,
        'obscene': 0.30,
        'threat': 0.85,
        'insult': 0.55,
        'identity_hate': 0.20
    })
    assert result.severity == SeverityLevel.CRITICAL.value
    assert result.is_critical()
    print("+ Test 3 passed: Threat detected -> CRITICAL")
    
    print("\n[PASS] All basic tests passed!")


def test_presets():
    """Test preset configurations."""
    print("\nTesting presets...")
    
    predictions = {
        'toxic': 0.50,
        'severe_toxic': 0.20,
        'obscene': 0.45,
        'threat': 0.15,
        'insult': 0.48,
        'identity_hate': 0.18
    }
    
    # Test all presets
    presets = ['strict', 'moderate', 'lenient', 'zero_tolerance']
    for preset in presets:
        moderator = ContentModerator.from_preset(preset)
        result = moderator.moderate(predictions)
        assert result.action in [a.value for a in ModerationAction]
        print(f"+ Preset '{preset}' works: {result.action}")
    
    print("\n[PASS] All preset tests passed!")


def test_batch_processing():
    """Test batch processing."""
    print("\nTesting batch processing...")
    
    moderator = ContentModerator()
    
    predictions_batch = [
        {'toxic': 0.05, 'severe_toxic': 0.01, 'obscene': 0.02, 'threat': 0.01, 'insult': 0.03, 'identity_hate': 0.01},
        {'toxic': 0.92, 'severe_toxic': 0.85, 'obscene': 0.88, 'threat': 0.30, 'insult': 0.90, 'identity_hate': 0.40},
    ]
    
    results = moderator.moderate_batch(predictions_batch)
    assert len(results) == 2
    assert results[0].action == ModerationAction.ALLOW.value
    assert results[1].action == ModerationAction.BLOCK.value
    
    print("+ Batch processing works")
    
    # Test statistics
    stats = moderator.get_statistics(results)
    assert stats['total_moderated'] == 2
    assert 'actions' in stats
    assert 'severities' in stats
    
    print("+ Statistics calculation works")
    print("\n[PASS] All batch tests passed!")


def test_json_output():
    """Test JSON serialization."""
    print("\nTesting JSON output...")
    
    moderator = ContentModerator()
    
    result = moderator.moderate({
        'toxic': 0.85,
        'severe_toxic': 0.60,
        'obscene': 0.75,
        'threat': 0.30,
        'insult': 0.80,
        'identity_hate': 0.40
    })
    
    # Test to_dict
    result_dict = result.to_dict()
    assert isinstance(result_dict, dict)
    assert 'action' in result_dict
    assert 'severity' in result_dict
    print("+ to_dict() works")
    
    # Test to_json
    result_json = result.to_json()
    assert isinstance(result_json, str)
    parsed = json.loads(result_json)
    assert parsed['action'] == result.action
    print("+ to_json() works")
    
    print("\n[PASS] All JSON tests passed!")


def test_custom_rules():
    """Test custom rules configuration."""
    print("\nTesting custom rules...")
    
    from src.moderation import ModerationRules
    
    # Create custom rules
    rules = ModerationRules()
    rules.thresholds[ModerationAction.BLOCK] = (0.7, 1.0)
    rules.label_weights['obscene'] = 1.5
    
    moderator = ContentModerator(rules=rules)
    
    # Test with custom rules
    result = moderator.moderate({
        'toxic': 0.60,
        'severe_toxic': 0.30,
        'obscene': 0.75,
        'threat': 0.20,
        'insult': 0.55,
        'identity_hate': 0.25
    })
    
    assert result.action in [a.value for a in ModerationAction]
    print("+ Custom rules work")
    
    # Test export/import
    config = moderator.export_config()
    assert isinstance(config, dict)
    print("+ Config export works")
    
    rules_imported = ModerationRules.from_dict(config)
    assert rules_imported.min_confidence == rules.min_confidence
    print("+ Config import works")
    
    print("\n[PASS] All custom rules tests passed!")


def main():
    """Run all tests."""
    print("="*70)
    print("MODERATION ENGINE - QUICK TEST")
    print("="*70)
    
    try:
        test_basic_functionality()
        test_presets()
        test_batch_processing()
        test_json_output()
        test_custom_rules()
        
        print("\n" + "="*70)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("="*70)
        print("\nThe moderation engine is working correctly!")
        print("\nNext steps:")
        print("  1. Run the demo: python src/moderation/demo.py")
        print("  2. Integrate with your toxicity model")
        print("  3. Test with real data")
        print("  4. Deploy to production")
        
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {str(e)}")
        raise
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        raise


if __name__ == '__main__':
    main()
