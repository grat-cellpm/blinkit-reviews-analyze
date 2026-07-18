# Blinkit Feedback Intelligence Platform

AI-powered platform that turns Blinkit Google Play Store reviews into actionable product insights for Product Managers.

## Features

- **Review ingestion** — Fetch Blinkit Play Store reviews with incremental updates
- **Preprocessing** — Dedup, clean, normalize while preserving ratings and metadata
- **LLM analysis** — Sentiment, themes, pain points, shopping behavior, opportunities
- **Semantic search (RAG)** — Embeddings + ChromaDB + retrieval-augmented answers
- **Theme clustering** — Habit shopping, discovery issues, delivery, pricing, and more
- **User segmentation** — Routine shoppers, explorers, deal hunters, emergency buyers
- **Product opportunities** — Ranked recommendations with evidence and confidence
- **AI chat** — Natural-language Q&A grounded in review evidence
- **Dashboard** — KPIs, themes, segments, review explorer, opportunities

## Tech Stack

| Layer | Stack |
|-------|--------|
| Frontend | Next.js 14, Tailwind CSS, shadcn/ui, Recharts |
| Backend | FastAPI, SQLAlchemy, SQLite |
| AI | Groq (LLM), Sentence Transformers, ChromaDB |
| Ingestion | google-play-scraper |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- (Optional) [Groq API key](https://console.groq.com) for live LLM analysis

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env and set GROQ_API_KEY if you have one

# Seed demo data (works offline / without Groq)
python -m app.seed.seed_data

# Start API
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:3000

### 3. Ingest live Play Store reviews (optional)

```bash
# With backend running and GROQ_API_KEY set:
curl -X POST http://localhost:8000/api/ingestion/fetch
curl -X POST http://localhost:8000/api/pipeline/run
```

## Project Structure

```
BLINKIT/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── main.py          # App entry
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── routers/         # REST endpoints
│   │   ├── services/        # Business logic & AI pipeline
│   │   └── seed/            # Demo dataset
│   └── requirements.txt
├── frontend/                # Next.js dashboard
│   ├── app/                 # App Router pages
│   ├── components/
│   └── lib/
└── docs/
    └── ARCHITECTURE.md      # Architecture & AI workflow
```

## AI notes

- **LLM**: Set `GROQ_API_KEY` in `backend/.env` for Groq-powered analysis and chat. Without it, a deterministic heuristic analyzer + RAG answerer still works for demos.
- **Vectors**: Prefer ChromaDB + Sentence Transformers when installable. On Python 3.14 (this environment), the app uses a **TF-IDF + cosine similarity** vector index with the same RAG API surface. Optional packages are listed in `requirements.txt`.

## Environment Variables

See `backend/.env.example`:

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key (optional; heuristic fallback without it) |
| `GROQ_MODEL` | Default: `llama-3.3-70b-versatile` |
| `DATABASE_URL` | Default: `sqlite:///./data/blinkit.db` |
| `CHROMA_PATH` | ChromaDB persist directory |
| `BLINKIT_APP_ID` | Play Store package: `com.grofers.customerapp` |
| `CORS_ORIGINS` | Frontend origins |

## Business Questions Answered

The AI chat and insight APIs answer questions such as:

- Why do users repeatedly buy from the same categories?
- What prevents category exploration?
- How do users discover products?
- What role do habits play?
- Which frustrations repeat across reviews?
- Which product improvements should Blinkit prioritize?

Every answer includes an explanation, supporting excerpts, matching review count, and a confidence score.

## Documentation

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for architecture, AI pipeline, RAG design, and validation.

## License

MIT
