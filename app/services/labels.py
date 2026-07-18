"""Canonical labels used across analysis, clustering, and the dashboard."""

CANONICAL_THEMES = [
    "Habit Shopping",
    "Poor Product Discovery",
    "Search Issues",
    "Recommendation Quality",
    "Delivery Experience",
    "Product Availability",
    "Pricing",
    "App Experience",
    "Customer Support",
    "Other",
]

USER_SEGMENTS = [
    "Routine Shoppers",
    "Explorers",
    "Deal Hunters",
    "Emergency Buyers",
    "High Frequency Users",
]

SENTIMENTS = ["positive", "neutral", "negative"]

THEME_ALIASES = {
    "habit": "Habit Shopping",
    "habit shopping": "Habit Shopping",
    "routine": "Habit Shopping",
    "discovery": "Poor Product Discovery",
    "poor product discovery": "Poor Product Discovery",
    "product discovery": "Poor Product Discovery",
    "search": "Search Issues",
    "search issues": "Search Issues",
    "recommendation": "Recommendation Quality",
    "recommendation quality": "Recommendation Quality",
    "recommendations": "Recommendation Quality",
    "delivery": "Delivery Experience",
    "delivery experience": "Delivery Experience",
    "availability": "Product Availability",
    "product availability": "Product Availability",
    "stock": "Product Availability",
    "pricing": "Pricing",
    "price": "Pricing",
    "app": "App Experience",
    "app experience": "App Experience",
    "ui": "App Experience",
    "support": "Customer Support",
    "customer support": "Customer Support",
    "service": "Customer Support",
}

SEGMENT_ALIASES = {
    "routine": "Routine Shoppers",
    "routine shoppers": "Routine Shoppers",
    "explorer": "Explorers",
    "explorers": "Explorers",
    "deal": "Deal Hunters",
    "deal hunters": "Deal Hunters",
    "emergency": "Emergency Buyers",
    "emergency buyers": "Emergency Buyers",
    "high frequency": "High Frequency Users",
    "high frequency users": "High Frequency Users",
    "frequent": "High Frequency Users",
}


def normalize_theme(raw: str | None) -> str:
    if not raw:
        return "Other"
    key = raw.strip().lower()
    if key in THEME_ALIASES:
        return THEME_ALIASES[key]
    for theme in CANONICAL_THEMES:
        if theme.lower() == key:
            return theme
    for alias, theme in THEME_ALIASES.items():
        if alias in key:
            return theme
    return "Other"


def normalize_segment(raw: str | None) -> str:
    if not raw:
        return "Routine Shoppers"
    key = raw.strip().lower()
    if key in SEGMENT_ALIASES:
        return SEGMENT_ALIASES[key]
    for seg in USER_SEGMENTS:
        if seg.lower() == key:
            return seg
    for alias, seg in SEGMENT_ALIASES.items():
        if alias in key:
            return seg
    return "Routine Shoppers"


def normalize_sentiment(raw: str | None) -> str:
    if not raw:
        return "neutral"
    key = raw.strip().lower()
    if key in SENTIMENTS:
        return key
    if key in {"pos", "good", "happy"}:
        return "positive"
    if key in {"neg", "bad", "angry"}:
        return "negative"
    return "neutral"
