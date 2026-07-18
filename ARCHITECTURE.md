# Blinkit Feedback Intelligence — Architecture

## Overview

The platform ingests Blinkit Google Play Store reviews, cleans them, embeds them for semantic search, analyzes them with an LLM, clusters themes, segments users, and surfaces insights through a Next.js dashboard and RAG-powered chat.

```
Google Play Reviews
        ↓
   Data Cleaning
        ↓
    Embeddings
        ↓
  Vector DB (ChromaDB)
        ↓
   RAG Retrieval
        ↓
   LLM Analysis
        ↓
 Theme Clustering + Segmentation
        ↓
  Insight Generation
        ↓
 Interactive Dashboard
```

## Clean Architecture

```
routers/     → HTTP adapters (thin)
schemas/     → request/response contracts
services/    → domain logic & AI orchestration
models/      → persistence
```

Review sources are abstracted behind `ReviewSource` so App Store or Reddit can be added later without changing analysis or RAG layers.

## Components

### 1. Review Collection

- Package: `google-play-scraper`
- App ID: `com.grofers.customerapp`
- Incremental: skip reviews whose `review_id` already exists
- Endpoint: `POST /api/ingestion/fetch`

### 2. Preprocessing

- Deduplicate by `review_id` and near-identical cleaned text
- Strip HTML, emojis, excess whitespace
- Normalize case for matching; keep original for display
- Preserve rating, date, thumbs-up, reply metadata

### 3. LLM Analysis (per review)

Structured JSON fields:

| Field | Purpose |
|-------|---------|
| `sentiment` | positive / neutral / negative |
| `main_theme` | Primary theme label |
| `pain_point` | Core complaint or friction |
| `shopping_behavior` | Habit / exploration / deal / emergency |
| `user_motivation` | Why they shop this way |
| `discovery_issue` | Barriers to finding products |
| `product_opportunity` | Implied product idea |
| `user_segment` | Segment assignment |
| `confidence` | 0–1 model confidence |

Provider: **Groq** (`llama-3.3-70b-versatile`). Without `GROQ_API_KEY`, a deterministic heuristic analyzer runs so the app remains demoable offline.

### 4. Embeddings & RAG

- Preferred: `sentence-transformers/all-MiniLM-L6-v2` + ChromaDB
- Fallback (Python versions without ST/Chroma wheels): TF-IDF + cosine similarity persisted under `CHROMA_PATH`
- Chat flow:
  1. Embed / vectorize the user question
  2. Retrieve top-k similar reviews
  3. Prompt LLM with question + evidence (or heuristic synthesizer)
  4. Return explanation, excerpts, match count, confidence

### 5. Theme Clustering

Themes are derived from LLM labels and frequency-aggregated. Canonical themes include:

- Habit Shopping
- Poor Product Discovery
- Search Issues
- Recommendation Quality
- Delivery Experience
- Product Availability
- Pricing
- App Experience
- Customer Support

### 6. User Segmentation

| Segment | Signal |
|---------|--------|
| Routine Shoppers | Habit / repeat-category language |
| Explorers | Trying new categories / discovery |
| Deal Hunters | Price, offers, coupons |
| Emergency Buyers | Urgency, last-minute, stockouts |
| High Frequency Users | Mentions of daily/weekly usage |

### 7. Product Opportunity Generator

Aggregates recurring pain points → ranked opportunities with evidence count, estimated impact, and confidence.

## API Surface

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/ingestion/fetch` | Pull Play Store reviews |
| POST | `/api/pipeline/preprocess` | Clean & dedupe |
| POST | `/api/pipeline/analyze` | LLM analysis |
| POST | `/api/pipeline/embed` | Embeddings → Chroma |
| POST | `/api/pipeline/run` | Full pipeline |
| GET | `/api/dashboard/metrics` | KPIs |
| GET | `/api/themes` | Theme distribution |
| GET | `/api/segments` | User segments |
| GET | `/api/reviews` | Search & filters |
| POST | `/api/chat` | RAG Q&A |
| GET | `/api/opportunities` | Ranked opportunities |

## Validation Process

1. **Ingestion** — Verify review IDs unique; spot-check ratings/dates against Play Store.
2. **Preprocessing** — Assert no HTML/emoji leftovers on sample; duplicate rate = 0 after clean.
3. **Analysis** — Schema validation on LLM JSON; confidence thresholds; human review of 20–50 samples.
4. **RAG** — Spot-check that retrieved reviews are topically relevant to the question; answers must cite excerpts.
5. **Themes/segments** — Frequency totals should sum to analyzed review count (within multi-label tolerance).
6. **Dashboard** — Metrics match SQL aggregates; filters return consistent subsets.

## Extensibility

To add Reddit or App Store:

1. Implement `ReviewSource.fetch()` in `services/sources/`
2. Map to the shared `Review` model
3. Reuse preprocessing → embeddings → analysis unchanged

## Security Notes

- Do not commit `.env` or API keys
- CORS limited to configured frontend origins
- SQLite suitable for local/demo; use PostgreSQL in production (`DATABASE_URL`)
