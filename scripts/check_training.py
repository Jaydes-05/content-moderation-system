"""
Quick script to check if BERT training is complete
"""

from pathlib import Path
import json

print("=" * 70)
print("CHECKING TRAINING STATUS")
print("=" * 70)

# Check if model exists
model_dir = Path("models/bert/final_model")
if model_dir.exists():
    files = list(model_dir.glob("*"))
    print(f"\n✅ Model directory exists!")
    print(f"   Files: {len(files)}")
    for f in files:
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"   - {f.name} ({size_mb:.1f} MB)")
    print("\n✅ TRAINING COMPLETE!")
    print("\nNext steps:")
    print("1. Restart the backend:")
    print("   python -m uvicorn api.main:app --reload")
    print("2. Test the extension on Reddit/Twitter")
else:
    print("\n⏳ Training still in progress...")
    print("   Model will be saved to: models/bert/final_model/")
    print("\n   Check back in a few minutes!")

# Check if results exist
results_file = Path("results/bert_metrics.json")
if results_file.exists():
    print("\n📊 Training Results:")
    with open(results_file) as f:
        results = json.load(f)
    print(f"   Accuracy: {results['overall']['accuracy']:.4f}")
    print(f"   F1 Score: {results['overall']['f1_micro']:.4f}")

print("\n" + "=" * 70)
