# Inference Module

Production-ready inference pipeline for toxicity detection.

## Overview

The inference module provides a clean, reusable interface for making predictions with the trained baseline model. It's designed for both CLI usage and API integration.

## Architecture

```
ToxicityPredictor
    ↓
Load Model Artifacts
    ↓
Preprocess Text (mode='ml')
    ↓
TF-IDF Vectorization
    ↓
Logistic Regression Prediction
    ↓
ToxicityResult (labels + probabilities)
```

## Components

### 1. ToxicityPredictor Class

Main prediction interface with model loading and inference logic.

```python
from inference.predict import ToxicityPredictor

# Initialize
predictor = ToxicityPredictor(
    model_dir='models/baseline',
    threshold=0.5
)

# Single prediction
result = predictor.predict("Your text here")
print(result.is_toxic)
print(result.toxic_labels)
print(result.max_toxicity_score)

# Batch prediction
results = predictor.predict_batch([
    "Text 1",
    "Text 2",
    "Text 3"
])
```

### 2. Data Classes

**LabelPrediction:**
- `label`: Toxicity category name
- `predicted`: Boolean prediction
- `probability`: Confidence score (0-1)

**ToxicityResult:**
- `text`: Original input text
- `is_toxic`: Overall toxicity flag
- `toxic_labels`: List of predicted labels
- `predictions`: List of LabelPrediction objects
- `max_toxicity_score`: Highest probability across all labels

### 3. Convenience Functions

```python
from inference.predict import predict_single, predict_batch

# Quick single prediction
result = predict_single("Your text here")

# Quick batch prediction
results = predict_batch(["Text 1", "Text 2"])
```

## CLI Usage

### Interactive Mode (Default)

```bash
python src/inference/predict.py
```

Enter text interactively and get instant predictions.

### Example Test Cases

```bash
python src/inference/predict.py --examples
```

Runs 12 predefined test cases covering:
- Toxic examples (insult, threat, obscene, identity hate, severe)
- Non-toxic examples (positive, neutral, question, constructive, informative)
- Edge cases (borderline, sarcasm)

### Batch Mode

```bash
python src/inference/predict.py --batch
```

Demonstrates batch prediction on 6 sample texts.

### Single Prediction

```bash
python src/inference/predict.py --text "Your text here"
```

### Custom Model Directory

```bash
python src/inference/predict.py --model-dir path/to/models --text "Your text"
```

### Custom Threshold

```bash
python src/inference/predict.py --threshold 0.7 --text "Your text"
```

## Programmatic Usage

### Basic Example

```python
import sys
sys.path.insert(0, 'src')

from inference.predict import ToxicityPredictor

# Initialize predictor
predictor = ToxicityPredictor()

# Make prediction
result = predictor.predict("You are an idiot!")

# Access results
print(f"Toxic: {result.is_toxic}")
print(f"Labels: {result.toxic_labels}")
print(f"Max Score: {result.max_toxicity_score:.4f}")

# Iterate over predictions
for pred in result.predictions:
    if pred.predicted:
        print(f"{pred.label}: {pred.probability:.4f}")
```

### Batch Processing

```python
from inference.predict import ToxicityPredictor

predictor = ToxicityPredictor()

texts = [
    "This is great!",
    "You are stupid!",
    "I disagree with you."
]

results = predictor.predict_batch(texts)

for text, result in zip(texts, results):
    print(f"{text[:30]:30s} → {'TOXIC' if result.is_toxic else 'CLEAN'}")
```

### JSON Output

```python
from inference.predict import ToxicityPredictor
import json

predictor = ToxicityPredictor()

# Get result as dictionary
result = predictor.predict("Your text", return_dict=True)

# Convert to JSON
json_output = json.dumps(result, indent=2)
print(json_output)
```

**Output:**
```json
{
  "text": "Your text",
  "is_toxic": false,
  "toxic_labels": [],
  "max_toxicity_score": 0.0234,
  "predictions": [
    {
      "label": "toxic",
      "predicted": false,
      "probability": 0.0234
    },
    ...
  ]
}
```

### Threshold Adjustment

```python
from inference.predict import ToxicityPredictor

predictor = ToxicityPredictor(threshold=0.5)

# Lower threshold = more sensitive (more false positives)
predictor.set_threshold(0.3)

# Higher threshold = less sensitive (more false negatives)
predictor.set_threshold(0.7)
```

## FastAPI Integration

The module is designed for easy FastAPI integration:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from inference.predict import ToxicityPredictor

app = FastAPI()
predictor = ToxicityPredictor()

class PredictionRequest(BaseModel):
    text: str

class PredictionResponse(BaseModel):
    text: str
    is_toxic: bool
    toxic_labels: list
    max_toxicity_score: float

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    result = predictor.predict(request.text, return_dict=True)
    return result

@app.post("/predict/batch")
def predict_batch(texts: list[str]):
    results = predictor.predict_batch(texts, return_dict=True)
    return {"results": results}
```

## Performance

| Metric | Value |
|--------|-------|
| Single prediction | ~10ms |
| Batch (100 samples) | ~500ms |
| Model load time | ~2 seconds |
| Memory usage | ~100 MB |

## Output Format

### Console Output

```
Text: You are an idiot!
Toxic: YES
Max Score: 1.0000
Labels: toxic, insult
Predictions:
  ✓ toxic          : 1.0000
  ✓ insult         : 0.9998
```

### Dictionary Output

```python
{
    'text': 'You are an idiot!',
    'is_toxic': True,
    'toxic_labels': ['toxic', 'insult'],
    'max_toxicity_score': 1.0,
    'predictions': [
        {'label': 'toxic', 'predicted': True, 'probability': 1.0},
        {'label': 'severe_toxic', 'predicted': False, 'probability': 0.23},
        {'label': 'obscene', 'predicted': False, 'probability': 0.45},
        {'label': 'threat', 'predicted': False, 'probability': 0.01},
        {'label': 'insult', 'predicted': True, 'probability': 0.9998},
        {'label': 'identity_hate', 'predicted': False, 'probability': 0.12}
    ]
}
```

## Error Handling

The predictor handles common edge cases:

- **Empty text:** Returns non-toxic result with zero probabilities
- **Missing model files:** Raises `FileNotFoundError` with clear message
- **Invalid threshold:** Raises `ValueError` if threshold not in [0, 1]
- **Preprocessing failures:** Logs warning and returns safe default

## Testing

```bash
# Run all example test cases
python src/inference/predict.py --examples

# Test specific text
python src/inference/predict.py --text "Test text here"

# Test batch processing
python src/inference/predict.py --batch
```

## Future Enhancements

- [ ] Add confidence intervals
- [ ] Support for custom thresholds per label
- [ ] Explanation/interpretability (LIME, SHAP)
- [ ] Caching for repeated predictions
- [ ] Async batch processing
- [ ] Model versioning support
- [ ] A/B testing between models
- [ ] Rate limiting for API deployment
