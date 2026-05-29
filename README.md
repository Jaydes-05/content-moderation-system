# 🛡️ AI-Based Content Moderation System

An end-to-end MLOps project for detecting and moderating toxic comments using deep learning. Built with DistilBERT, FastAPI, and Streamlit for production-ready deployment.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Model Performance](#model-performance)
- [Screenshots](#screenshots)
- [Future Scope](#future-scope)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

This project implements a complete content moderation pipeline using the [Jigsaw Toxic Comment Classification](https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge) dataset. It detects six types of toxicity: toxic, severe toxic, obscene, threat, insult, and identity hate.

The system provides:
- **Real-time toxicity detection** via REST API
- **Interactive web dashboard** for content moderation
- **Persistent analytics** with SQLite database
- **Production-ready deployment** with FastAPI and Streamlit

> **📊 Dataset**: This project uses the Jigsaw Toxic Comment Classification dataset from Kaggle. You'll need to download `train.csv` (159,571 comments) to train the models. [Download here](https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge/data)

## ✨ Key Features

### 🤖 Machine Learning
- **DistilBERT transformer model** for state-of-the-art accuracy (90-92%)
- **Multi-label classification** across 6 toxicity categories
- **Baseline TF-IDF model** for comparison (86% accuracy)
- **Comprehensive preprocessing pipeline** with multiple modes

### 🚀 Backend API
- **FastAPI REST API** with automatic OpenAPI documentation
- **Health checks** and model status endpoints
- **Batch processing** support for multiple texts
- **Automatic database logging** of all moderation decisions

### 🎨 Frontend Dashboard
- **Modern Streamlit interface** with dark theme
- **Real-time moderation tool** with confidence scores
- **Analytics dashboard** with interactive charts
- **System status monitoring** with health checks

### 📊 Analytics & Storage
- **SQLite database** for persistent storage
- **Real-time metrics**: total analyzed, toxic rate, action distribution
- **Historical tracking** of flagged content
- **Optimized queries** with proper indexing

### 🔧 Moderation Engine
- **Rule-based decision logic** with configurable thresholds
- **Severity classification**: NONE, LOW, MEDIUM, HIGH, CRITICAL
- **Action recommendations**: ALLOW, WARNING, HIDE, BLOCK
- **Confidence scoring** for transparency

## 🏗️ System Architecture

```
┌─────────────────┐
│  User Input     │
│  (Streamlit)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI        │
│  Backend        │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌──────────────┐
│  BERT   │ │  Moderation  │
│  Model  │ │  Engine      │
└────┬────┘ └──────┬───────┘
     │             │
     └──────┬──────┘
            ▼
    ┌───────────────┐
    │  SQLite DB    │
    │  (Analytics)  │
    └───────────────┘
```

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

## 🛠️ Technology Stack

### Machine Learning
- **PyTorch** - Deep learning framework
- **Transformers** (Hugging Face) - DistilBERT model
- **scikit-learn** - Baseline models and metrics
- **pandas** & **numpy** - Data processing

### Backend
- **FastAPI** - Modern REST API framework
- **Uvicorn** - ASGI server
- **SQLite** - Lightweight database
- **Pydantic** - Data validation

### Frontend
- **Streamlit** - Interactive web dashboard
- **Plotly** - Interactive charts
- **Requests** - API client

### Development
- **pytest** - Testing framework
- **Jupyter** - Exploratory analysis
- **Git** - Version control

## 📁 Project Structure

```
content-moderation-system/
├── api/                          # FastAPI backend
│   ├── database/                 # Database models and operations
│   │   ├── db.py                 # Database functions
│   │   └── models.py             # Schema definitions
│   ├── main.py                   # FastAPI application
│   ├── schemas.py                # Pydantic models
│   └── services.py               # Business logic
│
├── dashboard/                    # Streamlit frontend
│   └── app.py                    # Dashboard application
│
├── src/                          # Core modules
│   ├── inference/                # Prediction pipeline
│   │   ├── predict.py            # Baseline inference
│   │   └── bert_predict.py       # BERT inference
│   ├── moderation/               # Moderation engine
│   │   ├── moderator.py          # Decision logic
│   │   └── rules.py              # Moderation rules
│   ├── preprocessing/            # Text preprocessing
│   │   └── preprocess.py         # Cleaning functions
│   └── training/                 # Model training
│       ├── baseline_model.py     # TF-IDF + LogReg
│       └── train_bert.py         # BERT training
│
├── data/                         # Data storage
│   ├── raw/                      # Original datasets
│   ├── processed/                # Cleaned datasets
│   └── moderation_history.db     # Analytics database
│
├── models/                       # Saved models
│   ├── baseline/                 # TF-IDF model
│   └── bert/                     # BERT model
│
├── notebooks/                    # Jupyter notebooks
│   └── phase1_eda.ipynb          # Exploratory analysis
│
├── tests/                        # Test suite
│   ├── test_preprocess.py
│   ├── test_inference.py
│   └── test_bert_pipeline.py
│
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── QUICKSTART.md                 # Quick setup guide
└── ARCHITECTURE.md               # Detailed architecture
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip package manager
- 4GB+ RAM (8GB+ recommended for training)
- GPU optional (for faster training)

### Quick Setup

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/content-moderation-system.git
cd content-moderation-system

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download dataset (REQUIRED for training)
# Download from: https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge/data
# Place train.csv in data/raw/

# 5. Train the models (REQUIRED - models not included in repo)
# Option A: Train BERT model (recommended, ~30-45 min with GPU)
python train_bert_10k.py

# Option B: Train baseline model (faster, ~5 min)
python src/training/baseline_model.py

# 6. Start the backend API
uvicorn api.main:app --reload

# 7. Start the frontend (in another terminal)
streamlit run dashboard/app.py
```

**Verify your setup:**
```bash
# Run the setup verification script
python check_setup.py
```

Access the application:
- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

> **⚠️ Important**: Models are not included in the repository due to size. You must train them before running the application (see step 5 above).

## 📖 Usage

### Model Training (Required First Step)

Since models are not included in the repository, you must train them before using the application.

#### Option 1: Train BERT Model (Recommended)

```bash
# 1. Download the dataset
# Visit: https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge/data
# Download train.csv and place it in data/raw/

# 2. Train the model (~30-45 minutes with GPU, 2-3 hours with CPU)
python train_bert_10k.py

# This will create:
# - models/bert/final_model/
# - models/bert/tokenizer/
# - results/bert_metrics.json
```

**Training Configuration:**
- Model: DistilBERT (distilbert-base-uncased)
- Training samples: 10,000 (configurable)
- Epochs: 3
- Batch size: 16
- Learning rate: 2e-5

#### Option 2: Train Baseline Model (Faster Alternative)

```bash
# Train TF-IDF + Logistic Regression model (~5 minutes)
python src/training/baseline_model.py

# This will create:
# - models/baseline/tfidf_vectorizer.pkl
# - models/baseline/logistic_model.pkl
# - results/baseline_metrics.json
```

> **Note**: The BERT model provides better accuracy (90-92%) compared to the baseline (86%), but takes longer to train.

### Moderation Tool
1. Navigate to **🔍 Moderation Tool** in the dashboard
2. Enter or select example text
3. Click **Analyze Content**
4. View toxicity breakdown, severity, and recommended action

### Analytics Dashboard
1. Navigate to **📊 Analytics Dashboard**
2. View real-time statistics and charts
3. Monitor action distribution and severity levels
4. Review recent flagged content

### API Usage

```python
import requests

# Moderate text
response = requests.post(
    "http://localhost:8000/moderate",
    json={"text": "Your text here"}
)

result = response.json()
print(f"Toxic: {result['is_toxic']}")
print(f"Action: {result['action']}")
print(f"Confidence: {result['confidence']}")
```

### Programmatic Usage

```python
from src.inference.bert_predict import BERTToxicityPredictor

# Initialize predictor
predictor = BERTToxicityPredictor()

# Predict
result = predictor.predict("You are an idiot!")
print(f"Toxic: {result.is_toxic}")
print(f"Predictions: {result.predictions}")
```

## 📊 Model Performance

### DistilBERT Model (Production)
- **Accuracy**: 90-92%
- **F1 Score (macro)**: 0.70-0.75
- **Training Time**: ~30-45 minutes (GPU)
- **Inference Time**: ~50-100ms per text

### Baseline Model (TF-IDF + LogReg)
- **Accuracy**: 86.15%
- **F1 Score (macro)**: 0.5313
- **F1 Score (micro)**: 0.6452
- **Hamming Loss**: 0.0344

### Performance Comparison
| Metric | Baseline | DistilBERT | Improvement |
|--------|----------|------------|-------------|
| Accuracy | 86.15% | 90-92% | +5-7% |
| F1 (macro) | 0.53 | 0.70-0.75 | +40% |
| Inference | <10ms | ~50-100ms | - |

## � Future Scope

### Short-term Enhancements
- [ ] Add user authentication and role-based access
- [ ] Implement rate limiting and API keys
- [ ] Add export functionality for analytics data
- [ ] Create Docker containerization
- [ ] Add CI/CD pipeline with GitHub Actions

### Medium-term Features
- [ ] Multi-language support (non-English text)
- [ ] Custom moderation rules per organization
- [ ] A/B testing framework for model comparison
- [ ] Real-time monitoring dashboard with Grafana
- [ ] Webhook notifications for critical content

### Long-term Vision
- [ ] Fine-tune on domain-specific data
- [ ] Implement active learning pipeline
- [ ] Add explainability with LIME/SHAP
- [ ] Deploy to cloud (AWS/GCP/Azure)
- [ ] Scale with Kubernetes and load balancing

## 🤝 Contributing

We welcome contributions from team members! Here's how to get started:

### Development Workflow
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes
4. **Test** your changes (`pytest tests/`)
5. **Commit** with clear messages (`git commit -m 'Add amazing feature'`)
6. **Push** to your branch (`git push origin feature/amazing-feature`)
7. **Open** a Pull Request

### Code Standards
- Follow PEP 8 style guide
- Add docstrings to all functions
- Write unit tests for new features
- Update documentation as needed
- Keep commits atomic and well-described

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_inference.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Areas for Contribution
- 🐛 Bug fixes and issue resolution
- ✨ New features and enhancements
- 📝 Documentation improvements
- 🧪 Additional test coverage
- 🎨 UI/UX improvements
- ⚡ Performance optimizations

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Dataset**: [Jigsaw Toxic Comment Classification Challenge](https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge)
- **Model**: [DistilBERT](https://huggingface.co/distilbert-base-uncased) by Hugging Face
- **Inspiration**: Building safer online communities through AI

## 📧 Contact

For questions, suggestions, or collaboration opportunities, please open an issue or contact the team.

---

**Built with ❤️ for safer online communities**
