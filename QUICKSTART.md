# 🚀 Quick Start Guide

Get the Content Moderation System up and running in 5 minutes.

## 📋 Prerequisites

- Python 3.8 or higher
- pip package manager
- 4GB+ RAM (8GB+ recommended)
- Git

## ⚡ Quick Setup

### 1. Clone and Navigate

```bash
git clone https://github.com/yourusername/content-moderation-system.git
cd content-moderation-system
```

### 2. Create Virtual Environment

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- PyTorch and Transformers (for BERT model)
- FastAPI and Uvicorn (for backend API)
- Streamlit and Plotly (for frontend dashboard)
- scikit-learn and pandas (for data processing)

**Installation time**: ~5-10 minutes depending on your internet speed.

### 4. Download Dataset

The dataset is required for training models.

```bash
# Download from Kaggle:
# https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge/data

# You need: train.csv
# Place it in: data/raw/train.csv
```

**Manual Download Steps:**
1. Visit the Kaggle competition page
2. Accept the competition rules
3. Download `train.csv`
4. Place it in `data/raw/` directory

### 5. Train Models (REQUIRED)

Models are not included in the repository. You must train them before running the application.

**Option A: Train BERT Model (Recommended)**

```bash
python train_bert_10k.py
```

- **Time**: ~30-45 minutes (GPU) or 2-3 hours (CPU)
- **Output**: `models/bert/final_model/` and `models/bert/tokenizer/`
- **Accuracy**: 90-92%

**Option B: Train Baseline Model (Faster)**

```bash
python src/training/baseline_model.py
```

- **Time**: ~5 minutes
- **Output**: `models/baseline/*.pkl`
- **Accuracy**: 86%

> **⚠️ Important**: You must complete this step before starting the API. The application will not work without trained models.

### 6. Initialize Database

The database will be created automatically when you start the API, but you can initialize it manually:

```bash
python -c "from api.database.db import init_database; init_database(); print('✅ Database initialized')"
```

### 7. Start the Backend API

```bash
uvicorn api.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Keep this terminal running** and open a new terminal for the next step.

### 8. Start the Frontend Dashboard

In a **new terminal** (with venv activated):

```bash
streamlit run dashboard/app.py
```

The dashboard will automatically open in your browser at `http://localhost:8501`.

## ✅ Verify Installation

### Quick Verification Script

Run the setup verification script to check if everything is ready:

```bash
python check_setup.py
```

This will check:
- ✅ Python version (3.8+)
- ✅ Virtual environment active
- ✅ Dependencies installed
- ✅ Dataset downloaded
- ✅ Models trained
- ✅ Database directory exists

### Manual Verification

#### Check API Health

Visit: http://localhost:8000/health

You should see:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "moderator_loaded": true,
  "version": "1.0.0"
}
```

### Check API Documentation

Visit: http://localhost:8000/docs

You'll see interactive API documentation with all endpoints.

### Check Dashboard

Visit: http://localhost:8501

You should see the Content Moderation Dashboard with three pages:
- 🔍 Moderation Tool
- 📊 Analytics Dashboard
- ⚙️ System Status

## 🎯 First Steps

### 1. Test the Moderation Tool

1. Go to **🔍 Moderation Tool** in the dashboard
2. Click on an example text (e.g., "Severe Toxicity")
3. Click **🔍 Analyze Content**
4. View the results: toxicity status, action, severity, and confidence

### 2. View Analytics

1. Go to **📊 Analytics Dashboard**
2. View real-time statistics
3. See action and severity distributions
4. Review recent flagged content

### 3. Check System Status

1. Go to **⚙️ System Status**
2. Verify all components are online:
   - Backend API: 🟢 Online
   - BERT Model: 🟢 Loaded
   - Moderation Engine: 🟢 Ready

## 🧪 Test with API

### Using cURL

```bash
curl -X POST "http://localhost:8000/moderate" \
  -H "Content-Type: application/json" \
  -d '{"text": "You are an idiot!"}'
