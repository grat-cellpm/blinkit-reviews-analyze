"""Seed realistic Blinkit review data for local demos (no Play Store / Groq required)."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Allow `python -m app.seed.seed_data` from backend/
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import SessionLocal, init_db
from app.models import Review
from app.services.pipeline import (
    analyze_pending_reviews,
    embed_pending_reviews,
    rebuild_opportunities,
    rebuild_segment_summaries,
    rebuild_theme_summaries,
)
from app.services.preprocessing import clean_text

SEED_REVIEWS: list[dict] = [
    {
        "review_id": "seed_001",
        "user_name": "Priya S",
        "rating": 4,
        "content": "I always order dairy and snacks from Blinkit. Same categories every week. I trust these items but I never explore new sections because I don't know what's good.",
        "days_ago": 3,
    },
    {
        "review_id": "seed_002",
        "user_name": "Rahul M",
        "rating": 2,
        "content": "Search is terrible. I try to find organic products in new categories but get irrelevant results. Hard to discover anything beyond my usual list.",
        "days_ago": 5,
    },
    {
        "review_id": "seed_003",
        "user_name": "Ananya K",
        "rating": 3,
        "content": "Recommendations keep showing the same groceries I already buy. No suggestions for new categories like personal care or gourmet. Feels repetitive.",
        "days_ago": 7,
    },
    {
        "review_id": "seed_004",
        "user_name": "Vikram T",
        "rating": 5,
        "content": "Super fast delivery for emergency needs. Ordered medicines and fruits late night. Don't browse much though, just buy what I urgently need.",
        "days_ago": 2,
    },
    {
        "review_id": "seed_005",
        "user_name": "Sneha R",
        "rating": 2,
        "content": "Prices are higher than local stores. I only shop when there is a coupon or offer. Without deals I stick to the cheapest staples.",
        "days_ago": 10,
    },
    {
        "review_id": "seed_006",
        "user_name": "Arjun P",
        "rating": 1,
        "content": "Out of stock constantly for items I want to try in bakery and frozen foods. Availability issues stop me from exploring new categories.",
        "days_ago": 4,
    },
    {
        "review_id": "seed_007",
        "user_name": "Meera L",
        "rating": 4,
        "content": "I order almost daily for milk, bread and eggs. Habit shopping at its best. Would love occasional prompts to try new healthy snacks.",
        "days_ago": 1,
    },
    {
        "review_id": "seed_008",
        "user_name": "Karan D",
        "rating": 3,
        "content": "App is slow when browsing categories. I give up and just reorder my previous cart. UI friction kills discovery.",
        "days_ago": 8,
    },
    {
        "review_id": "seed_009",
        "user_name": "Neha G",
        "rating": 2,
        "content": "Customer support took forever for a missing item refund. Now I hesitate to try new brands or categories in case something goes wrong.",
        "days_ago": 12,
    },
    {
        "review_id": "seed_010",
        "user_name": "Siddharth N",
        "rating": 5,
        "content": "Love exploring gourmet and imported sections. Wish filters helped me discover more like what I liked before. Still the best for trying new products.",
        "days_ago": 6,
    },
    {
        "review_id": "seed_011",
        "user_name": "Pooja V",
        "rating": 3,
        "content": "I don't know how to find products outside groceries. No clear guide for beauty or home care. Need better information before trying a new category.",
        "days_ago": 9,
    },
    {
        "review_id": "seed_012",
        "user_name": "Amit B",
        "rating": 1,
        "content": "Delivery was late twice this week. When I'm in a hurry I only reorder known items so I don't waste time browsing.",
        "days_ago": 3,
    },
    {
        "review_id": "seed_013",
        "user_name": "Ishita C",
        "rating": 4,
        "content": "Deal hunter here. I check offers first then buy. Sometimes offers are only on categories I never use, so I ignore them.",
        "days_ago": 11,
    },
    {
        "review_id": "seed_014",
        "user_name": "Rohan J",
        "rating": 2,
        "content": "Search filters don't work well for dietary preferences. Can't discover gluten-free or vegan options easily across categories.",
        "days_ago": 14,
    },
    {
        "review_id": "seed_015",
        "user_name": "Divya A",
        "rating": 5,
        "content": "High frequency user. Order 4-5 times a week. Usually same pantry items. Personalized 'new for you' would help me experiment.",
        "days_ago": 2,
    },
    {
        "review_id": "seed_016",
        "user_name": "Nikhil S",
        "rating": 3,
        "content": "Poor product discovery on homepage. Everything pushes staples. Rarely see curated collections for new categories.",
        "days_ago": 15,
    },
    {
        "review_id": "seed_017",
        "user_name": "Kavya M",
        "rating": 2,
        "content": "MRP and Blinkit price differences confuse me. Without clear value I stick to what I bought before.",
        "days_ago": 7,
    },
    {
        "review_id": "seed_018",
        "user_name": "Harsh P",
        "rating": 4,
        "content": "Emergency buyer. When guests arrive I need party snacks fast. Don't explore, just search and checkout.",
        "days_ago": 4,
    },
    {
        "review_id": "seed_019",
        "user_name": "Aisha F",
        "rating": 3,
        "content": "Recommendations quality is weak. Shows baby care when I only buy kitchen essentials. Makes me distrust suggestions for new categories.",
        "days_ago": 13,
    },
    {
        "review_id": "seed_020",
        "user_name": "Manish K",
        "rating": 1,
        "content": "App crashes while opening category pages. Forced to use search for the same products again and again.",
        "days_ago": 5,
    },
    {
        "review_id": "seed_021",
        "user_name": "Ritu S",
        "rating": 5,
        "content": "Usually buy vegetables and fruits. Habit. Would try bakery if I could see freshness info and ratings before ordering.",
        "days_ago": 6,
    },
    {
        "review_id": "seed_022",
        "user_name": "Yash R",
        "rating": 2,
        "content": "Stockouts in personal care every time I want to try something new. Ends up buying the same soap and shampoo.",
        "days_ago": 8,
    },
    {
        "review_id": "seed_023",
        "user_name": "Tanvi H",
        "rating": 4,
        "content": "I enjoy exploring beverages and snacks. Better search suggestions would help me find niche products faster.",
        "days_ago": 1,
    },
    {
        "review_id": "seed_024",
        "user_name": "Gaurav L",
        "rating": 3,
        "content": "Need more info like ingredients and usage before trying new home cleaning products. Without that I stick to known brands.",
        "days_ago": 16,
    },
    {
        "review_id": "seed_025",
        "user_name": "Shreya D",
        "rating": 2,
        "content": "Biggest complaint is repetitive carts and no smart discovery. Why aren't users exploring? Because the app never nudges us beyond habits.",
        "days_ago": 9,
    },
    {
        "review_id": "seed_026",
        "user_name": "Aditya W",
        "rating": 5,
        "content": "Fast delivery and reliable for weekly groceries. I am a routine shopper but open to deals in new categories if highlighted clearly.",
        "days_ago": 3,
    },
    {
        "review_id": "seed_027",
        "user_name": "Nisha T",
        "rating": 1,
        "content": "Customer care chat disconnected thrice. Frustration with support makes me avoid experimenting with unfamiliar products.",
        "days_ago": 18,
    },
    {
        "review_id": "seed_028",
        "user_name": "Varun C",
        "rating": 3,
        "content": "How do users discover products? Mostly reorder and search. Browse feels empty. Category landing pages need better curation.",
        "days_ago": 11,
    },
    {
        "review_id": "seed_029",
        "user_name": "Lakshmi P",
        "rating": 4,
        "content": "Habits play a huge role. I reorder milk every morning without thinking. A weekly 'break your routine' pack could work.",
        "days_ago": 2,
    },
    {
        "review_id": "seed_030",
        "user_name": "Farhan A",
        "rating": 2,
        "content": "Pricing in electronics accessories and kitchenware feels opaque. Deal hunters like me need clearer savings vs other apps.",
        "days_ago": 10,
    },
    {
        "review_id": "seed_031",
        "user_name": "Jyoti R",
        "rating": 5,
        "content": "Explorer segment: I try new ice cream and dessert brands often. Segment of users who experiment need better reviews and photos.",
        "days_ago": 4,
    },
    {
        "review_id": "seed_032",
        "user_name": "Deepak M",
        "rating": 3,
        "content": "Unmet need: bundle suggestions across categories for dinners. Currently I buy veggies and forget complementary items.",
        "days_ago": 7,
    },
    {
        "review_id": "seed_033",
        "user_name": "Pallavi S",
        "rating": 2,
        "content": "Search issues when spelling brand names wrong. Autocomplete is weak so I never find new products outside my history.",
        "days_ago": 12,
    },
    {
        "review_id": "seed_034",
        "user_name": "Imran Q",
        "rating": 4,
        "content": "High frequency ordering for office pantry. Same SKUs. Product opportunity: rotating discovery carousel for frequent users.",
        "days_ago": 5,
    },
    {
        "review_id": "seed_035",
        "user_name": "Sonal B",
        "rating": 1,
        "content": "Delivery partner cancelled and I had to re-order urgently. In emergency mode there is zero exploration, only speed.",
        "days_ago": 6,
    },
    {
        "review_id": "seed_036",
        "user_name": "Rakesh V",
        "rating": 3,
        "content": "What prevents category exploration? Fear of bad quality, no samples, and no trust badges on new brands.",
        "days_ago": 14,
    },
    {
        "review_id": "seed_037",
        "user_name": "Chitra N",
        "rating": 5,
        "content": "Great for staples. I would try baby products if I saw expiry and authenticity guarantees more clearly.",
        "days_ago": 8,
    },
    {
        "review_id": "seed_038",
        "user_name": "Mohit G",
        "rating": 2,
        "content": "App experience on category browse is cluttered. Too many banners. Hard to calmly explore new aisles.",
        "days_ago": 15,
    },
    {
        "review_id": "seed_039",
        "user_name": "Anjali K",
        "rating": 4,
        "content": "I discover products mainly via search and past orders. Recommendations rarely help me try a new category.",
        "days_ago": 3,
    },
    {
        "review_id": "seed_040",
        "user_name": "Suresh P",
        "rating": 3,
        "content": "Frustrations that repeat: late slots, stockouts, and useless recommendations. Fix these and exploration will improve.",
        "days_ago": 9,
    },
]


def seed(run_embeddings: bool = True) -> None:
    init_db()
    db = SessionLocal()
    try:
        existing = {r[0] for r in db.query(Review.review_id).all()}
        inserted = 0
        now = datetime.utcnow()
        for i in range(3000):
            base_item = SEED_REVIEWS[i % len(SEED_REVIEWS)]
            review_id = f"seed_{i+1:04d}"
            if review_id in existing:
                continue
            content = base_item["content"]
            db.add(
                Review(
                    review_id=review_id,
                    user_name=f"{base_item['user_name']} {i // len(SEED_REVIEWS)}",
                    content=content,
                    cleaned_content=clean_text(content),
                    rating=base_item["rating"],
                    thumbs_up=base_item.get("thumbs_up", 0),
                    review_date=now - timedelta(days=base_item["days_ago"]),
                    source="seed",
                    is_processed=True,
                    is_duplicate=False,
                )
            )
            inserted += 1
            if inserted % 500 == 0:
                db.commit()
        db.commit()
        print(f"Inserted {inserted} seed reviews")

        analyzed = analyze_pending_reviews(db)
        print(f"Analyzed: {analyzed}")
        themes = rebuild_theme_summaries(db)
        segments = rebuild_segment_summaries(db)
        opps = rebuild_opportunities(db)
        print(f"Themes: {themes}, Segments: {segments}, Opportunities: {opps}")

        if run_embeddings:
            try:
                embedded = embed_pending_reviews(db)
                print(f"Embedded: {embedded}")
            except Exception as exc:
                print(f"Embedding skipped (install sentence-transformers/chromadb): {exc}")
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed(run_embeddings=True)
