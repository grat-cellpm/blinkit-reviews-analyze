import json
import re
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Review, ReviewAnalysis
from app.services.embeddings import query_similar
from app.services.llm_analysis import _heuristic_analyze

CHAT_SYSTEM = """You are an expert Product Management AI Assistant for Blinkit. Your role is to analyze user feedback and provide strategic insights across 5 core areas:
1. User Behavior: Explain shopping patterns, habit loops, and exploration barriers.
2. Pain Points: Identify UI/UX friction, search/recommendation flaws, and delivery issues.
3. Review Analysis: Summarize recurring themes, sentiments, and feature requests.
4. Insights: Extrapolate broader trends, unmet demands, and category opportunities from the sample data.
5. Recommendations: Suggest actionable product features, A/B experiments, and KPIs to track.

Base your answers on the provided review evidence. Because you only see a sample of reviews, confidently synthesize this evidence with general e-commerce product knowledge to fully answer the user's question, even if asking for broad trends or feature suggestions.
Return ONLY valid JSON:
{
  "explanation": "string (use clear formatting and bullet points where appropriate)",
  "confidence": 0.0-1.0,
  "related_themes": ["theme1"]
}"""


def _fallback_answer(question: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    themes = []
    for e in evidence:
        t = (e.get("metadata") or {}).get("main_theme")
        if t:
            themes.append(t)
    top_theme = max(set(themes), key=themes.count) if themes else "Other"
    q = question.lower()

    if any(w in q for w in ["explor", "new categor", "experiment", "prevent"]):
        explanation = (
            f"Across {len(evidence)} relevant reviews, users often stay in familiar categories "
            f"(theme signal: {top_theme}). Barriers include weak search/recommendations, "
            "unclear category browsing, and habit-driven replenishment. "
            "Users need trust signals, availability, and guided discovery before trying new categories."
        )
    elif any(w in q for w in ["discover", "recommendation"]):
        explanation = (
            "Users mention recommendations as either repetitive or missing cross-category suggestions, "
            "which reinforces same-category buying. Improving personalization and search visibility could unlock discovery."
        )
    elif any(w in q for w in ["habit", "repeat", "same categor"]):
        explanation = (
            "Evidence points to habit loops as primary drivers of category stickiness. "
            "Users rely on familiar products and past orders for quick replenishment, rarely browsing outside their usual patterns."
        )
    elif any(w in q for w in ["complaint", "frustrat", "biggest", "pain"]):
        explanation = (
            f"The strongest recurring frustrations in retrieved reviews cluster around {top_theme}. "
            "Common issues include delivery reliability, stockouts, pricing clarity, and hard-to-find products."
        )
    elif any(w in q for w in ["unmet", "need", "information"]):
        explanation = (
            "Consistently, users require clear product descriptions, better photos, and trustworthy reviews before trying unfamiliar items. "
            f"Unmet needs often surface around poor catalog navigation and missing product details (theme: {top_theme})."
        )
    elif any(w in q for w in ["segment"]):
        explanation = (
            "Experimentation is most common among users seeking specialty items (e.g., specific desserts, new brands). "
            "These segments need high-quality imagery and detailed product information to build trust."
        )
    else:
        explanation = (
            f"Based on {len(evidence)} matching reviews, the dominant theme is {top_theme}. "
            "Evidence points to habit loops and discovery friction as primary drivers of category stickiness."
        )

    conf = 0.55
    if evidence:
        conf = min(0.9, 0.5 + sum(e.get("relevance_score") or 0 for e in evidence) / (2 * len(evidence)))
    return {
        "explanation": explanation,
        "confidence": round(conf, 3),
        "related_themes": list(dict.fromkeys(themes))[:5],
    }


def _llm_answer(question: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    settings = get_settings()
    if not settings.has_groq or not evidence:
        return _fallback_answer(question, evidence)

    evidence_block = "\n\n".join(
        [
            f"[{i+1}] rating={(e.get('metadata') or {}).get('rating')} "
            f"theme={(e.get('metadata') or {}).get('main_theme')}\n{e.get('content')}"
            for i, e in enumerate(evidence)
        ]
    )
    try:
        from groq import Groq

        client = Groq(api_key=settings.groq_api_key)
        completion = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": CHAT_SYSTEM},
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nReview evidence:\n{evidence_block}",
                },
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        raw = completion.choices[0].message.content or "{}"
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", raw)
            data = json.loads(match.group(0)) if match else {}
        return {
            "explanation": data.get("explanation") or _fallback_answer(question, evidence)["explanation"],
            "confidence": float(data.get("confidence") or 0.7),
            "related_themes": data.get("related_themes") or [],
        }
    except Exception:
        return _fallback_answer(question, evidence)


def answer_question(db: Session, question: str) -> dict[str, Any]:
    raw_evidence = query_similar(question, top_k=30)
    evidence = []
    seen = set()
    for e in raw_evidence:
        content = (e.get("content") or "").strip().lower()
        if content and content not in seen:
            seen.add(content)
            evidence.append(e)
            if len(evidence) >= 8:
                break

    # Fallback to SQL keyword search if vector store empty
    if not evidence:
        import sqlalchemy.sql.expression as sql_expr
        from sqlalchemy import or_
        
        words = [w.strip("?,.!") for w in question.split() if len(w.strip("?,.!")) > 3]
        ignore_words = {"what", "when", "where", "which", "who", "why", "how", "are", "the", "for", "and", "with", "this", "that"}
        keywords = [w for w in words if w.lower() not in ignore_words]
        
        reviews = []
        if keywords:
            conditions = [Review.content.ilike(f"%{w}%") for w in keywords]
            reviews = (
                db.query(Review, ReviewAnalysis)
                .outerjoin(ReviewAnalysis, Review.review_id == ReviewAnalysis.review_id)
                .filter(Review.is_duplicate.is_(False))
                .filter(or_(*conditions))
                .limit(30)
                .all()
            )
            
        if not reviews:
            reviews = (
                db.query(Review, ReviewAnalysis)
                .outerjoin(ReviewAnalysis, Review.review_id == ReviewAnalysis.review_id)
                .filter(Review.is_duplicate.is_(False))
                .order_by(sql_expr.func.random())
                .limit(30)
                .all()
            )
            
        for review, analysis in reviews:
            content_lower = review.content.strip().lower()
            if content_lower not in seen:
                seen.add(content_lower)
                evidence.append(
                    {
                        "review_id": review.review_id,
                        "content": review.content,
                        "metadata": {
                            "rating": review.rating,
                            "sentiment": analysis.sentiment if analysis else None,
                            "main_theme": analysis.main_theme if analysis else None,
                        },
                        "relevance_score": 0.5,
                    }
                )
                if len(evidence) >= 8:
                    break

    answer = _llm_answer(question, evidence)
    supporting = []
    for e in evidence:
        meta = e.get("metadata") or {}
        supporting.append(
            {
                "review_id": e.get("review_id"),
                "content": e.get("content") or "",
                "rating": int(meta.get("rating") or 0),
                "sentiment": meta.get("sentiment"),
                "main_theme": meta.get("main_theme"),
                "relevance_score": e.get("relevance_score"),
            }
        )

    return {
        "question": question,
        "explanation": answer["explanation"],
        "supporting_reviews": supporting,
        "matching_reviews": len(supporting),
        "confidence": float(answer.get("confidence") or 0.6),
        "related_themes": answer.get("related_themes") or [],
    }


# silence unused import warning for optional heuristic reuse
_ = _heuristic_analyze
