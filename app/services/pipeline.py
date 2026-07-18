from collections import Counter, defaultdict
from typing import Any

from sqlalchemy.orm import Session

from app.models import (
    PipelineRun,
    ProductOpportunity,
    Review,
    ReviewAnalysis,
    SegmentSummary,
    ThemeSummary,
)
from app.services.embeddings import upsert_review_embeddings
from app.services.labels import USER_SEGMENTS
from app.services.llm_analysis import analyze_review_text


def analyze_pending_reviews(db: Session, limit: int | None = None) -> dict[str, Any]:
    q = (
        db.query(Review)
        .filter(
            Review.is_processed.is_(True),
            Review.is_duplicate.is_(False),
            Review.is_analyzed.is_(False),
        )
        .order_by(Review.id.asc())
    )
    if limit:
        q = q.limit(limit)
    reviews = q.all()
    analyzed = 0
    for review in reviews:
        text = review.cleaned_content or review.content
        result = analyze_review_text(text, review.rating)
        existing = db.query(ReviewAnalysis).filter(ReviewAnalysis.review_id == review.review_id).first()
        if existing:
            for key, value in result.items():
                if key == "raw_json":
                    existing.raw_json = value
                elif hasattr(existing, key):
                    setattr(existing, key, value)
        else:
            db.add(
                ReviewAnalysis(
                    review_id=review.review_id,
                    sentiment=result["sentiment"],
                    main_theme=result["main_theme"],
                    pain_point=result.get("pain_point"),
                    shopping_behavior=result.get("shopping_behavior"),
                    user_motivation=result.get("user_motivation"),
                    discovery_issue=result.get("discovery_issue"),
                    product_opportunity=result.get("product_opportunity"),
                    user_segment=result["user_segment"],
                    confidence=result["confidence"],
                    raw_json=result.get("raw_json"),
                )
            )
        review.is_analyzed = True
        analyzed += 1
        if analyzed % 25 == 0:
            db.commit()
    db.add(
        PipelineRun(
            stage="analyze",
            status="completed",
            details={"analyzed": analyzed},
        )
    )
    db.commit()
    return {"analyzed": analyzed}


def embed_pending_reviews(db: Session, limit: int | None = None) -> dict[str, Any]:
    q = (
        db.query(Review, ReviewAnalysis)
        .outerjoin(ReviewAnalysis, Review.review_id == ReviewAnalysis.review_id)
        .filter(
            Review.is_processed.is_(True),
            Review.is_duplicate.is_(False),
            Review.is_embedded.is_(False),
        )
        .order_by(Review.id.asc())
    )
    if limit:
        q = q.limit(limit)
    rows = q.all()
    if not rows:
        return {"embedded": 0}

    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict[str, Any]] = []
    review_objs: list[Review] = []

    for review, analysis in rows:
        text = review.cleaned_content or review.content
        if not text.strip():
            continue
        ids.append(review.review_id)
        docs.append(text)
        metas.append(
            {
                "review_id": review.review_id,
                "rating": review.rating,
                "sentiment": analysis.sentiment if analysis else "unknown",
                "main_theme": analysis.main_theme if analysis else "Other",
                "user_segment": analysis.user_segment if analysis else "Routine Shoppers",
            }
        )
        review_objs.append(review)

    count = upsert_review_embeddings(ids, docs, metas)
    for review in review_objs:
        review.is_embedded = True
    db.add(
        PipelineRun(
            stage="embed",
            status="completed",
            details={"embedded": count},
        )
    )
    db.commit()
    return {"embedded": count}


def rebuild_theme_summaries(db: Session) -> dict[str, Any]:
    analyses = db.query(ReviewAnalysis).all()
    by_theme: dict[str, list[ReviewAnalysis]] = defaultdict(list)
    for a in analyses:
        by_theme[a.main_theme].append(a)

    db.query(ThemeSummary).delete()
    for theme, items in by_theme.items():
        # representative: highest confidence with non-empty pain
        ranked = sorted(items, key=lambda x: x.confidence, reverse=True)
        reps = []
        for item in ranked[:5]:
            review = db.query(Review).filter(Review.review_id == item.review_id).first()
            if not review:
                continue
            reps.append(
                {
                    "review_id": item.review_id,
                    "content": review.content,
                    "rating": review.rating,
                    "sentiment": item.sentiment,
                    "confidence": item.confidence,
                }
            )
        pains = [i.pain_point for i in items if i.pain_point]
        top_pain = Counter(pains).most_common(1)[0][0] if pains else "Varied feedback"
        summary = (
            f"{theme} appears in {len(items)} reviews. "
            f"Common signal: {top_pain}. "
            f"Avg confidence {sum(i.confidence for i in items) / len(items):.2f}."
        )
        db.add(
            ThemeSummary(
                theme=theme,
                frequency=len(items),
                ai_summary=summary,
                representative_reviews=reps,
            )
        )
    db.commit()
    return {"themes": len(by_theme)}


