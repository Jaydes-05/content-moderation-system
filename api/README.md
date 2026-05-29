## Content Moderation API

Production-ready FastAPI backend for AI-based content moderation.

## Features

- **Toxicity Detection**: Detect toxic, insulting, threatening, and hateful content
- **Moderation Decisions**: Get actionable moderation recommendations (ALLOW, WARNING, HIDE, BLOCK)
- **Batch Processing**: Process up to 100 texts in a single request
- **Health Checks**: Monitor API and model status
- **Auto Documentation**: Interactive Swagger UI and ReDoc
- **CORS Support**: Ready for frontend integration
- **Error Handling**: Comprehensive error handling and logging
- **Type Safety**: Full Pydantic validation

## Quick Start

### Prerequisites

1. **Train the model** (if not done yet):
```bash
python train_bert_10k.py
```

2. **Install FastAPI dependencies**:
```bash
pip install fastapi uvicorn pydantic
```

### Run the API

```bash
# Development mode (with auto-reload)
uvicorn api.main:app --reload

# Production mode
uvicorn api.main:app --host 0.0.0.0 --port 8000

# With custom settings
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access the API

- **API**: http://localhost:8000
- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### GET /
Root endpoint with API information

### GET /health
Health check endpoint
- Returns API status and model loading state

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "moderator_loaded": true,
  "version": "1.0.0"
}
```

### POST /predict
Get toxicity predictions (no moderation decision)

**Request:**
```json
{
  "text": "You are an idiot!"
}
```

**Response:**
```json
{
  "text": "You are an idiot!",
  "is_toxic": true,
  "predictions": {
    "toxic": 0.94,
    "severe_toxic": 0.45,
    "obscene": 0.67,
    "threat": 0.12,
    "insult": 0.88,
    "identity_hate": 0.23
  },
  "toxic_labels": ["toxic", "insult"],
  "max_score": 0.94,
  "confidence": 0.94
}
```

### POST /moderate
Get toxicity predictions + moderation decision

**Request:**
```json
{
  "text": "You are an idiot!"
}
```

**Response:**
```json
{
  "text": "You are an idiot!",
  "is_toxic": true,
  "predictions": {
    "toxic": 0.94,
    "insult": 0.88
  },
  "action": "BLOCK",
  "severity": "HIGH",
  "primary_label": "toxic",
  "confidence": 0.94,
  "explanation": "Content contains severe toxicity (primary: toxic, confidence: 0.94). Recommended to block and remove content."
}
```

### POST /batch-moderate
Process multiple texts (max 100)

**Request:**
```json
{
  "texts": [
    "Great post!",
    "You are stupid!"
  ]
}
```

**Response:**
```json
{
  "total": 2,
  "results": [
    {
      "text": "Great post!",
      "is_toxic": false,
      "predictions": {"toxic": 0.05},
      "action": "ALLOW",
      "severity": "NONE",
      "primary_label": "none",
      "confidence": 0.05,
      "explanation": "Content appears safe."
    },
    {
      "text": "You are stupid!",
      "is_toxic": true,
      "predictions": {"toxic": 0.88, "insult": 0.85},
      "action": "BLOCK",
      "severity": "HIGH",
      "primary_label": "insult",
      "confidence": 0.88,
      "explanation": "Content should be blocked."
    }
  ],
  "statistics": {
    "toxic_count": 1,
    "safe_count": 1,
    "actions": {
      "ALLOW": 1,
      "BLOCK": 1
    }
  }
}
```

## Usage Examples

### Python (requests)

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Single prediction
response = requests.post(
    "http://localhost:8000/predict",
    json={"text": "You are an idiot!"}
)
print(response.json())

# Moderation
response = requests.post(
    "http://localhost:8000/moderate",
    json={"text": "You are an idiot!"}
)
print(response.json())

# Batch moderation
response = requests.post(
    "http://localhost:8000/batch-moderate",
    json={
        "texts": [
            "Great post!",
            "You are stupid!"
        ]
    }
)
print(response.json())
```

### cURL

```bash
# Health check
curl http://localhost:8000/health

# Prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "You are an idiot!"}'

# Moderation
curl -X POST http://localhost:8000/moderate \
  -H "Content-Type: application/json" \
  -d '{"text": "You are an idiot!"}'

