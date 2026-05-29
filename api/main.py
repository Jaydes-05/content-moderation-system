"""
FastAPI Backend for Content Moderation System

This module provides REST API endpoints for toxicity detection
and content moderation using DistilBERT and the moderation engine.

Usage:
    uvicorn api.main:app --reload
    uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.schemas import (
    TextRequest,
    BatchTextRequest,
    HealthResponse,
    PredictionResponse,
    ModerationResponse,
    BatchModerationResponse,
    ErrorResponse
)
from api.services import model_service
from api.database import init_database, insert_moderation_record

# ── Configure logging ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ── Application Lifecycle ───────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Startup: Load ML models once
    - Shutdown: Cleanup resources
    """
    # Startup
    logger.info("="*70)
    logger.info("CONTENT MODERATION API - STARTING UP")
    logger.info("="*70)
    
    # Initialize database
    logger.info("Initializing database...")
    try:
        init_database()
        logger.info("✓ Database initialized")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        logger.warning("Continuing startup - API will function without analytics")
    
    try:
        # Load models once during startup
        model_service.load_models()
        logger.info("✓ Models loaded successfully")
        logger.info("✓ API ready to accept requests")
    except FileNotFoundError as e:
        logger.warning(f"⚠ Model files not found: {e}")
        logger.warning("Running in DEMO MODE with mock predictions")
        logger.warning("To use real ML models, train them first:")
        logger.warning("  python train_bert_10k.py")
        # Continue without models - use demo mode
    except Exception as e:
        logger.warning(f"⚠ Failed to load models: {e}")
        logger.warning("Running in DEMO MODE with mock predictions")
    
    logger.info("="*70)
    
    yield
    
    # Shutdown
    logger.info("Shutting down API...")
    logger.info("✓ Cleanup complete")


# ── FastAPI Application ─────────────────────────────────────────────────────

app = FastAPI(
    title="Content Moderation API",
    description="""
    Production-ready REST API for AI-based content moderation.
    
    ## Features
    - **Toxicity Detection**: Detect toxic, insulting, threatening, and hateful content
    - **Moderation Decisions**: Get actionable moderation recommendations
    - **Batch Processing**: Process multiple texts efficiently
    - **Configurable Rules**: Choose from multiple moderation presets
    
    ## Models
    - **BERT Model**: DistilBERT fine-tuned on Jigsaw Toxic Comment dataset
    - **Moderation Engine**: Rule-based decision engine with configurable thresholds
    
    ## Use Cases
    - Social media comment moderation
    - Forum post filtering
    - Chat message screening
    - User-generated content review
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception Handlers ──────────────────────────────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": exc.detail,
            "detail": None
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors."""
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": str(exc),
            "detail": None
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "detail": str(exc) if logger.level == logging.DEBUG else None
        }
    )


