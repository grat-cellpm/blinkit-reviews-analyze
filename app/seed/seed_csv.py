import sys
import csv
from pathlib import Path
from datetime import datetime
import dateutil.parser

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

def seed_csv(csv_path: str, run_embeddings: bool = True) -> None:
    init_db()
    db = SessionLocal()
    try:
        existing = {r[0] for r in db.query(Review.review_id).all()}
        
        inserted = 0
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                review_id = str(row['Review ID'])
                if review_id in existing:
                    continue
                    
                content = str(row['Original Review Text'])
                
                try:
                    rating = int(row['Star Rating'])
                except (ValueError, TypeError):
                    rating = 5
                
                try:
                    review_date = dateutil.parser.parse(row['Review Date'])
                    if review_date.tzinfo is not None:
                        review_date = review_date.replace(tzinfo=None)
                except Exception:
                    review_date = datetime.utcnow()
                    
                db.add(
                    Review(
                        review_id=review_id,
                        user_name="Play Store User",
                        content=content,
                        cleaned_content=clean_text(content),
                        rating=rating,
                        thumbs_up=0,
                        review_date=review_date,
                        source="play_store",
                        is_processed=True,
                        is_duplicate=False,
                    )
                )
                inserted += 1
                if inserted % 500 == 0:
                    db.commit()
                    print(f"Inserted {inserted} reviews...")
                    
        db.commit()
        print(f"Total inserted {inserted} reviews from CSV")

        print("Analyzing pending reviews...")
        analyzed = analyze_pending_reviews(db)
        print(f"Analyzed: {analyzed}")
        
        print("Rebuilding summaries...")
        themes = rebuild_theme_summaries(db)
        segments = rebuild_segment_summaries(db)
        opps = rebuild_opportunities(db)
        print(f"Themes: {themes}, Segments: {segments}, Opportunities: {opps}")

        if run_embeddings:
            try:
                print("Running embeddings...")
                embedded = embed_pending_reviews(db)
                print(f"Embedded: {embedded}")
            except Exception as exc:
                print(f"Embedding skipped: {exc}")
        print("CSV Seed complete.")
    finally:
        db.close()

if __name__ == "__main__":
    csv_file = ROOT.parent / "data_collection" / "data" / "blinkit_reviews.csv"
    if csv_file.exists():
        print(f"Seeding from {csv_file}")
        seed_csv(str(csv_file), run_embeddings=True)
    else:
        print(f"CSV not found at {csv_file}")