# Batch moderation
curl -X POST http://localhost:8000/batch-moderate \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Great post!", "You are stupid!"]}'
```

### JavaScript (fetch)

```javascript
// Health check
fetch('http://localhost:8000/health')
  .then(res => res.json())
  .then(data => console.log(data));

// Moderation
fetch('http://localhost:8000/moderate', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({text: 'You are an idiot!'})
})
  .then(res => res.json())
  .then(data => console.log(data));
```

## Architecture

```
api/
├── __init__.py       # Package initialization
├── main.py           # FastAPI application and endpoints
├── schemas.py        # Pydantic request/response models
├── services.py       # Business logic (model inference)
└── README.md         # This file
```

### Design Principles

1. **Single Model Loading**: Models loaded once at startup, reused for all requests
2. **Separation of Concerns**: Clear separation between API, schemas, and services
3. **Type Safety**: Full Pydantic validation for requests and responses
4. **Error Handling**: Comprehensive exception handling with structured errors
5. **Logging**: Structured logging for monitoring and debugging
6. **Scalability**: Stateless design ready for horizontal scaling

## Configuration

### Model Path
Default: `models/bert/final_model`

To use a different model, modify `api/services.py`:
```python
model_service.load_models(model_dir="path/to/your/model")
```

### Moderation Preset
Default: `moderate`

Available presets:
- `strict`: Low tolerance (family-friendly)
- `moderate`: Balanced (general social media)
- `lenient`: High tolerance (adult platforms)
- `zero_tolerance`: Block everything suspicious

To change preset, modify `api/services.py`:
```python
model_service.load_models(preset="strict")
```

### CORS
Default: Allow all origins (`*`)

For production, configure in `api/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Error Handling

The API returns structured error responses:

```json
{
  "error": "ValidationError",
  "message": "Text cannot be empty",
  "detail": null
}
```

Error types:
- `ValidationError` (422): Invalid input
- `HTTPException` (4xx): Client errors
- `InternalServerError` (500): Server errors

## Performance

- **Startup time**: 5-10 seconds (model loading)
- **Single prediction**: ~100-200ms (CPU) / ~20-50ms (GPU)
- **Batch (100 items)**: ~5-10 seconds (CPU) / ~1-2 seconds (GPU)
- **Memory usage**: ~2GB (model + API)

## Production Deployment

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Multiple Workers

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Behind Nginx

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Logs
Logs are written to stdout in structured format:
```
2026-05-08 17:00:00 - api.main - INFO - Moderation request: You are an idiot!
2026-05-08 17:00:00 - api.main - INFO - Moderation complete: action=BLOCK, severity=HIGH
```

## Testing

```python
# Test the API
import requests

def test_api():
    # Health check
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    
    # Prediction
    response = requests.post(
        "http://localhost:8000/predict",
        json={"text": "You are an idiot!"}
    )
    assert response.status_code == 200
    assert response.json()["is_toxic"] == True
    
    print("All tests passed!")

if __name__ == "__main__":
    test_api()
```

## Troubleshooting

### Model not found
```
FileNotFoundError: Model not found at models/bert/final_model
```
**Solution**: Train the model first:
```bash
python train_bert_10k.py
```

### Port already in use
```
ERROR: [Errno 48] Address already in use
```
**Solution**: Use a different port:
```bash
uvicorn api.main:app --port 8001
```

### Import errors
```
ModuleNotFoundError: No module named 'fastapi'
```
**Solution**: Install dependencies:
```bash
pip install fastapi uvicorn pydantic
```

## Next Steps

1. **Frontend Integration**: Build Streamlit dashboard
2. **Database Logging**: Store predictions and decisions
3. **User Authentication**: Add API keys or OAuth
4. **Rate Limiting**: Prevent abuse
5. **Caching**: Cache frequent predictions
6. **Monitoring**: Add Prometheus metrics
7. **A/B Testing**: Test different moderation presets

## Support

For issues or questions:
1. Check the interactive docs: http://localhost:8000/docs
2. Review the logs
3. Test with curl or Postman
4. Check model is trained and loaded

## License

Part of the Content Moderation System MLOps project.
