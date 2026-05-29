# Setup Notes for Team

## 🎯 Quick Reference

This repository is ready for GitHub. Here's what you need to know:

### 📚 Documentation Files (4)
- **README.md** - Main project documentation
- **QUICKSTART.md** - 5-minute setup guide
- **ARCHITECTURE.md** - Technical architecture
- **CONTRIBUTING.md** - Team collaboration guidelines

### ⚠️ Important: Models Not Included

**Models are NOT in the repository** due to file size. Team members must:

1. **Download dataset** from Kaggle:
   - https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge/data
   - Place `train.csv` in `data/raw/`

2. **Train models** (choose one):
   ```bash
   # Option A: BERT model (recommended, ~30-45 min)
   python train_bert_10k.py
   
   # Option B: Baseline model (faster, ~5 min)
   python src/training/baseline_model.py
   ```

3. **Verify setup**:
   ```bash
   python check_setup.py
   ```

### 🚀 Quick Start for New Team Members

```bash
# 1. Clone repo
git clone <repo-url>
cd content-moderation-system

# 2. Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Download dataset (see link above)
# Place in: data/raw/train.csv

# 4. Train model
python train_bert_10k.py

# 5. Verify setup
python check_setup.py

# 6. Run application
uvicorn api.main:app --reload  # Terminal 1
streamlit run dashboard/app.py  # Terminal 2
```

### 📝 Before Pushing to GitHub

Update these placeholders in documentation:
- [ ] Replace `yourusername` with actual GitHub username in:
  - README.md (line ~100)
  - QUICKSTART.md (line ~20)
  - CONTRIBUTING.md (line ~15)

### 🔒 What's Ignored (.gitignore)

- Models (`models/bert/`, `models/baseline/*.pkl`)
- Dataset (`data/raw/*.csv`)
- Database (`*.db`)
- Virtual environment (`venv/`)
- Python cache (`__pycache__/`)
- IDE files (`.vscode/`, `.idea/`)

### ✅ What's Included

- ✅ Source code (api/, dashboard/, src/)
- ✅ Tests (tests/)
- ✅ Documentation (README, QUICKSTART, etc.)
- ✅ Configuration (requirements.txt, .gitignore)
- ✅ Training scripts (train_bert_10k.py)
- ✅ Setup verification (check_setup.py)

### 🎓 For Academic Submission

If submitting for academic purposes:
- Models can be shared separately (Google Drive, etc.)
- Include training logs in report
- Reference dataset source in documentation
- Cite BERT model and libraries used

---

**Questions?** See QUICKSTART.md or open an issue.
