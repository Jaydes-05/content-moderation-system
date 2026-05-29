"""
FastAPI example for toxicity detection API.

This is a minimal example showing how to integrate the ToxicityPredictor
with FastAPI for production deployment.

Installation:
    pip install fastapi uvicorn

Usage:
    uvicorn src.inference.api_example:app --reload
    
    # Or directly:
    python src/inference/api_example.py

API Endpoints:
    POST /predict          - Single text prediction
    POST /predict/batch    - Batch text prediction
    GET  /health          - Health check
    GET  /                - API documentation
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from inference.predict import ToxicityPredictor

# ═══════════════════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════════════════

class PredictionRequest(BaseModel):
    """Request model for single prediction."""
    text: str = Field(..., description="Text to analyze for toxicity")
    threshold: Optional[float] = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Classification threshold (0.0 to 1.0)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "You are an idiot!",
                "threshold": 0.5
            }
        }


class BatchPredictionRequest(BaseModel):
    """Request model for batch prediction."""
    texts: List[str] = Field(..., description="List of texts to analyze")
    threshold: Optional[float] = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Classification threshold (0.0 to 1.0)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "texts": [
                    "This is great!",
                    "You are stupid!",
                    "I disagree with you."
                ],
                "threshold": 0.5
            }
        }


class LabelPredictionResponse(BaseModel):
    """Response model for individual label prediction."""
    label: str
    predicted: bool
    probability: float


class PredictionResponse(BaseModel):
    """Response model for single prediction."""
    text: str
    is_toxic: bool
    toxic_labels: List[str]
    max_toxicity_score: float
    predictions: List[LabelPredictionResponse]


class BatchPredictionResponse(BaseModel):
    """Response model for batch prediction."""
    results: List[PredictionResponse]
    summary: dict


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    model_loaded: bool
    version: str


# ═══════════════════════════════════════════════════════════════════════════
# FastAPI Application
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Toxicity Detection API",
    description="AI-powered content moderation API using TF-IDF + Logistic Regression",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global predictor instance (loaded once at startup)
predictor: Optional[ToxicityPredictor] = None


@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    global predictor
    try:
        predictor = ToxicityPredictor(model_dir='models/baseline')
        print("✓ Model loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        raise


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API information."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Toxicity Detection API</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                border-bottom: 3px solid #4CAF50;
                padding-bottom: 10px;
            }
            .endpoint {
                background-color: #f9f9f9;
                padding: 15px;
                margin: 10px 0;
                border-left: 4px solid #4CAF50;
                border-radius: 4px;
            }
            .method {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                margin-right: 10px;
            }
            .post { background-color: #49cc90; color: white; }
            .get { background-color: #61affe; color: white; }
            code {
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: monospace;
            }
            a {
                color: #4CAF50;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛡️ Toxicity Detection API</h1>
            <p>AI-powered content moderation using TF-IDF + Logistic Regression</p>
            
            <h2>Available Endpoints</h2>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/predict</code>
                <p>Analyze a single text for toxicity</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/predict/batch</code>
                <p>Analyze multiple texts in batch</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/health</code>
                <p>Check API health status</p>
            </div>
            
            <h2>Documentation</h2>
            <p>
                📖 <a href="/docs">Interactive API Documentation (Swagger UI)</a><br>
                📖 <a href="/redoc">Alternative Documentation (ReDoc)</a>
            </p>
            
            <h2>Quick Example</h2>
            <pre><code>curl -X POST "http://localhost:8000/predict" \\
  -H "Content-Type: application/json" \\
  -d '{"text": "You are an idiot!"}'</code></pre>
            
            <h2>Model Information</h2>
            <ul>
                <li><strong>Architecture:</strong> TF-IDF + Logistic Regression</li>
                <li><strong>Labels:</strong> toxic, severe_toxic, obscene, threat, insult, identity_hate</li>
                <li><strong>Test F1 (macro):</strong> 0.53</li>
                <li><strong>Test Accuracy:</strong> 86.15%</li>
            </ul>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy" if predictor is not None else "unhealthy",
        "model_loaded": predictor is not None,
        "version": "1.0.0"
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Predict toxicity for a single text.
    
    Returns toxicity labels and probability scores for the input text.
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        # Update threshold if provided
        if request.threshold != 0.5:
            predictor.set_threshold(request.threshold)
        
        # Make prediction
        result = predictor.predict(request.text, return_dict=True)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchPredictionRequest):
    """
    Predict toxicity for multiple texts.
    
    Returns toxicity labels and probability scores for each input text,
    along with a summary of results.
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if not request.texts:
        raise HTTPException(status_code=400, detail="Texts list cannot be empty")
    
    if len(request.texts) > 100:
        raise HTTPException(
            status_code=400,
            detail="Batch size too large (max 100 texts)"
        )
    
    try:
        # Update threshold if provided
        if request.threshold != 0.5:
            predictor.set_threshold(request.threshold)
        
        # Make predictions
        results = predictor.predict_batch(request.texts, return_dict=True)
        
        # Calculate summary
        toxic_count = sum(1 for r in results if r['is_toxic'])
        clean_count = len(results) - toxic_count
        
        summary = {
            "total": len(results),
            "toxic": toxic_count,
            "clean": clean_count,
            "toxic_percentage": round(toxic_count / len(results) * 100, 2)
        }
        
        return {
            "results": results,
            "summary": summary
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# Run Server
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("TOXICITY DETECTION API")
    print("=" * 70)
    print("\nStarting server...")
    print("API Documentation: http://localhost:8000/docs")
    print("Alternative Docs:  http://localhost:8000/redoc")
    print("Health Check:      http://localhost:8000/health")
    print("\nPress CTRL+C to stop")
    print("=" * 70)
    
    uvicorn.run(
        "api_example:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
