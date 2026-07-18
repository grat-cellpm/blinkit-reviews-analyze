"""Keep only meaningful reviews from 2025-2026 and refill to TARGET."""

from __future__ import annotations

from datetime import datetime

from google_play_scraper import Sort, reviews

from app.config import get_settings
from app.database import SessionLocal
from app.models import Review, ReviewAnalysis
from app.seed.filter_meaningful import TARGET, is_meaningful
from app.services.pipeline import (
    analyze_pending_reviews,
    embed_pending_reviews,
    rebuild_opportunities,
    rebuild_segment_summaries,
    rebuild_theme_summaries,
)
from app.services.preprocessing import clean_text

YEAR_MIN = 2025
YEAR_MAX = 2026


def in_year_range(dt: datetime | None) -> bool:
    if dt is None:
        return False
    return YEAR_MIN <= dt.year <= YEAR_MAX


def main() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        removed = 0
        kept = 0
        for review in db.query(Review).all():
            if in_year_range(review.review_date) and is_meaningful(review.content):
                kept += 1
                continue
            db.query(ReviewAnalysis).filter(ReviewAnalysis.review_id == review.review_id).delete()
            db.delete(review)
            removed += 1
        db.commit()
        print(f"removed={removed} kept={kept}")

        existing = {r[0] for r in db.query(Review.review_id).all()}
        collected: list[dict] = []
        pages = 0

        # NEWEST first — best chance of 2025/2026
        for sort in (Sort.NEWEST, Sort.MOST_RELEVANT):
            token = None
            stale_pages = 0
            while kept + len(collected) < TARGET and pages < 120:
                batch, token = reviews(
                    settings.blinkit_app_id,
                    lang=settings.blinkit_app_lang,
                    country=settings.blinkit_app_country,
                    sort=sort,
                    count=200,
                    continuation_token=token,
                )
                pages += 1
                added = 0
                in_range = 0
                for item in batch:
                    rid = item.get("reviewId")
                    content = item.get("content") or ""
                    at = item.get("at")
                    if not rid or rid in existing:
                        continue
                    if not isinstance(at, datetime) or not in_year_range(at):
                        continue
                    in_range += 1
                    if not is_meaningful(content):
                        continue
                    existing.add(rid)
                    collected.append(item)
                    added += 1
                    if kept + len(collected) >= TARGET:
                        break

                print(
                    f"sort={sort} page={pages} in_range={in_range} added={added} "
                    f"collected={len(collected)} total_would={kept + len(collected)}"
                )

                # If NEWEST page has almost no 2025/2026, stop that sort
                if sort == Sort.NEWEST and in_range == 0:
                    stale_pages += 1
                    if stale_pages >= 2:
                        break
                else:
                    stale_pages = 0

                if kept + len(collected) >= TARGET:
                    break
                if not token:
                    break
            if kept + len(collected) >= TARGET:
                break

        need = max(0, TARGET - kept)
        to_insert = collected[:need]
        print(f"inserting={len(to_insert)}")

        for item in to_insert:
            content = item.get("content") or ""
            at = item.get("at")
            db.add(
                Review(
                    review_id=item["reviewId"],
                    user_name=item.get("userName"),
                    content=content,
                    cleaned_content=clean_text(content),
                    rating=int(item.get("score") or 0),
                    thumbs_up=int(item.get("thumbsUpCount") or 0),
                    review_date=at if isinstance(at, datetime) else None,
                    reply_content=item.get("replyContent") or None,
                    source="google_play",
                    is_processed=True,
                    is_duplicate=False,
                    is_analyzed=False,
                    is_embedded=False,
                )
            )
        db.commit()

        print(analyze_pending_reviews(db))
        print(embed_pending_reviews(db))
        print(rebuild_theme_summaries(db))
        print(rebuild_segment_summaries(db))
        print(rebuild_opportunities(db))

        rows = db.query(Review).filter(Review.is_duplicate.is_(False)).all()
        years: dict[int, int] = {}
        for row in rows:
            y = row.review_date.year if row.review_date else 0
            years[y] = years.get(y, 0) + 1
        analyzed = sum(1 for r in rows if r.is_analyzed)
        print(f"DONE total={len(rows)} analyzed={analyzed} by_year={years}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
