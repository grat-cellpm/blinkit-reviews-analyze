# Blinkit Feedback Intelligence

Full-stack AI platform for Blinkit Google Play review insights.

## Setup

See root [README.md](../README.md).

## Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env
python -m app.seed.seed_data
uvicorn app.main:app --reload --port 8000
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```
