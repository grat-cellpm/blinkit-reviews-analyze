from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ReviewOut(BaseModel):
    id: int
    review_id: str
    user_name: Optional[str] = None
    content: str
    cleaned_content: Optional[str] = None
    rating: int
    thumbs_up: int = 0
    review_date: Optional[datetime] = None
    source: str = "google_play"
    is_analyzed: bool = False
    sentiment: Optional[str] = None
    main_theme: Optional[str] = None
    user_segment: Optional[str] = None
    pain_point: Optional[str] = None
    confidence: Optional[float] = None

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    total: int
    items: list[ReviewOut]


class DashboardMetrics(BaseModel):
    total_reviews: int
    analyzed_reviews: int
    average_rating: float
    sentiment_distribution: dict[str, int]
    theme_distribution: dict[str, int]
    segment_distribution: dict[str, int]
    rating_distribution: dict[str, int]


class ThemeOut(BaseModel):
    theme: str
    frequency: int
    ai_summary: Optional[str] = None
    representative_reviews: list[dict[str, Any]] = Field(default_factory=list)


class SegmentOut(BaseModel):
    segment: str
    count: int
    shopping_behaviors: list[str] = Field(default_factory=list)
    insights: Optional[str] = None


class OpportunityOut(BaseModel):
    id: int
    title: str
    description: str
    supporting_evidence: list[dict[str, Any]] = Field(default_factory=list)
    evidence_count: int
    estimated_impact: str
    confidence: float
    related_theme: Optional[str] = None
    rank: int


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)


class EvidenceReview(BaseModel):
    review_id: str
    content: str
    rating: int
    sentiment: Optional[str] = None
    main_theme: Optional[str] = None
    relevance_score: Optional[float] = None


class ChatResponse(BaseModel):
    question: str
    explanation: str
    supporting_reviews: list[EvidenceReview]
    matching_reviews: int
    confidence: float
    related_themes: list[str] = Field(default_factory=list)


class PipelineStatus(BaseModel):
    stage: str
    status: str
    details: dict[str, Any] = Field(default_factory=dict)


class IngestionResult(BaseModel):
    fetched: int
    inserted: int
    skipped: int
    message: str
