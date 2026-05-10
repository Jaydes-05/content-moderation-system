"""
Pydantic schemas for request/response validation.

This module defines all data models used in the API for
request validation and response serialization.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator


# ═══════════════════════════════════════════════════════════════════════════
# Request Schemas
# ═══════════════════════════════════════════════════════════════════════════

class TextRequest(BaseModel):
    """
    Request model for single text prediction/moderation.
    
    Attributes
    ----------
    text : str
        The text content to analyze (1-10000 characters)
    """
    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Text content to analyze",
        example="You are an idiot!"
    )
    
    @validator('text')
    def text_not_empty(cls, v):
        """Validate text is not just whitespace."""
        if not v.strip():
            raise ValueError('Text cannot be empty or only whitespace')
        return v.strip()


class BatchTextRequest(BaseModel):
    """
    Request model for batch text prediction/moderation.
    
    Attributes
    ----------
    texts : List[str]
        List of text contents to analyze (max 100 items)
    """
    texts: List[str] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of text contents to analyze",
        example=["Great post!", "You are stupid!"]
    )
    
    @validator('texts')
    def validate_texts(cls, v):
        """Validate all texts are non-empty."""
        cleaned = []
        for text in v:
            if not text or not text.strip():
                raise ValueError('All texts must be non-empty')
            if len(text) > 10000:
                raise ValueError('Each text must be less than 10000 characters')
            cleaned.append(text.strip())
        return cleaned


class ModerationConfigRequest(BaseModel):
    """
    Optional configuration for moderation rules.
    
    Attributes
    ----------
    preset : str
        Moderation preset: strict, moderate, lenient, zero_tolerance
    """
    preset: Optional[str] = Field(
        "moderate",
        description="Moderation preset",
        example="moderate"
    )
    
    @validator('preset')
    def validate_preset(cls, v):
        """Validate preset is valid."""
        valid_presets = ['strict', 'moderate', 'lenient', 'zero_tolerance']
        if v not in valid_presets:
            raise ValueError(f'Preset must be one of: {", ".join(valid_presets)}')
        return v


# ═══════════════════════════════════════════════════════════════════════════
# Response Schemas
# ═══════════════════════════════════════════════════════════════════════════

class HealthResponse(BaseModel):
    """
    Health check response.
    
    Attributes
    ----------
    status : str
        Service status (healthy/unhealthy)
    model_loaded : bool
        Whether BERT model is loaded
    moderator_loaded : bool
        Whether moderation engine is loaded
    version : str
        API version
    """
    model_config = {"protected_namespaces": ()}  # Allow 'model_' prefix
    
    status: str = Field(..., description="Service status", example="healthy")
    model_loaded: bool = Field(..., description="BERT model loaded", example=True)
    moderator_loaded: bool = Field(..., description="Moderator loaded", example=True)
    version: str = Field(..., description="API version", example="1.0.0")


class PredictionResponse(BaseModel):
    """
    Response model for toxicity prediction.
    
    Attributes
    ----------
    text : str
        Original input text
    is_toxic : bool
        Whether toxicity was detected
    predictions : Dict[str, float]
        Probability scores for each label
    toxic_labels : List[str]
        Labels that exceeded threshold
    max_score : float
        Highest probability score
    confidence : float
        Overall confidence score
    """
    text: str = Field(..., description="Original input text")
    is_toxic: bool = Field(..., description="Toxicity detected", example=True)
    predictions: Dict[str, float] = Field(
        ...,
        description="Probability scores for each label",
        example={
            "toxic": 0.94,
            "severe_toxic": 0.45,
            "obscene": 0.67,
            "threat": 0.12,
            "insult": 0.88,
            "identity_hate": 0.23
        }
    )
    toxic_labels: List[str] = Field(
        ...,
        description="Labels above threshold",
        example=["toxic", "insult"]
    )
    max_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Highest probability",
        example=0.94
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence",
        example=0.94
    )


class ModerationResponse(BaseModel):
    """
    Response model for content moderation.
    
    Attributes
    ----------
    text : str
        Original input text
    is_toxic : bool
        Whether toxicity was detected
    predictions : Dict[str, float]
        Probability scores for each label
    action : str
        Recommended moderation action
    severity : str
        Severity level
    primary_label : str
        Primary toxic category
    confidence : float
        Confidence score
    explanation : str
        Human-readable explanation
    """
    text: str = Field(..., description="Original input text")
    is_toxic: bool = Field(..., description="Toxicity detected", example=True)
    predictions: Dict[str, float] = Field(
        ...,
        description="Probability scores",
        example={"toxic": 0.94, "insult": 0.88}
    )
    action: str = Field(
        ...,
        description="Moderation action",
        example="BLOCK"
    )
    severity: str = Field(
        ...,
        description="Severity level",
        example="HIGH"
    )
    primary_label: str = Field(
        ...,
        description="Primary toxic category",
        example="toxic"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score",
        example=0.94
    )
    explanation: str = Field(
        ...,
        description="Human-readable explanation",
        example="Content contains severe toxicity and should be blocked."
    )


class BatchModerationResponse(BaseModel):
    """
    Response model for batch moderation.
    
    Attributes
    ----------
    total : int
        Total number of items processed
    results : List[ModerationResponse]
        List of moderation results
    statistics : Dict
        Aggregated statistics
    """
    total: int = Field(..., description="Total items processed", example=2)
    results: List[ModerationResponse] = Field(
        ...,
        description="List of moderation results"
    )
    statistics: Dict = Field(
        ...,
        description="Aggregated statistics",
        example={
            "toxic_count": 1,
            "safe_count": 1,
            "actions": {
                "ALLOW": 1,
                "BLOCK": 1
            }
        }
    )


class ErrorResponse(BaseModel):
    """
    Error response model.
    
    Attributes
    ----------
    error : str
        Error type
    message : str
        Error message
    detail : str
        Detailed error information
    """
    error: str = Field(..., description="Error type", example="ValidationError")
    message: str = Field(..., description="Error message", example="Invalid input")
    detail: Optional[str] = Field(None, description="Detailed error info")
