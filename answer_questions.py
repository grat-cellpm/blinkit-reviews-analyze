import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db, engine, SessionLocal
from app.services.rag import answer_question

questions = {
    "1. Understand user behavior": [
        "Why are users repeatedly buying the same products?",
        "What are the most common shopping patterns?",
        "Which categories have the highest repeat purchases?",
        "Which users rarely explore new products?"
    ],
    "2. Discover pain points": [
        "What are the biggest pain points mentioned in Blinkit reviews?",
        "Why aren't users discovering new products?",
        "Are users complaining about search, recommendations, or product visibility?"
    ],
    "3. Analyze reviews": [
        "What are the top recurring themes in recent reviews?",
        "Summarize negative reviews related to product discovery.",
        "Show reviews mentioning 'search', 'recommendation', or 'explore'.",
        "What features are users requesting most?"
    ],
    "4. Generate insights": [
        "What are the top 5 opportunities to improve product discovery?",
        "What trends have emerged in the last 30 days?",
        "Which categories have the highest unmet demand?",
        "Which product categories receive the most positive feedback?"
    ],
    "5. Recommend actions": [
        "How can Blinkit encourage users to discover new products?",
        "Suggest AI-powered recommendation features.",
        "What experiments (A/B tests) should the product team run?",
        "Which KPIs should we track to measure improved discovery?"
    ]
}

def main():
    db = SessionLocal()
    try:
        with open("rag_answers.md", "w", encoding="utf-8") as f:
            f.write("# Blinkit AI Assistant Answers\n\n")
            for section, qs in questions.items():
                f.write(f"## {section}\n\n")
                for q in qs:
                    print(f"Answering: {q}")
                    res = answer_question(db, q)
                    f.write(f"### Q: {q}\n")
                    f.write(f"**Answer:** {res['explanation']}\n\n")
                    f.write(f"*Confidence: {res['confidence']}, Related Themes: {', '.join(res['related_themes'])}*\n\n")
                    
                    if res.get('supporting_reviews'):
                        f.write("**Supporting Reviews:**\n")
                        for review in res['supporting_reviews'][:2]: # Only show top 2 to keep it concise
                            f.write(f"- (Rating: {review['rating']}, Theme: {review['main_theme']}) {review['content'][:150]}...\n")
                        f.write("\n")
    finally:
        db.close()
    
    print("Done! Check rag_answers.md")

if __name__ == "__main__":
    main()
