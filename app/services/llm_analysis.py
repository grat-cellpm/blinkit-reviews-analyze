import json
import re
from typing import Any

from app.config import get_settings
from app.services.labels import normalize_segment, normalize_sentiment, normalize_theme

ANALYSIS_SYSTEM_PROMPT = """You are a product research analyst for Blinkit (quick commerce grocery delivery in India).
Analyze the user review and return ONLY valid JSON with these keys:
- sentiment: positive | neutral | negative
- main_theme: one of [Habit Shopping, Poor Product Discovery, Search Issues, Recommendation Quality, Delivery Experience, Product Availability, Pricing, App Experience, Customer Support, Other]
- pain_point: short string or null
- shopping_behavior: short string describing habit/exploration/deals/urgency
- user_motivation: short string
- discovery_issue: short string or null (what blocks finding/trying new categories)
- product_opportunity: short product idea or null
- user_segment: one of [Routine Shoppers, Explorers, Deal Hunters, Emergency Buyers, High Frequency Users]
- confidence: number between 0 and 1

Focus on category habit loops, discovery barriers, search/recommendation quality, and unmet needs."""


def _heuristic_analyze(text: str, rating: int) -> dict[str, Any]:
    lower = (text or "").lower()

    if rating >= 4:
        sentiment = "positive"
    elif rating <= 2:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    theme = "Other"
    pain = None
    discovery = None
    opportunity = None
    behavior = "general shopping"
    motivation = "convenience"
    segment = "Routine Shoppers"

    rules = [
        (
            ["same", "always", "usually", "habit", "every time", "regular", "only buy"],
            "Habit Shopping",
            "Users stick to familiar categories",
            "Habit / repeat purchases reduce category exploration",
            "Surface 'try something new' prompts for routine shoppers",
            "repeat category purchases",
            "familiarity and trust",
            "Routine Shoppers",
        ),
        (
            ["search", "find", "can't find", "cannot find", "filter", "no results"],
            "Search Issues",
            "Hard to find products via search",
            "Search fails to surface relevant or new-category items",
            "Improve search ranking and category-aware filters",
            "search-driven discovery",
            "need to locate specific items quickly",
            "Explorers",
        ),
        (
            ["recommend", "suggestion", "for you", "personalized"],
            "Recommendation Quality",
            "Recommendations feel irrelevant or repetitive",
            "Weak personalization keeps users in known categories",
            "Cross-category recommendation carousels",
            "recommendation browsing",
            "guided discovery",
            "Explorers",
        ),
        (
            ["discover", "explore", "new category", "don't know", "unaware", "browse"],
            "Poor Product Discovery",
            "Users struggle to discover new categories",
            "Poor discovery UX prevents category expansion",
            "Category onboarding and guided browsing",
            "limited exploration",
            "curiosity blocked by UI",
            "Explorers",
        ),
        (
            ["late", "delivery", "rider", "delayed", "minutes", "arrived"],
            "Delivery Experience",
            "Delivery timing or experience issues",
            None,
            "Better ETA accuracy and delivery status transparency",
            "time-sensitive ordering",
            "speed and reliability",
            "Emergency Buyers",
        ),
        (
            ["stock", "available", "out of stock", "unavailable", "missing"],
            "Product Availability",
            "Items frequently out of stock",
            "Stockouts discourage trying new products",
            "Availability badges and substitute suggestions",
            "availability-sensitive shopping",
            "need item immediately",
            "Emergency Buyers",
        ),
        (
            ["price", "expensive", "costly", "offer", "discount", "coupon", "mrp"],
            "Pricing",
            "Price perception or deal hunting friction",
            None,
            "Clearer deal discovery across categories",
            "deal-driven shopping",
            "value seeking",
            "Deal Hunters",
        ),
        (
            ["app", "crash", "bug", "slow", "ui", "interface", "login"],
            "App Experience",
            "App usability or performance issues",
            "Friction in browse/search flows",
            "Simplify browse and search UX",
            "app usage friction",
            "ease of use",
            "High Frequency Users",
        ),
        (
            ["support", "refund", "customer care", "complaint", "chat"],
            "Customer Support",
            "Support or refund friction",
            None,
            "Faster resolution for order issues",
            "support-dependent",
            "trust restoration",
            "High Frequency Users",
        ),
        (
            ["daily", "every day", "weekly", "often", "frequent"],
            "Habit Shopping",
            "High-frequency usage patterns",
            "Frequent users may not see new categories",
            "Habit-breaker campaigns for frequent users",
            "high frequency ordering",
            "routine replenishment",
            "High Frequency Users",
        ),
        (
            ["urgent", "emergency", "suddenly", "immediately", "tonight"],
            "Delivery Experience",
            "Urgent purchase needs",
            "Emergency mode hides exploration",
            "Quick-buy presets plus soft discovery",
            "emergency purchases",
            "urgency",
            "Emergency Buyers",
        ),
    ]

    for keywords, t, p, d, o, b, m, s in rules:
        if any(k in lower for k in keywords):
            theme, pain, discovery, opportunity = t, p, d, o
            behavior, motivation, segment = b, m, s
            break

    confidence = 0.62 if theme != "Other" else 0.45
    if rating <= 2 and theme != "Other":
        confidence = min(0.85, confidence + 0.1)

    return {
        "sentiment": sentiment,
        "main_theme": theme,
        "pain_point": pain,
        "shopping_behavior": behavior,
        "user_motivation": motivation,
        "discovery_issue": discovery,
        "product_opportunity": opportunity,
        "user_segment": segment,
        "confidence": confidence,
    }


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0))
        raise


def analyze_review_text(content: str, rating: int = 3) -> dict[str, Any]:
    settings = get_settings()
    if not settings.has_groq:
        result = _heuristic_analyze(content, rating)
    else:
        try:
            from groq import Groq

            client = Groq(api_key=settings.groq_api_key)
            completion = client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Rating: {rating}/5\nReview: {content}",
                    },
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            raw = completion.choices[0].message.content or "{}"
            result = _extract_json(raw)
        except Exception:
            result = _heuristic_analyze(content, rating)

    return {
        "sentiment": normalize_sentiment(str(result.get("sentiment", "neutral"))),
        "main_theme": normalize_theme(str(result.get("main_theme", "Other"))),
        "pain_point": result.get("pain_point"),
        "shopping_behavior": result.get("shopping_behavior"),
        "user_motivation": result.get("user_motivation"),
        "discovery_issue": result.get("discovery_issue"),
        "product_opportunity": result.get("product_opportunity"),
        "user_segment": normalize_segment(str(result.get("user_segment", "Routine Shoppers"))),
        "confidence": float(result.get("confidence") or 0.7),
        "raw_json": result,
    }
