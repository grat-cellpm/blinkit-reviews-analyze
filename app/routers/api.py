from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ProductOpportunity, SegmentSummary, ThemeSummary
from app.schemas import (
    ChatRequest,
    ChatResponse,
    DashboardMetrics,
    IngestionResult,
    OpportunityOut,
    PipelineStatus,
    ReviewListResponse,
    SegmentOut,
    ThemeOut,
)
from app.services.ingestion import ingest_reviews, preprocess_pending
from app.services.metrics import get_dashboard_metrics, list_reviews
from app.services.pipeline import (
    analyze_pending_reviews,
    embed_pending_reviews,
    rebuild_opportunities,
    rebuild_segment_summaries,
    rebuild_theme_summaries,
    run_full_pipeline,
)
from app.services.rag import answer_question

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "blinkit-feedback-intelligence"}


@router.post("/ingestion/fetch", response_model=IngestionResult)
def fetch_reviews(
    count: int | None = Query(default=None, ge=10, le=5000),
    db: Session = Depends(get_db),
) -> IngestionResult:
    result = ingest_reviews(db, count=count)
    return IngestionResult(**result)


@router.post("/pipeline/preprocess", response_model=PipelineStatus)
def pipeline_preprocess(db: Session = Depends(get_db)) -> PipelineStatus:
    details = preprocess_pending(db)
    return PipelineStatus(stage="preprocess", status="completed", details=details)


@router.post("/pipeline/analyze", response_model=PipelineStatus)
def pipeline_analyze(
    limit: int | None = Query(default=None, ge=1, le=500),
    db: Session = Depends(get_db),
) -> PipelineStatus:
    details = analyze_pending_reviews(db, limit=limit)
    rebuild_theme_summaries(db)
    rebuild_segment_summaries(db)
    rebuild_opportunities(db)
    return PipelineStatus(stage="analyze", status="completed", details=details)


@router.post("/pipeline/embed", response_model=PipelineStatus)
def pipeline_embed(
    limit: int | None = Query(default=None, ge=1, le=500),
    db: Session = Depends(get_db),
) -> PipelineStatus:
    details = embed_pending_reviews(db, limit=limit)
    return PipelineStatus(stage="embed", status="completed", details=details)


@router.post("/pipeline/run", response_model=PipelineStatus)
def pipeline_run(db: Session = Depends(get_db)) -> PipelineStatus:
    details = run_full_pipeline(db)
    return PipelineStatus(stage="full_pipeline", status="completed", details=details)


@router.get("/dashboard/metrics", response_model=DashboardMetrics)
def dashboard_metrics(db: Session = Depends(get_db)) -> DashboardMetrics:
    return DashboardMetrics(**get_dashboard_metrics(db))


@router.get("/themes", response_model=list[ThemeOut])
def get_themes(db: Session = Depends(get_db)) -> list[ThemeOut]:
    rows = db.query(ThemeSummary).order_by(ThemeSummary.frequency.desc()).all()
    return [
        ThemeOut(
            theme=r.theme,
            frequency=r.frequency,
            ai_summary=r.ai_summary,
            representative_reviews=r.representative_reviews or [],
        )
        for r in rows
    ]


@router.get("/segments", response_model=list[SegmentOut])
def get_segments(db: Session = Depends(get_db)) -> list[SegmentOut]:
    rows = db.query(SegmentSummary).order_by(SegmentSummary.count.desc()).all()
    return [
        SegmentOut(
            segment=r.segment,
            count=r.count,
            shopping_behaviors=r.shopping_behaviors or [],
            insights=r.insights,
        )
        for r in rows
    ]


@router.get("/reviews", response_model=ReviewListResponse)
def get_reviews(
    q: str | None = None,
    rating: int | None = Query(default=None, ge=1, le=5),
    sentiment: str | None = None,
    theme: str | None = None,
    segment: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ReviewListResponse:
    result = list_reviews(
        db,
        q=q,
        rating=rating,
        sentiment=sentiment,
        theme=theme,
        segment=segment,
        limit=limit,
        offset=offset,
    )
    return ReviewListResponse(total=result["total"], items=result["items"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    result = answer_question(db, payload.question)
    return ChatResponse(**result)


@router.get("/opportunities", response_model=list[OpportunityOut])
def get_opportunities(db: Session = Depends(get_db)) -> list[OpportunityOut]:
    rows = db.query(ProductOpportunity).order_by(ProductOpportunity.rank.asc()).all()
    return [
        OpportunityOut(
            id=r.id,
            title=r.title,
            description=r.description,
            supporting_evidence=r.supporting_evidence or [],
            evidence_count=r.evidence_count,
            estimated_impact=r.estimated_impact,
            confidence=r.confidence,
            related_theme=r.related_theme,
            rank=r.rank,
        )
        for r in rows
    ]
