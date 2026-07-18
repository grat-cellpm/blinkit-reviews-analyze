from collections import Counter
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Review, ReviewAnalysis
from app.schemas import ReviewOut


def get_dashboard_metrics(db: Session) -> dict[str, Any]:
    total = db.query(func.count(Review.id)).filter(Review.is_duplicate.is_(False)).scalar() or 0
    analyzed = db.query(func.count(Review.id)).filter(Review.is_analyzed.is_(True)).scalar() or 0
    avg_rating = db.query(func.avg(Review.rating)).filter(Review.is_duplicate.is_(False)).scalar() or 0.0

    sentiments = dict(
        db.query(ReviewAnalysis.sentiment, func.count(ReviewAnalysis.id))
        .group_by(ReviewAnalysis.sentiment)
        .all()
    )
    themes = dict(
        db.query(ReviewAnalysis.main_theme, func.count(ReviewAnalysis.id))
        .group_by(ReviewAnalysis.main_theme)
        .all()
    )
    segments = dict(
        db.query(ReviewAnalysis.user_segment, func.count(ReviewAnalysis.id))
        .group_by(ReviewAnalysis.user_segment)
        .all()
    )
    ratings = dict(
        db.query(Review.rating, func.count(Review.id))
        .filter(Review.is_duplicate.is_(False))
        .group_by(Review.rating)
        .all()
    )
    return {
        "total_reviews": total,
        "analyzed_reviews": analyzed,
        "average_rating": round(float(avg_rating), 2),
        "sentiment_distribution": {str(k): int(v) for k, v in sentiments.items()},
        "theme_distribution": {str(k): int(v) for k, v in themes.items()},
        "segment_distribution": {str(k): int(v) for k, v in segments.items()},
        "rating_distribution": {str(k): int(v) for k, v in ratings.items()},
    }


def list_reviews(
    db: Session,
    *,
    q: Optional[str] = None,
    rating: Optional[int] = None,
    sentiment: Optional[str] = None,
    theme: Optional[str] = None,
    segment: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    query = (
        db.query(Review, ReviewAnalysis)
        .outerjoin(ReviewAnalysis, Review.review_id == ReviewAnalysis.review_id)
        .filter(Review.is_duplicate.is_(False))
    )
    if q:
        like = f"%{q}%"
        query = query.filter(Review.content.ilike(like))
    if rating is not None:
        query = query.filter(Review.rating == rating)
    if sentiment:
        query = query.filter(ReviewAnalysis.sentiment == sentiment.lower())
    if theme:
        query = query.filter(ReviewAnalysis.main_theme == theme)
    if segment:
        query = query.filter(ReviewAnalysis.user_segment == segment)
    if date_from:
        query = query.filter(Review.review_date >= date_from)
    if date_to:
        query = query.filter(Review.review_date <= date_to)

    total = query.count()
    rows = query.order_by(Review.review_date.desc(), Review.id.desc()).offset(offset).limit(limit).all()
    items: list[ReviewOut] = []
    for review, analysis in rows:
        items.append(
            ReviewOut(
                id=review.id,
                review_id=review.review_id,
                user_name=review.user_name,
                content=review.content,
                cleaned_content=review.cleaned_content,
                rating=review.rating,
                thumbs_up=review.thumbs_up,
                review_date=review.review_date,
                source=review.source,
                is_analyzed=review.is_analyzed,
                sentiment=analysis.sentiment if analysis else None,
                main_theme=analysis.main_theme if analysis else None,
                user_segment=analysis.user_segment if analysis else None,
                pain_point=analysis.pain_point if analysis else None,
                confidence=analysis.confidence if analysis else None,
            )
        )
    return {"total": total, "items": items}