def rebuild_segment_summaries(db: Session) -> dict[str, Any]:
    analyses = db.query(ReviewAnalysis).all()
    by_seg: dict[str, list[ReviewAnalysis]] = defaultdict(list)
    for a in analyses:
        by_seg[a.user_segment].append(a)

    db.query(SegmentSummary).delete()
    for segment in USER_SEGMENTS:
        items = by_seg.get(segment, [])
        behaviors = [i.shopping_behavior for i in items if i.shopping_behavior]
        top_behaviors = [b for b, _ in Counter(behaviors).most_common(5)]
        themes = [i.main_theme for i in items]
        top_theme = Counter(themes).most_common(1)[0][0] if themes else "Other"
        insights = (
            f"{segment}: {len(items)} users. Dominant theme is {top_theme}. "
            f"Behaviors: {', '.join(top_behaviors[:3]) or 'n/a'}."
        )
        db.add(
            SegmentSummary(
                segment=segment,
                count=len(items),
                shopping_behaviors=top_behaviors,
                insights=insights,
            )
        )
    db.commit()
    return {"segments": len(USER_SEGMENTS)}


IMPACT_BY_THEME = {
    "Poor Product Discovery": "High",
    "Search Issues": "High",
    "Recommendation Quality": "High",
    "Habit Shopping": "High",
    "Product Availability": "Medium",
    "Delivery Experience": "Medium",
    "Pricing": "Medium",
    "App Experience": "Medium",
    "Customer Support": "Low",
}


def rebuild_opportunities(db: Session) -> dict[str, Any]:
    analyses = db.query(ReviewAnalysis).filter(ReviewAnalysis.product_opportunity.isnot(None)).all()
    grouped: dict[str, list[ReviewAnalysis]] = defaultdict(list)
    for a in analyses:
        key = (a.product_opportunity or "").strip()
        if not key:
            continue
        # normalize similar opportunities by theme + lowercased stem
        group_key = f"{a.main_theme}::{key.lower()[:80]}"
        grouped[group_key].append(a)

    db.query(ProductOpportunity).delete()
    ranked = sorted(grouped.items(), key=lambda kv: len(kv[1]), reverse=True)
    created = 0
    for rank, (_, items) in enumerate(ranked[:15], start=1):
        sample = items[0]
        evidence = []
        for item in items[:5]:
            review = db.query(Review).filter(Review.review_id == item.review_id).first()
            if review:
                evidence.append(
                    {
                        "review_id": item.review_id,
                        "content": review.content[:280],
                        "rating": review.rating,
                        "theme": item.main_theme,
                    }
                )
        conf = sum(i.confidence for i in items) / len(items)
        db.add(
            ProductOpportunity(
                title=sample.product_opportunity[:120] if sample.product_opportunity else "Opportunity",
                description=(
                    f"Based on {len(items)} reviews under theme '{sample.main_theme}'. "
                    f"Pain point pattern: {sample.pain_point or 'n/a'}."
                ),
                supporting_evidence=evidence,
                evidence_count=len(items),
                estimated_impact=IMPACT_BY_THEME.get(sample.main_theme, "Medium"),
                confidence=round(conf, 3),
                related_theme=sample.main_theme,
                rank=rank,
            )
        )
        created += 1
    db.commit()
    return {"opportunities": created}


def run_full_pipeline(db: Session) -> dict[str, Any]:
    from app.services.ingestion import preprocess_pending

    pre = preprocess_pending(db)
    analyzed = analyze_pending_reviews(db)
    embedded = embed_pending_reviews(db)
    themes = rebuild_theme_summaries(db)
    segments = rebuild_segment_summaries(db)
    opps = rebuild_opportunities(db)
    details = {
        "preprocess": pre,
        "analyze": analyzed,
        "embed": embedded,
        "themes": themes,
        "segments": segments,
        "opportunities": opps,
    }
    db.add(PipelineRun(stage="full_pipeline", status="completed", details=details))
    db.commit()
    return details
