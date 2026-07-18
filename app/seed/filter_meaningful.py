"""Filter out short/one-line reviews and refill with meaningful Play Store reviews."""

from __future__ import annotations

import re
from datetime import datetime

from google_play_scraper import Sort, reviews

from app.config import get_settings
from app.database import SessionLocal
from app.models import Review, ReviewAnalysis
from app.services.pipeline import (
    analyze_pending_reviews,
    embed_pending_reviews,
    rebuild_opportunities,
    rebuild_segment_summaries,
    rebuild_theme_summaries,
)
from app.services.preprocessing import clean_text

MIN_CHARS = 100
MIN_WORDS = 18
TARGET = 1000

BANNED = {
    "good",
    "bad",
    "nice",
    "ok",
    "okay",
    "super",
    "great",
    "awesome",
    "excellent",
    "poor",
    "worst",
    "best",
    "love",
    "hate",
    "average",
    "useful",
    "useless",
    "thank you",
    "thanks",
    "nice app",
    "good app",
    "bad app",
    "great app",
    "very good",
    "very bad",
    "ok app",
    "superb",
    "amazing",
    "fantastic",
    "terrible",
    "worst app",
    "best app",
    "nice one",
}


def is_meaningful(text: str) -> bool:
    cleaned = clean_text(text or "")
    if len(cleaned) < MIN_CHARS:
        return False
    words = re.findall(r"[A-Za-z']+", cleaned)
    if len(words) < MIN_WORDS:
        return False
    lower = cleaned.lower().strip().strip(".!")
    if lower in BANNED:
        return False
    if len({w.lower() for w in words}) < 10 and len(cleaned) < 140:
        return False
    return True


def main() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        all_reviews = db.query(Review).all()
        removed = 0
        kept = 0
        for review in all_reviews:
            if is_meaningful(review.content):
                kept += 1
                continue
            db.query(ReviewAnalysis).filter(ReviewAnalysis.review_id == review.review_id).delete()
            db.delete(review)
            removed += 1
        db.commit()
        print(f"removed_short={removed} kept={kept}")

        existing = {r[0] for r in db.query(Review.review_id).all()}
        collected: list[dict] = []
        pages = 0

        for sort in (Sort.MOST_RELEVANT, Sort.NEWEST, Sort.RATING):
            token = None
            while kept + len(collected) < TARGET and pages < 100:
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
                for item in batch:
                    rid = item.get("reviewId")
                    content = item.get("content") or ""
                    if not rid or rid in existing:
                        continue
                    if not is_meaningful(content):
                        continue
                    existing.add(rid)
                    collected.append(item)
                    added += 1
                    if kept + len(collected) >= TARGET:
                        break
                print(
                    f"sort={sort} page={pages} added={added} "
                    f"collected={len(collected)} total_would={kept + len(collected)}"
                )
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
            db.add(
                Review(
                    review_id=item["reviewId"],
                    user_name=item.get("userName"),
                    content=content,
                    cleaned_content=clean_text(content),
                    rating=int(item.get("score") or 0),
                    thumbs_up=int(item.get("thumbsUpCount") or 0),
                    review_date=item.get("at") if isinstance(item.get("at"), datetime) else None,
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

        total = db.query(Review).filter(Review.is_duplicate.is_(False)).count()
        analyzed = db.query(Review).filter(Review.is_analyzed.is_(True)).count()
        print(f"DONE total={total} analyzed={analyzed}")

        samples = db.query(Review).order_by(Review.id.desc()).limit(5).all()
        for sample in samples:
            preview = sample.content[:140].replace("\n", " ")
            print(f"--- {len(sample.content)} chars | {preview}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
