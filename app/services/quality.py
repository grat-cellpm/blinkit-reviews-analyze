"""Shared quality gates for review ingestion."""

from __future__ import annotations

import re
from datetime import datetime

from app.services.preprocessing import clean_text

MIN_HELPFUL_CHARS = 180
MIN_HELPFUL_WORDS = 30
YEAR_MIN = 2025
YEAR_MAX = 2026

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
LOW_VALUE = re.compile(
    r"^(very )?(good|bad|nice|worst|best|ok|okay|great|awesome|excellent|poor|love|hate).{0,40}$",
    re.I,
)


def insight_score(text: str) -> int:
    return sum(1 for pattern in INSIGHT_RE if pattern.search(text or ""))


def is_helpful_review(text: str) -> bool:
    """Long, multi-signal reviews useful for product insight (not one-liners)."""
    cleaned = clean_text(text or "")
    if len(cleaned) < MIN_HELPFUL_CHARS:
        return False
    words = re.findall(r"[A-Za-z']+", cleaned)
    if len(words) < MIN_HELPFUL_WORDS:
        return False
    if LOW_VALUE.match(cleaned.strip()):
        return False
    if insight_score(cleaned) < 2:
        return False
    if len({w.lower() for w in words}) < 18:
        return False
    return True


def is_recent_review(review_date: datetime | None) -> bool:
    if review_date is None:
        return False
    return YEAR_MIN <= review_date.year <= YEAR_MAX


# Backwards-compatible aliases used by older callers
def is_meaningful_review(text: str) -> bool:
    return is_helpful_review(text)
