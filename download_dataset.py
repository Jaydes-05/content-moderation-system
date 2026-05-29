"""
Download Jigsaw Toxic Comment dataset from Kaggle

Prerequisites:
1. Install kaggle: pip install kaggle
2. Get Kaggle API credentials:
   - Go to https://www.kaggle.com/settings
   - Click "Create New API Token"
   - Save kaggle.json to: C:\\Users\\AMISHA\\.kaggle\\kaggle.json
"""

import os
import sys
import zipfile
from pathlib import Path

def download_dataset():
    print("=" * 70)
    print("DOWNLOADING JIGSAW TOXIC COMMENT DATASET")
    print("=" * 70)
    
    # Check if kaggle is installed
    try:
        import kaggle
        print("✓ Kaggle package found")
    except ImportError:
        print("✗ Kaggle package not found")
        print("\nInstalling kaggle...")
        os.system("pip install kaggle")
        import kaggle
        print("✓ Kaggle installed")
    
    # Check for API credentials
    kaggle_dir = Path.home() / ".kaggle"
    kaggle_json = kaggle_dir / "kaggle.json"
    
    if not kaggle_json.exists():
        print("\n" + "=" * 70)
        print("⚠️  KAGGLE API CREDENTIALS NOT FOUND")
        print("=" * 70)
        print("\nTo download the dataset, you need Kaggle API credentials:")
        print("\n1. Go to: https://www.kaggle.com/settings")
        print("2. Scroll to 'API' section")
        print("3. Click 'Create New API Token'")
        print("4. Save the downloaded kaggle.json to:")
        print(f"   {kaggle_json}")
        print("\n5. Then run this script again")
        print("=" * 70)
        sys.exit(1)
    
    print(f"✓ Kaggle credentials found at {kaggle_json}")
    
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Download dataset
    print("\nDownloading dataset from Kaggle...")
    print("Competition: jigsaw-toxic-comment-classification-challenge")
    print("This may take a few minutes...\n")
    
    try:
        # Download using kaggle API
        os.system('kaggle competitions download -c jigsaw-toxic-comment-classification-challenge -p data')
        
        # Check if zip file was downloaded
        zip_file = data_dir / "jigsaw-toxic-comment-classification-challenge.zip"
        
        if not zip_file.exists():
            print("\n✗ Download failed. Make sure you've accepted the competition rules:")
            print("   https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge/rules")
            sys.exit(1)
        
        print(f"\n✓ Downloaded: {zip_file}")
        
        # Extract zip file
        print("\nExtracting files...")
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(data_dir)
        
        print("✓ Extracted successfully")
        
        # Check for train.csv
        train_csv = data_dir / "train.csv"
        if train_csv.exists():
            file_size = train_csv.stat().st_size / (1024 * 1024)  # MB
            print(f"\n✓ train.csv found ({file_size:.1f} MB)")
            
            # Count lines
            with open(train_csv, 'r', encoding='utf-8') as f:
                line_count = sum(1 for _ in f) - 1  # Subtract header
            print(f"✓ Dataset contains {line_count:,} comments")
        else:
            print("\n✗ train.csv not found in extracted files")
            sys.exit(1)
        
        # Clean up zip file
        zip_file.unlink()
        print("\n✓ Cleaned up zip file")
        
        print("\n" + "=" * 70)
        print("✅ DATASET READY!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Train the model:")
        print("   python train_bert_10k.py")
        print("\n2. This will take 30-45 minutes on CPU")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you've accepted the competition rules")
        print("2. Check your Kaggle API credentials")
        print("3. Try downloading manually from:")
        print("   https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge/data")
        sys.exit(1)

if __name__ == '__main__':
    download_dataset()
