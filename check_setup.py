"""
Setup verification script - checks if the project is ready to run.
"""

import os
import sys
from pathlib import Path

def check_item(name, condition, fix_hint=""):
    """Check a condition and print result."""
    if condition:
        print(f"✅ {name}")
        return True
    else:
        print(f"❌ {name}")
        if fix_hint:
            print(f"   Fix: {fix_hint}")
        return False

def main():
    print("\n" + "="*60)
    print("  Content Moderation System - Setup Verification")
    print("="*60 + "\n")
    
    all_good = True
    
    # Check Python version
    print("📋 Python Environment")
    print("-" * 60)
    py_version = sys.version_info
    all_good &= check_item(
        f"Python {py_version.major}.{py_version.minor}.{py_version.micro}",
        py_version >= (3, 8),
        "Install Python 3.8 or higher"
    )
    
    # Check virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    all_good &= check_item(
        "Virtual environment active",
        in_venv,
        "Activate venv: source venv/bin/activate (or venv\\Scripts\\activate on Windows)"
    )
    
    # Check dependencies
    print("\n📦 Dependencies")
    print("-" * 60)
    
    required_packages = [
        ('torch', 'PyTorch'),
        ('transformers', 'Transformers'),
        ('fastapi', 'FastAPI'),
        ('streamlit', 'Streamlit'),
        ('pandas', 'Pandas'),
        ('sklearn', 'scikit-learn')
    ]
    
    for package, name in required_packages:
        try:
            __import__(package)
            check_item(f"{name} installed", True)
        except ImportError:
            all_good &= check_item(
                f"{name} installed",
                False,
                "Run: pip install -r requirements.txt"
            )
    
    # Check dataset
    print("\n📊 Dataset")
    print("-" * 60)
    dataset_path = Path("data/raw/train.csv")
    all_good &= check_item(
        "Dataset (train.csv) present",
        dataset_path.exists(),
        "Download from: https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge/data"
    )
    
    # Check models
    print("\n🤖 Models")
    print("-" * 60)
    
    bert_model = Path("models/bert/final_model")
    bert_exists = bert_model.exists() and any(bert_model.iterdir())
    check_item(
        "BERT model trained",
        bert_exists,
        "Train model: python train_bert_10k.py"
    )
    
    baseline_model = Path("models/baseline/logistic_model.pkl")
    baseline_exists = baseline_model.exists()
    check_item(
        "Baseline model trained",
        baseline_exists,
        "Train model: python src/training/baseline_model.py"
    )
    
    if not bert_exists and not baseline_exists:
        print("\n   ⚠️  At least one model must be trained to run the application!")
        all_good = False
    
    # Check database directory
    print("\n💾 Database")
    print("-" * 60)
    data_dir = Path("data")
    check_item(
        "Data directory exists",
        data_dir.exists(),
        "Create directory: mkdir data"
    )
    
    # Summary
    print("\n" + "="*60)
    if all_good:
        print("🎉 All checks passed! You're ready to run the application.")
        print("="*60)
        print("\nNext steps:")
        print("  1. Start API: uvicorn api.main:app --reload")
        print("  2. Start Dashboard: streamlit run dashboard/app.py")
        print("  3. Visit: http://localhost:8501")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("="*60)
        print("\nQuick fixes:")
        if not dataset_path.exists():
            print("  • Download dataset and place in data/raw/")
        if not bert_exists and not baseline_exists:
            print("  • Train a model (BERT or baseline)")
        print("\nSee QUICKSTART.md for detailed instructions.")
        sys.exit(1)
    
    print()

if __name__ == "__main__":
    main()
