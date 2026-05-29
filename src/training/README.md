# Training Module

Baseline and advanced models for toxicity classification.

## Baseline Model

### Architecture

**TF-IDF + Logistic Regression** multi-label classifier:

```
Input Text
    ↓
Preprocessing (mode='ml')
    ↓
TF-IDF Vectorizer (10k features, 1-2 grams)
    ↓
OneVsRestClassifier (6 binary classifiers)
    ↓
Predictions (6 toxicity labels)
```

### Labels

| Label | Description | Prevalence |
|-------|-------------|------------|
| `toxic` | General toxicity | 9.59% |
| `severe_toxic` | Extremely toxic | 1.00% |
| `obscene` | Obscene language | 5.27% |
| `threat` | Threatening content | 0.30% |
| `insult` | Insulting language | 4.92% |
| `identity_hate` | Identity-based hate | 0.88% |

### Performance

**Test Set Results (31,912 samples):**

| Metric | Value |
|--------|-------|
| Accuracy (exact match) | 86.15% |
| Hamming Loss | 0.0344 |
| Jaccard Score | 0.0583 |
| Precision (micro) | 0.5213 |
| Precision (macro) | 0.4139 |
| Recall (micro) | 0.8465 |
| Recall (macro) | 0.7973 |
| F1 (micro) | 0.6452 |
| F1 (macro) | 0.5313 |

**Per-Label Performance:**

| Label | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| toxic | 0.5970 | 0.8578 | 0.7041 | 3,059 |
| severe_toxic | 0.2810 | 0.8190 | 0.4185 | 315 |
| obscene | 0.6166 | 0.8659 | 0.7203 | 1,722 |
| threat | 0.2509 | 0.7158 | 0.3716 | 95 |
| insult | 0.5220 | 0.8471 | 0.6460 | 1,596 |
| identity_hate | 0.2160 | 0.6784 | 0.3276 | 283 |

### Key Observations

✓ **High Recall** — Model catches most toxic content (79.7% macro recall)  
✗ **Lower Precision** — More false positives (41.4% macro precision)  
⚠️ **Class Imbalance** — Rare labels (threat, identity_hate) have lower precision  
✓ **Good F1 on Common Labels** — toxic, obscene, insult perform well  

**Trade-off:** The model prioritizes catching toxic content (high recall) over minimizing false positives (lower precision). This is appropriate for content moderation where missing toxic content is worse than over-flagging.

### Hyperparameters

```python
TfidfVectorizer(
    max_features=10000,
    ngram_range=(1, 2),
    min_df=5,
    max_df=0.8,
    sublinear_tf=True
)

LogisticRegression(
    C=4.0,
    solver='lbfgs',
    max_iter=1000,
    class_weight='balanced'
)
```

## Usage

### Training

```bash
python src/training/baseline_model.py
```

**Output:**
- `models/baseline/tfidf_vectorizer.pkl` — Fitted TF-IDF vectorizer
- `models/baseline/logistic_model.pkl` — Trained classifier
- `results/baseline_metrics.json` — Evaluation metrics

### Inference

**Option 1: Use the inference script**

```bash
python src/training/inference.py
```

**Option 2: Programmatic usage**

```python
import sys
sys.path.insert(0, 'src')

from training.baseline_model import BaselineClassifier
from preprocessing import preprocess_pipeline
import pandas as pd

# Load trained model
classifier = BaselineClassifier.load_artifacts('models/baseline')

# Prepare text
text = "You are an idiot and should be ashamed!"
text_clean = preprocess_pipeline(text, mode='ml')

# Get predictions
predictions = classifier.predict(pd.Series([text_clean]))[0]
probabilities = classifier.predict_proba(pd.Series([text_clean]))[0]

# Display results
for i, label in enumerate(classifier.label_cols):
    if predictions[i]:
        print(f"{label}: {probabilities[i]:.4f}")
```

**Output:**
```
toxic: 0.9999
severe_toxic: 0.6935
obscene: 0.9930
insult: 1.0000
identity_hate: 0.7085
```

### Batch Inference

```python
# Load dataset
df = pd.read_csv('data/test.csv')

# Preprocess
df['text_clean'] = df['comment_text'].apply(
    lambda x: preprocess_pipeline(x, mode='ml')
)

# Predict
predictions = classifier.predict(df['text_clean'])
probabilities = classifier.predict_proba(df['text_clean'])

# Add to dataframe
for i, label in enumerate(classifier.label_cols):
    df[f'{label}_pred'] = predictions[:, i]
    df[f'{label}_prob'] = probabilities[:, i]
```

## Model Artifacts

### File Structure

```
models/baseline/
├── tfidf_vectorizer.pkl    # 10k vocabulary, fitted on 127k samples
└── logistic_model.pkl       # 6 binary classifiers (OneVsRestClassifier)

results/
└── baseline_metrics.json    # Complete evaluation metrics
```

### Artifact Sizes

- `tfidf_vectorizer.pkl`: ~2.5 MB
- `logistic_model.pkl`: ~1.2 MB
- Total: ~3.7 MB (lightweight, production-ready)

## Future Improvements

### Short-term
- [ ] Hyperparameter tuning (grid search on C, max_features)
- [ ] Try different classifiers (SVM, Random Forest, XGBoost)
- [ ] Ensemble methods (voting, stacking)
- [ ] Threshold tuning per label (optimize precision/recall trade-off)

### Medium-term
- [ ] Add BERT/RoBERTa fine-tuning
- [ ] Multi-task learning (share representations across labels)
- [ ] Active learning (focus on hard examples)
- [ ] Explainability (LIME, SHAP)

### Long-term
- [ ] Real-time inference API (FastAPI)
- [ ] Model monitoring (drift detection)
- [ ] A/B testing framework
- [ ] MLflow integration for experiment tracking

## Comparison with Transformer Models

| Aspect | Baseline (TF-IDF + LogReg) | Transformer (BERT) |
|--------|----------------------------|---------------------|
| Training time | ~30 seconds | ~2-4 hours |
| Inference speed | ~1000 samples/sec | ~10-50 samples/sec |
| Model size | ~4 MB | ~400 MB |
| F1 (macro) | 0.53 | 0.70-0.75 (expected) |
| Context understanding | ✗ Bag-of-words | ✓ Contextual |
| Deployment | ✓ Easy | ⚠️ Requires GPU |

**When to use baseline:**
- Quick prototyping
- Resource-constrained environments
- High-throughput requirements
- Interpretability needed

**When to use transformers:**
- Maximum accuracy required
- Context-dependent toxicity
- Sarcasm/irony detection
- Production with GPU infrastructure
