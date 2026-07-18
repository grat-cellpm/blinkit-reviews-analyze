"""Keep only long, insight-relevant reviews (2025-2026) useful for PM analysis."""

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

TARGET = 1000
MIN_CHARS = 180
MIN_WORDS = 30
YEAR_MIN = 2025
YEAR_MAX = 2026

# Signals that help answer habit / discovery / category / opportunity questions
INSIGHT_PATTERNS = [
    r"\bcategor",
    r"\bdiscover",
    r"\bexplor",
    r"\bsearch",
    r"\bfind\b",
    r"\brecommend",
    r"\bsuggest",
    r"\bbrowse",
    r"\bhabit",
    r"\balways\b",
    r"\busually\b",
    r"\bsame\b",
    r"\breorder",
    r"\bprevious (cart|order)",
    r"\bnew (product|categor|brand|item)",
    r"\btry(ing)?\b",
    r"\bpersonal care\b",
    r"\bgourmet\b",
    r"\bsnack",
    r"\bdairy\b",
    r"\bvegetabl",
    r"\bfruit",
    r"\bpantry\b",
    r"\bstaple",
    r"\bfilter",
    r"\bavailability|out of stock|stockout|unavailable",
    r"\bprice|expensive|mrp|discount|offer|coupon|deal",
    r"\bui\b|\bux\b|interface|app (is |was )?(slow|crash|bug|clutter)",
    r"\bnavigate|homepage|landing",
    r"\bbundle|complement",
    r"\bquality\b",
    r"\bfresh",
    r"\bbrand",
    r"\bvariety|assortment|selection",
    r"\bcompare|zepto|instamart|swiggy",
]

INSIGHT_RE = [re.compile(p, re.I) for p in INSIGHT_PATTERNS]

# Generic stubs / pure venting without product signal
LOW_VALUE = re.compile(
    r"^(very )?(good|bad|nice|worst|best|ok|okay|great|awesome|excellent|poor|love|hate).{0,40}$",
    re.I,
)


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z']+", text or ""))


def insight_score(text: str) -> int:
    return sum(1 for pattern in INSIGHT_RE if pattern.search(text or ""))


def is_helpful_review(text: str) -> bool:
    cleaned = clean_text(text or "")
    if len(cleaned) < MIN_CHARS:
        return False
    if word_count(cleaned) < MIN_WORDS:
        return False
    if LOW_VALUE.match(cleaned.strip()):
        return False
    # Must hit at least 2 insight signals so it can help product questions
    if insight_score(cleaned) < 2:
        return False
    # Avoid near-duplicate filler like repeated "delivery late" only — require substance
    unique_words = {w.lower() for w in re.findall(r"[A-Za-z']+", cleaned)}
    if len(unique_words) < 18:
        return False
    return True


def in_year_range(dt: datetime | None) -> bool:
    return bool(dt) and YEAR_MIN <= dt.year <= YEAR_MAX


def main() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        removed = 0
        kept = 0
        for review in db.query(Review).all():
            if in_year_range(review.review_date) and is_helpful_review(review.content):
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

        for sort in (Sort.MOST_RELEVANT, Sort.NEWEST):
            token = None
            while kept + len(collected) < TARGET and pages < 150:
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
                    at = item.get("at")
                    if not rid or rid in existing:
                        continue
                    if not isinstance(at, datetime) or not in_year_range(at):
                        continue
                    if not is_helpful_review(content):
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
                    review_date=item.get("at"),
                    reply_content=item.get("replyContent") or None,
                    source="google_play",
                    is_processed=True,
                    is_duplicate=False,
                )
            )
        db.commit()

        print(analyze_pending_reviews(db))
        print(embed_pending_reviews(db))
        print(rebuild_theme_summaries(db))
        print(rebuild_segment_summaries(db))
        print(rebuild_opportunities(db))

        rows = db.query(Review).all()
        lens = sorted(len(r.content or "") for r in rows)
        years: dict[int, int] = {}
        for r in rows:
            y = r.review_date.year if r.review_date else 0
            years[y] = years.get(y, 0) + 1
        print(f"DONE total={len(rows)} analyzed={sum(1 for r in rows if r.is_analyzed)}")
        print(f"by_year={years}")
        if lens:
            print(
                f"chars min={lens[0]} median={lens[len(lens)//2]} "
                f"avg={sum(lens)/len(lens):.0f} max={lens[-1]}"
            )
        print("--- samples ---")
        for r in sorted(rows, key=lambda x: len(x.content or ""), reverse=True)[:3]:
            preview = (r.content or "")[:200].replace("\n", " ")
            print(f"{len(r.content)} | {preview}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
