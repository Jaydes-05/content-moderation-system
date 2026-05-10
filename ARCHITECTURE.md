# 🏗️ System Architecture

Detailed technical architecture of the Content Moderation System.

## 📋 Table of Contents

- [Overview](#overview)
- [System Components](#system-components)
- [Data Flow](#data-flow)
- [Component Details](#component-details)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Deployment Architecture](#deployment-architecture)

## 🎯 Overview

The Content Moderation System follows a **microservices-inspired architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                          │
│                   (Streamlit Dashboard)                     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     API LAYER                               │
│                   (FastAPI Backend)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Routing    │  │  Validation  │  │   Services   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  ML MODEL    │  │  MODERATION  │  │   DATABASE   │
│   (BERT)     │  │    ENGINE    │  │   (SQLite)   │
│              │  │              │  │              │
│ • Inference  │  │ • Rules      │  │ • Analytics  │
│ • Scoring    │  │ • Decisions  │  │ • History    │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Design Principles

1. **Modularity**: Each component has a single responsibility
2. **Scalability**: Stateless API design for horizontal scaling
3. **Maintainability**: Clear interfaces and documentation
4. **Testability**: Unit tests for all core components
5. **Performance**: Optimized database queries and model inference

## 🧩 System Components

### 1. Frontend (Streamlit Dashboard)

**Location**: `dashboard/app.py`

**Purpose**: Interactive web interface for content moderation and analytics.

**Features**:
- 🔍 **Moderation Tool**: Real-time text analysis
- 📊 **Analytics Dashboard**: Statistics and visualizations
- ⚙️ **System Status**: Health monitoring

**Technology**:
- Streamlit for UI framework
- Plotly for interactive charts
- Requests for API communication

**Key Functions**:
```python
page_moderation_tool()      # Moderation interface
page_analytics_dashboard()  # Analytics visualization
page_system_status()        # Health monitoring
fetch_analytics_data()      # Database queries
```

### 2. Backend API (FastAPI)

**Location**: `api/main.py`

**Purpose**: RESTful API for toxicity detection and moderation.

**Endpoints**:
- `GET /health` - Health check
- `POST /predict` - Get toxicity predictions
- `POST /moderate` - Get moderation decision
- `POST /batch-moderate` - Batch processing

**Technology**:
- FastAPI for API framework
- Pydantic for data validation
- Uvicorn as ASGI server

**Architecture**:
```
api/
├── main.py          # FastAPI app and routes
├── schemas.py       # Pydantic models (request/response)
├── services.py      # Business logic
└── database/        # Database layer
    ├── db.py        # Database operations
    └── models.py    # Schema definitions
```

### 3. ML Model (DistilBERT)

**Location**: `src/inference/bert_predict.py`

**Purpose**: Deep learning model for toxicity classification.

**Architecture**:
```
Input Text
    ↓
Tokenizer (DistilBERT)
    ↓
Transformer Encoder (6 layers)
    ↓
Classification Head
    ↓
Sigmoid Activation
    ↓
6 Toxicity Scores [0-1]
```

**Model Details**:
- **Base Model**: distilbert-base-uncased
- **Parameters**: 66M
- **Input**: Text (max 512 tokens)
- **Output**: 6 probabilities (multi-label)
- **Labels**: toxic, severe_toxic, obscene, threat, insult, identity_hate

**Inference Pipeline**:
```python
class BERTToxicityPredictor:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(...)
        self.model = AutoModelForSequenceClassification.from_pretrained(...)
    
    def predict(self, text: str) -> PredictionResult:
        # 1. Tokenize
        inputs = self.tokenizer(text, ...)
        
        # 2. Forward pass
        outputs = self.model(**inputs)
        
        # 3. Apply sigmoid
        probs = torch.sigmoid(outputs.logits)
        
        # 4. Return results
        return PredictionResult(...)
```

### 4. Moderation Engine

**Location**: `src/moderation/moderator.py`

**Purpose**: Rule-based decision logic for content moderation.

**Decision Flow**:
```
Toxicity Scores
    ↓
Determine Primary Label (max score)
    ↓
Calculate Severity (NONE/LOW/MEDIUM/HIGH/CRITICAL)
    ↓
Determine Action (ALLOW/WARNING/HIDE/BLOCK)
    ↓
Generate Explanation
    ↓
Return ModerationDecision
```

**Severity Thresholds**:
```python
SEVERITY_THRESHOLDS = {
    'CRITICAL': 0.9,  # Extreme toxicity
    'HIGH': 0.7,      # Clear toxicity
    'MEDIUM': 0.5,    # Moderate toxicity
    'LOW': 0.3,       # Mild toxicity
    'NONE': 0.0       # Clean content
}
```

**Action Rules**:
```python
ACTION_RULES = {
    'CRITICAL': 'BLOCK',   # Remove immediately
    'HIGH': 'HIDE',        # Hide from public
    'MEDIUM': 'HIDE',      # Hide from public
    'LOW': 'WARNING',      # Show warning
    'NONE': 'ALLOW'        # Allow publication
}
```

### 5. Database Layer (SQLite)

**Location**: `api/database/db.py`

**Purpose**: Persistent storage for moderation history and analytics.

**Schema**: See [Database Schema](#database-schema) section below.

**Key Operations**:
```python
# Write operations
insert_moderation_record()  # Save moderation decision

# Analytics queries
get_total_analyzed()        # Total count
get_toxic_count()           # Toxic count
get_action_distribution()   # Action breakdown
get_severity_distribution() # Severity breakdown
get_recent_flagged()        # Recent toxic content
```

**Performance Optimizations**:
- Indexed columns: `timestamp`, `is_toxic`, `moderation_action`
- Connection pooling with `check_same_thread=False`
- Row factory for dict-like access
- Prepared statements for SQL injection prevention

## 🔄 Data Flow

### Request Flow (Moderation)

```
1. User Input
   └─> Text entered in Streamlit dashboard

2. API Request
   └─> POST /moderate with JSON payload

3. Validation
   └─> Pydantic validates request schema

4. ML Inference
   └─> BERT model predicts toxicity scores

5. Moderation Decision
   └─> Engine applies rules and determines action

6. Database Storage
   └─> Record saved to SQLite

7. API Response
   └─> JSON response with decision

8. UI Update
   └─> Dashboard displays results
```

### Analytics Flow

```
1. Dashboard Request
   └─> User navigates to Analytics page

2. Database Queries
   └─> Multiple aggregation queries executed

3. Data Processing
   └─> Results formatted for visualization

4. Chart Rendering
   └─> Plotly generates interactive charts

5. Display
   └─> Streamlit renders dashboard
```

## 🔍 Component Details

### Frontend Architecture

**File**: `dashboard/app.py` (~700 lines)

**Structure**:
```python
# Configuration
API_BASE_URL = "http://127.0.0.1:8000"
st.set_page_config(...)

# Custom CSS
st.markdown("""<style>...</style>""")

# API Functions
check_api_health()
moderate_text()

# UI Components
render_sidebar()
render_action_badge()
create_toxicity_chart()

# Pages
page_moderation_tool()
page_analytics_dashboard()
page_system_status()

# Main
main()
```

**State Management**:
```python
# Session state for persistence
st.session_state.total_analyzed
st.session_state.total_toxic
st.session_state.current_text
```

### Backend Architecture

**File**: `api/main.py` (~200 lines)

**Structure**:
```python
# FastAPI app
app = FastAPI(title="Content Moderation API")

# Startup event
@app.on_event("startup")
async def startup_event():
    init_database()
    load_models()

# Routes
@app.get("/health")
@app.post("/predict")
@app.post("/moderate")
@app.post("/batch-moderate")

# Error handling
@app.exception_handler(Exception)
```

**Request/Response Models**:
```python
# schemas.py
class ModerationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)

class ModerationResponse(BaseModel):
    is_toxic: bool
    action: str
    severity: str
    confidence: float
    primary_label: str
    predictions: Dict[str, float]
    explanation: str
```

### ML Model Architecture

**Training**: `src/training/train_bert.py`

**Inference**: `src/inference/bert_predict.py`

**Model Configuration**:
```python
MODEL_CONFIG = {
    'model_name': 'distilbert-base-uncased',
    'num_labels': 6,
    'max_length': 128,
    'batch_size': 16,
    'learning_rate': 2e-5,
    'epochs': 3,
    'warmup_steps': 500
}
```

**Training Pipeline**:
```python
1. Load dataset (train.csv)
2. Preprocess text
3. Tokenize with DistilBERT tokenizer
4. Create PyTorch DataLoader
5. Initialize model with classification head
6. Train with Hugging Face Trainer
7. Evaluate on validation set
8. Save model and tokenizer
```

**Inference Pipeline**:
```python
1. Load saved model and tokenizer
2. Preprocess input text
3. Tokenize (padding, truncation)
4. Forward pass through model
5. Apply sigmoid activation
6. Return probabilities
```

### Moderation Engine Architecture

**File**: `src/moderation/moderator.py`

**Class Structure**:
```python
class ContentModerator:
    def __init__(self, rules: ModerationRules):
        self.rules = rules
    
    def moderate(self, predictions: Dict[str, float]) -> ModerationDecision:
        # 1. Find primary label
        primary_label = max(predictions, key=predictions.get)
        max_score = predictions[primary_label]
        
        # 2. Determine severity
        severity = self._calculate_severity(max_score)
        
        # 3. Determine action
        action = self.rules.get_action(severity)
        
        # 4. Generate explanation
        explanation = self._generate_explanation(...)
        
        return ModerationDecision(...)
```

**Rules Configuration**:
```python
# src/moderation/rules.py
class ModerationRules:
    SEVERITY_THRESHOLDS = {...}
    ACTION_RULES = {...}
    LABEL_DESCRIPTIONS = {...}
```

## 🗄️ Database Schema

### Table: `moderation_history`

```sql
CREATE TABLE moderation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_text TEXT NOT NULL,
    moderation_action TEXT NOT NULL CHECK(moderation_action IN ('ALLOW', 'WARNING', 'HIDE', 'BLOCK')),
    severity TEXT NOT NULL CHECK(severity IN ('NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    primary_label TEXT NOT NULL,
    confidence REAL NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),
    toxicity_scores TEXT NOT NULL,  -- JSON string
    timestamp TEXT NOT NULL,         -- ISO 8601 format
    is_toxic INTEGER NOT NULL CHECK(is_toxic IN (0, 1))
);
```

### Indexes

```sql
CREATE INDEX idx_timestamp ON moderation_history(timestamp);
CREATE INDEX idx_is_toxic ON moderation_history(is_toxic);
CREATE INDEX idx_moderation_action ON moderation_history(moderation_action);
```

### Example Record

```json
{
  "id": 1,
  "input_text": "You are an idiot!",
  "moderation_action": "HIDE",
  "severity": "HIGH",
  "primary_label": "insult",
  "confidence": 0.75,
  "toxicity_scores": "{\"toxic\": 0.89, \"insult\": 0.75, ...}",
  "timestamp": "2024-01-15T10:30:00Z",
  "is_toxic": 1
}
```

## 🌐 API Endpoints

### GET /health

**Purpose**: Health check and system status

**Response**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "moderator_loaded": true,
  "version": "1.0.0"
}
```

### POST /predict

**Purpose**: Get toxicity predictions only (no moderation decision)

**Request**:
```json
{
  "text": "Your text here"
}
```

**Response**:
```json
{
  "predictions": {
    "toxic": 0.89,
    "severe_toxic": 0.12,
    "obscene": 0.45,
    "threat": 0.08,
    "insult": 0.75,
    "identity_hate": 0.05
  },
  "is_toxic": true,
  "max_toxicity_score": 0.89,
  "primary_label": "toxic"
}
```

### POST /moderate

**Purpose**: Get complete moderation decision with action recommendation

**Request**:
```json
{
  "text": "Your text here"
}
```

**Response**:
```json
{
  "is_toxic": true,
  "action": "HIDE",
  "severity": "HIGH",
  "confidence": 0.75,
  "primary_label": "insult",
  "predictions": {
    "toxic": 0.89,
    "severe_toxic": 0.12,
    "obscene": 0.45,
    "threat": 0.08,
    "insult": 0.75,
    "identity_hate": 0.05
  },
  "explanation": "Content contains insults and toxic language. Recommended action: HIDE from public view."
}
```

### POST /batch-moderate

**Purpose**: Process multiple texts in a single request

**Request**:
```json
{
  "texts": [
    "First text",
    "Second text",
    "Third text"
  ]
}
```

**Response**:
```json
{
  "results": [
    { /* moderation result 1 */ },
    { /* moderation result 2 */ },
    { /* moderation result 3 */ }
  ]
}
```

## 🚀 Deployment Architecture

### Development Setup

```
┌─────────────┐
│  Developer  │
│   Machine   │
│             │
│  • Python   │
│  • SQLite   │
│  • Local    │
└─────────────┘
```

### Production Setup (Recommended)

```
┌──────────────────────────────────────────┐
│           Load Balancer (Nginx)          │
└────────────┬─────────────────────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
┌─────────┐      ┌─────────┐
│ FastAPI │      │ FastAPI │
│ Instance│      │ Instance│
│    1    │      │    2    │
└────┬────┘      └────┬────┘
     │                │
     └────────┬───────┘
              ▼
      ┌──────────────┐
      │  PostgreSQL  │
      │   Database   │
      └──────────────┘
```

### Containerization (Docker)

```dockerfile
# Dockerfile (example)
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Scaling Considerations

1. **Horizontal Scaling**: Multiple API instances behind load balancer
2. **Database**: Migrate from SQLite to PostgreSQL for production
3. **Caching**: Add Redis for model predictions cache
4. **Queue**: Add Celery for async batch processing
5. **Monitoring**: Add Prometheus + Grafana for metrics

## 📊 Performance Characteristics

### Latency

| Operation | Latency | Notes |
|-----------|---------|-------|
| BERT Inference | 50-100ms | Per text, GPU accelerated |
| Database Insert | <10ms | Single record |
| Database Query | <50ms | Aggregation queries |
| API Request | 100-200ms | End-to-end |

### Throughput

| Metric | Value | Notes |
|--------|-------|-------|
| Requests/sec | ~10-20 | Single instance, CPU |
| Requests/sec | ~50-100 | Single instance, GPU |
| Concurrent Users | ~50 | With proper scaling |

### Resource Usage

| Resource | Usage | Notes |
|----------|-------|-------|
| RAM | 2-4 GB | Model loaded in memory |
| CPU | 1-2 cores | Per instance |
| GPU | Optional | 4-8 GB VRAM recommended |
| Disk | ~500 MB | Model + dependencies |

## 🔐 Security Considerations

1. **Input Validation**: Pydantic models validate all inputs
2. **SQL Injection**: Parameterized queries prevent injection
3. **Rate Limiting**: Should be added for production
4. **Authentication**: Should be added for production
5. **HTTPS**: Required for production deployment
6. **CORS**: Configured in FastAPI for frontend access

## 📚 Further Reading

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/)
- [DistilBERT Paper](https://arxiv.org/abs/1910.01108)

---

**Questions?** Open an issue or check the [README.md](README.md) for more information.