# ═══════════════════════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@app.get(
    "/",
    summary="Root endpoint",
    description="Returns API information and available endpoints"
)
async def root() -> Dict:
    """
    Root endpoint with API information.
    
    Returns
    -------
    dict
        API information and available endpoints
    """
    return {
        "name": "Content Moderation API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "moderate": "/moderate",
            "batch_moderate": "/batch-moderate",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the API and models are loaded and ready",
    tags=["Health"]
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns service status and model loading state.
    
    Returns
    -------
    HealthResponse
        Health status information
    """
    is_loaded = model_service.is_loaded()
    
    return HealthResponse(
        status="healthy" if is_loaded else "unhealthy",
        model_loaded=is_loaded,
        moderator_loaded=is_loaded,
        version="1.0.0"
    )


@app.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict toxicity",
    description="Get toxicity predictions for a single text",
    tags=["Prediction"],
    responses={
        200: {
            "description": "Successful prediction",
            "content": {
                "application/json": {
                    "example": {
                        "text": "You are an idiot!",
                        "is_toxic": True,
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
                }
            }
        },
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"}
    }
)
async def predict(request: TextRequest) -> PredictionResponse:
    """
    Get toxicity predictions for text.
    
    This endpoint returns raw model predictions without moderation decisions.
    Use this when you only need toxicity scores.
    
    Parameters
    ----------
    request : TextRequest
        Request containing text to analyze
    
    Returns
    -------
    PredictionResponse
        Toxicity predictions
    
    Raises
    ------
    HTTPException
        If prediction fails
    """
    try:
        logger.info(f"Prediction request: {request.text[:50]}...")
        
        result = model_service.predict(request.text)
        
        logger.info(f"Prediction complete: is_toxic={result['is_toxic']}, max_score={result['max_score']:.4f}")
        
        return PredictionResponse(**result)
    
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@app.post(
    "/moderate",
    response_model=ModerationResponse,
    summary="Moderate content",
    description="Get toxicity predictions and moderation decision for a single text",
    tags=["Moderation"],
    responses={
        200: {
            "description": "Successful moderation",
            "content": {
                "application/json": {
                    "example": {
                        "text": "You are an idiot!",
                        "is_toxic": True,
                        "predictions": {
                            "toxic": 0.94,
                            "insult": 0.88
                        },
                        "action": "BLOCK",
                        "severity": "HIGH",
                        "primary_label": "toxic",
                        "confidence": 0.94,
                        "explanation": "Content contains severe toxicity and should be blocked."
                    }
                }
            }
        },
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"}
    }
)
async def moderate(request: TextRequest) -> ModerationResponse:
    """
    Get moderation decision for text.
    
    This endpoint returns both toxicity predictions and actionable
    moderation recommendations (ALLOW, WARNING, HIDE, BLOCK).
    
    Parameters
    ----------
    request : TextRequest
        Request containing text to analyze
    
    Returns
    -------
    ModerationResponse
        Moderation decision with predictions
    
    Raises
    ------
    HTTPException
        If moderation fails
    """
    try:
        logger.info(f"Moderation request: {request.text[:50]}...")
        
        result = model_service.moderate(request.text)
        
        logger.info(
            f"Moderation complete: action={result['action']}, "
            f"severity={result['severity']}, confidence={result['confidence']:.4f}"
        )
        
        # Save to database (non-blocking, errors logged but not raised)
        try:
            import json
            from datetime import datetime
            
            insert_moderation_record(
                input_text=request.text,
                moderation_action=result['action'],
                severity=result['severity'],
                primary_label=result['primary_label'],
                confidence=result['confidence'],
                toxicity_scores=json.dumps(result['predictions']),
                timestamp=datetime.utcnow().isoformat() + 'Z',
                is_toxic=result['is_toxic']
            )
            logger.debug("Moderation record saved to database")
        except Exception as db_error:
            logger.error(f"Failed to save moderation record: {db_error}")
            # Continue - don't fail the API request due to DB errors
        
        return ModerationResponse(**result)
    
    except Exception as e:
        logger.error(f"Moderation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Moderation failed: {str(e)}"
        )


@app.post(
    "/batch-moderate",
    response_model=BatchModerationResponse,
    summary="Batch moderate content",
    description="Get moderation decisions for multiple texts (max 100)",
    tags=["Moderation"],
    responses={
        200: {
            "description": "Successful batch moderation",
            "content": {
                "application/json": {
                    "example": {
                        "total": 2,
                        "results": [
                            {
                                "text": "Great post!",
                                "is_toxic": False,
                                "predictions": {"toxic": 0.05},
                                "action": "ALLOW",
                                "severity": "NONE",
                                "primary_label": "none",
                                "confidence": 0.05,
                                "explanation": "Content is safe."
                            },
                            {
                                "text": "You are stupid!",
                                "is_toxic": True,
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
                }
            }
        },
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"}
    }
)
async def batch_moderate(request: BatchTextRequest) -> BatchModerationResponse:
    """
    Get moderation decisions for multiple texts.
    
    This endpoint processes multiple texts efficiently and returns
    individual results plus aggregated statistics.
    
    Parameters
    ----------
    request : BatchTextRequest
        Request containing list of texts to analyze (max 100)
    
    Returns
    -------
    BatchModerationResponse
        Batch moderation results with statistics
    
    Raises
    ------
    HTTPException
        If batch moderation fails
    """
    try:
        logger.info(f"Batch moderation request: {len(request.texts)} texts")
        
        result = model_service.moderate_batch(request.texts)
        
        logger.info(
            f"Batch moderation complete: {result['total']} texts, "
            f"{result['statistics']['toxic_count']} toxic, "
            f"{result['statistics']['safe_count']} safe"
        )
        
        return BatchModerationResponse(**result)
    
    except Exception as e:
        logger.error(f"Batch moderation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch moderation failed: {str(e)}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Browser Extension Endpoints
# ═══════════════════════════════════════════════════════════════════════════

import httpx
from pydantic import BaseModel as PydanticBaseModel
from typing import Optional


class TranslateRequest(PydanticBaseModel):
    """Request schema for translation."""
    text: str
    target_language: str = "es"  # ISO 639-1 language code


class TranslateResponse(PydanticBaseModel):
    """Response schema for translation."""
    original: str
    translated: str
    target_language: str
    ok: bool


@app.post(
    "/translate",
    response_model=TranslateResponse,
    summary="Translate text",
    description="Translate text to a target language using the MyMemory free translation API",
    tags=["Extension"],
)
async def translate_text(request: TranslateRequest) -> TranslateResponse:
    """
    Translate text to the specified target language.

    Uses the MyMemory free translation API (no API key required).
    Supports ISO 639-1 language codes (e.g. 'es', 'fr', 'hi', 'de', 'zh').

    Parameters
    ----------
    request : TranslateRequest
        Text and target language code

    Returns
    -------
    TranslateResponse
        Original and translated text
    """
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text cannot be empty"
        )

    text = request.text.strip()[:500]  # MyMemory limit

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "q": text,
                "langpair": f"en|{request.target_language}"
            }
            resp = await client.get(
                "https://api.mymemory.translated.net/get",
                params=params
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("responseStatus") == 200:
            translated = data["responseData"]["translatedText"]
            return TranslateResponse(
                original=text,
                translated=translated,
                target_language=request.target_language,
                ok=True
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Translation API error: {data.get('responseDetails', 'unknown')}"
            )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Translation API timed out"
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Translation API returned {e.response.status_code}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )


@app.get(
    "/extension-stats",
    summary="Extension analytics",
    description="Get aggregated moderation statistics for the browser extension dashboard",
    tags=["Extension"],
)
async def extension_stats() -> Dict:
    """
    Return aggregated moderation statistics from the database.

    Returns
    -------
    dict
        Aggregated stats: total moderated, toxic count, action breakdown
    """
    try:
        from api.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM moderation_records")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM moderation_records WHERE is_toxic = 1")
        toxic = cursor.fetchone()[0]

        cursor.execute("""
            SELECT moderation_action, COUNT(*) as cnt
            FROM moderation_records
            GROUP BY moderation_action
        """)
        actions = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return {
            "total_moderated": total,
            "toxic_count": toxic,
            "safe_count": total - toxic,
            "toxic_percent": round((toxic / total * 100) if total else 0, 1),
            "actions": actions
        }
    except Exception as e:
        logger.warning(f"Could not fetch extension stats: {e}")
        return {"total_moderated": 0, "toxic_count": 0, "safe_count": 0, "actions": {}}


# ═══════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
