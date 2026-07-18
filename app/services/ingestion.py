from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import PipelineRun, Review
from app.services.preprocessing import clean_text, content_hash
from app.services.quality import is_helpful_review, is_recent_review


class GooglePlaySource:
    """Fetch Blinkit reviews from Google Play Store with pagination."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def fetch(self, count: int | None = None) -> list[dict[str, Any]]:
        from google_play_scraper import Sort, reviews

        target = count or self.settings.review_fetch_count
        collected: dict[str, dict[str, Any]] = {}
        sorts = [Sort.NEWEST, Sort.MOST_RELEVANT, Sort.RATING]

        for sort in sorts:
            if len(collected) >= target:
                break
            token = None
            # Keep paging until we have enough unique IDs or the token ends
            while len(collected) < target:
                batch_size = min(200, target - len(collected) + 50)
                try:
                    batch, token = reviews(
                        self.settings.blinkit_app_id,
                        lang=self.settings.blinkit_app_lang,
                        country=self.settings.blinkit_app_country,
                        sort=sort,
                        count=batch_size,
                        continuation_token=token,
                    )
                except Exception:
                    break
                if not batch:
                    break
                for item in batch:
                    rid = item.get("reviewId")
                    if not rid or rid in collected:
                        continue
                    collected[rid] = {
                        "review_id": rid,
                        "user_name": item.get("userName"),
                        "content": item.get("content") or "",
                        "rating": int(item.get("score") or 0),
                        "thumbs_up": int(item.get("thumbsUpCount") or 0),
                        "review_date": item.get("at"),
                        "reply_content": (item.get("replyContent") or None),
                        "source": "google_play",
                    }
                    if len(collected) >= target:
                        break
                if not token:
                    break

        return list(collected.values())[:target]


def ingest_reviews(db: Session, count: int | None = None) -> dict[str, Any]:
    settings = get_settings()
    source = GooglePlaySource()
    fetched_items: list[dict[str, Any]] = []
    try:
        fetched_items = source.fetch(count)
    except Exception as exc:  # network / scraper failures
        run = PipelineRun(
            stage="ingestion",
            status="failed",
            details={"error": str(exc)},
        )
        db.add(run)
        db.commit()
        return {
            "fetched": 0,
            "inserted": 0,
            "skipped": 0,
            "message": f"Ingestion failed: {exc}",
        }

    existing_ids = {r[0] for r in db.query(Review.review_id).all()}
    # Only hash-dedupe non-trivial text; short/empty reviews share a hash
    existing_hashes = {
        content_hash(r[0])
        for r in db.query(Review.cleaned_content)
        .filter(Review.cleaned_content.isnot(None))
        .filter(Review.cleaned_content != "")
        .all()
        if r[0] and len(r[0]) >= 40
    }

    inserted = 0
    skipped = 0
    skipped_short = 0
    for item in fetched_items:
        rid = item["review_id"]
        cleaned = clean_text(item["content"])
        if rid in existing_ids:
            skipped += 1
            continue
        if not is_helpful_review(item["content"]):
            skipped_short += 1
            skipped += 1
            continue
        review_date = item.get("review_date")
        dt = review_date if isinstance(review_date, datetime) else None
        if not is_recent_review(dt):
            skipped += 1
            continue
        # Near-duplicate only when cleaned text is substantial
        if cleaned and len(cleaned) >= 40:
            ch = content_hash(cleaned)
            if ch in existing_hashes:
                skipped += 1
                continue
            existing_hashes.add(ch)

        db.add(
            Review(
                review_id=rid,
                user_name=item.get("user_name"),
                content=item["content"],
                cleaned_content=cleaned,
                rating=item["rating"],
                thumbs_up=item.get("thumbs_up") or 0,
                review_date=dt,
                reply_content=item.get("reply_content"),
                source=item.get("source") or "google_play",
                is_processed=True,
                is_duplicate=False,
            )
        )
        existing_ids.add(rid)
        inserted += 1

    run = PipelineRun(
        stage="ingestion",
        status="completed",
        details={
            "fetched": len(fetched_items),
            "inserted": inserted,
            "skipped": skipped,
            "skipped_short": skipped_short,
            "app_id": settings.blinkit_app_id,
        },
    )
    db.add(run)
    db.commit()
    return {
        "fetched": len(fetched_items),
        "inserted": inserted,
        "skipped": skipped,
        "message": (
            f"Ingested {inserted} meaningful reviews "
            f"({skipped} skipped: duplicates/short one-liners)."
        ),
    }


def preprocess_pending(db: Session) -> dict[str, Any]:
    pending = db.query(Review).filter(Review.is_processed.is_(False)).all()
    seen_hashes: set[str] = set()
    processed = 0
    duplicates = 0
    for review in pending:
        cleaned = clean_text(review.content)
        review.cleaned_content = cleaned
        if cleaned and len(cleaned) >= 40:
            ch = content_hash(cleaned)
            if ch in seen_hashes:
                review.is_duplicate = True
                duplicates += 1
            else:
                seen_hashes.add(ch)
                review.is_duplicate = False
        else:
            review.is_duplicate = False
        review.is_processed = True
        processed += 1
    db.add(
        PipelineRun(
            stage="preprocess",
            status="completed",
            details={"processed": processed, "duplicates_marked": duplicates},
        )
    )
    db.commit()
    return {"processed": processed, "duplicates_marked": duplicates}
