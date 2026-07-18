from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    user_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    cleaned_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rating: Mapped[int] = mapped_column(Integer, index=True)
    thumbs_up: Mapped[int] = mapped_column(Integer, default=0)
    review_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    reply_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="google_play")
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_analyzed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_embedded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReviewAnalysis(Base):
    __tablename__ = "review_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    sentiment: Mapped[str] = mapped_column(String(32), index=True)
    main_theme: Mapped[str] = mapped_column(String(128), index=True)
    pain_point: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shopping_behavior: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    user_motivation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    discovery_issue: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    product_opportunity: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_segment: Mapped[str] = mapped_column(String(64), index=True, default="Routine Shoppers")
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    raw_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ThemeSummary(Base):
    __tablename__ = "theme_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    theme: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    frequency: Mapped[int] = mapped_column(Integer, default=0)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    representative_reviews: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SegmentSummary(Base):
    __tablename__ = "segment_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    segment: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    shopping_behaviors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    insights: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProductOpportunity(Base):
    __tablename__ = "product_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text)
    supporting_evidence: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    estimated_impact: Mapped[str] = mapped_column(String(64), default="Medium")
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    related_theme: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    rank: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stage: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="started")
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
