"""
Prepare raw train.csv for BERT training
"""

import pandas as pd
from pathlib import Path
from src.preprocessing.preprocess import preprocess_pipeline

print("=" * 70)
print("PREPARING DATA FOR BERT TRAINING")
print("=" * 70)

# Load raw data
print("\n1. Loading raw data from data/train.csv...")
df = pd.read_csv('data/train.csv')
print(f"   ✓ Loaded {len(df):,} comments")

# Check columns
print(f"\n2. Columns: {list(df.columns)}")

# Clean text
print("\n3. Preprocessing text (transformer mode)...")
df['comment_text'] = df['comment_text'].apply(
    lambda x: preprocess_pipeline(x, mode='transformer')
)
print("   ✓ Text cleaned")

# Create processed directory
processed_dir = Path('data/processed')
processed_dir.mkdir(exist_ok=True)

# Save
output_path = processed_dir / 'train_cleaned.csv'
print(f"\n4. Saving to {output_path}...")
df.to_csv(output_path, index=False)
print(f"   ✓ Saved {len(df):,} rows")

print("\n" + "=" * 70)
print("✅ DATA READY FOR TRAINING!")
print("=" * 70)
print("\nNext step:")
print("  python train_bert_10k.py")
print("=" * 70)