```

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/moderate",
    json={"text": "You are an idiot!"}
)

print(response.json())
```

Expected output:
```json
{
  "is_toxic": true,
  "action": "HIDE",
  "severity": "HIGH",
  "confidence": 0.75,
  "primary_label": "insult",
  "predictions": {
    "toxic": 0.89,
    "insult": 0.75,
    ...
  },
  "explanation": "Content contains insults and toxic language..."
}
```

## 📊 Populate Test Data (Optional)

To see analytics with sample data:

```bash
python populate_test_data.py
```

This will add 20 sample moderation records to the database.

## 🔧 Common Issues & Solutions

### Issue: "Model not found" or "Model not loaded"

**Cause**: Models are not included in the repository and must be trained.

**Solution**: Train the models before starting the API.

```bash
# Train BERT model (recommended)
python train_bert_10k.py

# OR train baseline model (faster)
python src/training/baseline_model.py
```

**Verify models exist:**
```bash
# Check BERT model
ls models/bert/final_model/

# Check baseline model
ls models/baseline/
```

### Issue: "ModuleNotFoundError: No module named 'api'"

**Solution**: Make sure you're in the project root directory and the virtual environment is activated.

```bash
# Check current directory
pwd  # Should show: .../content-moderation-system

# Activate venv if not activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### Issue: "Port 8000 already in use"

**Solution**: Kill the process using port 8000 or use a different port.

```bash
# Use different port
uvicorn api.main:app --reload --port 8001

# Update API_BASE_URL in dashboard/app.py to http://127.0.0.1:8001
```

### Issue: "Model not found" or "Model not loaded"

**Solution**: The pre-trained BERT model should be in `models/bert/final_model/`. If missing:

```bash
# Check if model exists
ls models/bert/final_model/

# If missing, you need to train the model (requires dataset)
python train_bert_10k.py
```

### Issue: "Database locked"

**Solution**: Close any open database connections or delete the database file.

```bash
# Remove database (will be recreated)
rm data/moderation_history.db

# Restart the API
uvicorn api.main:app --reload
```

### Issue: Streamlit shows "Connection error"

**Solution**: Make sure the FastAPI backend is running first.

```bash
# Terminal 1: Start API first
uvicorn api.main:app --reload

# Terminal 2: Then start Streamlit
streamlit run dashboard/app.py
```

### Issue: "No module named 'torch'"

**Solution**: PyTorch installation failed. Install manually:

```bash
# CPU version
pip install torch torchvision torchaudio

# GPU version (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 🛠️ Development Setup

### Install Development Dependencies

```bash
pip install pytest pytest-cov black flake8 mypy
```

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_inference.py -v
```

### Code Formatting

```bash
# Format code
black src/ api/ dashboard/

# Check style
flake8 src/ api/ dashboard/
```

## 📚 Next Steps

1. **Read the Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md) for system design details
2. **Explore the Code**: Check out the modular structure in `src/`, `api/`, and `dashboard/`
3. **Try the API**: Use the interactive docs at http://localhost:8000/docs
4. **Customize Rules**: Modify moderation rules in `src/moderation/rules.py`
5. **Train Your Model**: Use your own dataset with `src/training/train_bert.py`

## 🆘 Getting Help

- **Check Documentation**: See [README.md](README.md) and [ARCHITECTURE.md](ARCHITECTURE.md)
- **Run Diagnostics**: Use `python verify_database_connection.py` to check database
- **View Logs**: Check terminal output for error messages
- **Open an Issue**: Report bugs or ask questions on GitHub

## 🎉 You're Ready!

Your Content Moderation System is now running. Start moderating content and building safer online communities!

**Quick Links:**
- Dashboard: http://localhost:8501
- API Docs: http://localhost:8000/docs
- API Health: http://localhost:8000/health

---

**Need help?** Open an issue or check the troubleshooting section above.
