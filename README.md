# 📰 Regional Newsroom Feedback System v2.0

[![CI](https://github.com/Ashwani4545/regional-newsroom-feedback/actions/workflows/ci.yml/badge.svg)](https://github.com/Ashwani4545/regional-newsroom-feedback/actions)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

AI-powered audience feedback analytics platform built specifically for **regional newsrooms**. Collects reader reactions from multiple channels, detects factual correction requests, computes an Audience Trust Score, and surfaces urgent items for editorial action — all in a purpose-built dashboard.

---

## 🎯 Why this exists

Enterprise social-listening tools (Meltwater, Brandwatch, Talkwalker) cost $6,000–$150,000/year — unaffordable for regional and vernacular outlets. Open-source alternatives are generic NLP notebooks with no newsroom context. This project fills the gap:

| Capability | Enterprise tools | Generic OSS | This project |
|---|---|---|---|
| Affordable / self-hostable | ❌ | ✅ | ✅ |
| Newsroom-specific data model | ❌ | ❌ | ✅ |
| Correction request detection | ❌ | ❌ | ✅ |
| Audience Trust Score | ❌ | ❌ | ✅ |
| Indic language support | ❌ | ❌ | ✅ |
| Editorial workflow routing | ❌ | ❌ | ✅ (roadmap) |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Data Sources                        │
│  Twitter/X API  │  Manual /ingest  │  WhatsApp (soon)  │
└────────┬───────────────┬────────────────────────────────┘
         │               │
         ▼               ▼
┌─────────────────────────────────────────────────────────┐
│               FastAPI Backend (port 8000)               │
│  /ingest_manual  /urgent  /corrections  /trust          │
│  /sentiment_summary  /healthz  /token  /docs            │
└────────┬───────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                    NLP Analysis Engine                  │
│  Tier 1: VADER (default, fast, offline)                 │
│  Tier 2: twitter-roberta-base (USE_TRANSFORMER=true)    │
│  Tier 3: MuRIL / IndicBERT  (USE_INDIC_MODEL=true)      │
└────────┬───────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│              SQLite / PostgreSQL (SQLAlchemy)           │
│  channels │ feedback │ feedback_processing              │
│  trust_snapshots                                        │
└────────┬───────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│            Streamlit Dashboard (port 8501)              │
│  Sentiment trend │ Trust Score │ Urgent feed            │
│  Correction requests │ Export CSV                       │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ Features

- **Multi-channel ingestion** — Twitter/X API v2 + manual REST endpoint (WhatsApp/YouTube on roadmap)
- **Three-tier NLP** — VADER → RoBERTa → MuRIL, progressively richer with env flags
- **Correction request detection** — keyword + pattern matching in English and Hindi transliteration
- **Audience Trust Score (ATS)** — `(positive − negative − corrections) / total`, rolling window, −1 to +1
- **Urgency scoring** — multi-signal (sentiment + correction flag + viral keywords), 1–10 scale
- **Indic language support** — auto language detection via `langdetect`, MuRIL model for 10 Indic languages
- **FastAPI backend** — automatic `/docs` (Swagger UI), Pydantic validation, async-ready
- **JWT authentication** — optional (AUTH_ENABLED=true), token endpoint included
- **Rate limiting** — 60 req/min on ingest endpoints via slowapi
- **Real test suite** — 20+ tests covering analysis, API round-trips, ETL deduplication
- **Docker + Compose** — non-root user, healthcheck, PostgreSQL-ready volume config

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn |
| NLP | NLTK VADER, HuggingFace Transformers, langdetect |
| Database | SQLite (dev) / PostgreSQL (prod) via SQLAlchemy 2.0 |
| Dashboard | Streamlit 1.35, Altair |
| Auth | python-jose (JWT) |
| Rate limiting | slowapi |
| Testing | pytest, pytest-cov, httpx TestClient |
| CI/CD | GitHub Actions |
| Deployment | Docker, Docker Compose |

---

## 🚀 Quick start

### 1. Clone & install

```bash
git clone https://github.com/Ashwani4545/regional-newsroom-feedback.git
cd regional-newsroom-feedback
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env — set TWITTER_BEARER_TOKEN at minimum
```

### 3. Run

```bash
# Terminal 1 — API
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Dashboard
streamlit run dashboard/streamlit_app.py

# Terminal 3 — Fetch tweets (optional)
python -m app.twitter_etl --query "#BanarasNews -is:retweet lang:en" --max_results 50
```

API docs: http://localhost:8000/docs  
Dashboard: http://localhost:8501

---

## 🐳 Docker

```bash
docker-compose up --build
```

- API: http://localhost:8000
- Dashboard: http://localhost:8501

---

## 🧠 NLP tiers

### Tier 1 — VADER (default)
No GPU, no extra install. Good for demos and development.

### Tier 2 — Transformer (recommended for production)
```bash
# Uncomment transformers + torch in requirements.txt, then:
USE_TRANSFORMER=true uvicorn app.main:app
```
Uses `cardiffnlp/twitter-roberta-base-sentiment-latest` — purpose-built for social media text, ~20 percentage points more accurate than VADER on tweets.

### Tier 3 — Indic languages
```bash
USE_INDIC_MODEL=true uvicorn app.main:app
```
Uses `google/muril-base-cased` — supports Hindi, Tamil, Telugu, Marathi, Bengali, Gujarati, Kannada, Malayalam, Punjabi, Urdu.

---

## 📊 Audience Trust Score

The ATS is the key differentiator metric — no competitor tool offers this.

```
ATS = (positive_count − negative_count − correction_count) / total_count
```

- **> 0.3** → High trust — audience is largely satisfied
- **−0.1 to 0.3** → Moderate trust — mixed signals
- **< −0.1** → Low trust — editorial review recommended

Accessible via `GET /trust?days=30&channel=twitter`.

---

## 🧪 Tests

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

Covers: sentiment analysis unit tests, API endpoint round-trips, urgency threshold filtering, correction detection, Trust Score calculation, ETL deduplication.

---

## 🔌 API reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/healthz` | Health check |
| POST | `/token` | Get JWT token |
| POST | `/ingest_manual` | Submit feedback |
| GET | `/urgent` | High-urgency feedback |
| GET | `/corrections` | Correction requests only |
| GET | `/sentiment_summary` | Breakdown for N days |
| GET | `/trust` | Audience Trust Score |
| GET | `/docs` | Swagger UI |

---

## 🗺️ Roadmap

- [ ] Celery + Redis async ETL scheduling
- [ ] BERTopic topic clustering (`/topics` endpoint)
- [ ] WhatsApp Business API ingestion
- [ ] Journalist-level correction routing (Slack webhook)
- [ ] Alembic migrations (replace `create_all`)
- [ ] PostgreSQL full-text search on feedback
- [ ] Article URL ingestion — extract text, match corrections to claims

---

## 🧑‍💻 Author

**Ashwani Pandey**  
[GitHub: Ashwani4545](https://github.com/Ashwani4545)  
Stack: Python · FastAPI · SQLAlchemy · Streamlit · HuggingFace · Docker