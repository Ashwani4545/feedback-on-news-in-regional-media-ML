# 📘 Regional Newsroom Feedback System (AI + Twitter/X Integration)

---

# 📰 Overview

This project aims to analyze audience feedback for regional news outlets using AI/ML techniques.
It collects audience reactions from multiple channels — especially Twitter/X — and generates actionable insights to improve content relevance, credibility, and community trust.

The system automatically:
• Fetches tweets via Twitter/X API (v2)
• Analyzes sentiment, urgency, and correction indicators using NLP
• Stores and manages data in a structured SQL database
• Displays insights through an interactive Streamlit dashboard

---

# ⚙️ Features
```
✅ Collect regional news feedback via Twitter/X APIs
✅ Store structured feedback using SQLAlchemy + SQLite
✅ Perform sentiment & urgency analysis (VADER NLP)
✅ RESTful Flask backend APIs
✅ Streamlit dashboard for visualization
✅ Optional Dockerized environment
✅ CI-ready with GitHub Actions
```
---

# 🧰 Tech Stack
```
Layer Technology

Backend Python (Flask)

NLP/ML NLTK (VADER), scikit-learn

Database SQLite (upgradeable to MySQL/PostgreSQL)

Frontend Streamlit

External APIs Twitter/X API v2

CI/CD GitHub Actions

Deployment Docker, Docker Compose
```
---

# 🧩 Folder Structure
```
regional_feedback_full/
│
├── app/
│ ├── main.py # Flask API server
│ ├── twitter_etl.py # Fetch feedback from Twitter/X
│ ├── analysis.py # NLP-based sentiment and correction detection
│ ├── database.py # SQLAlchemy models and DB initialization
│
├── dashboard/
│ └── streamlit_app.py # Streamlit dashboard
│
├── tests/ # Unit tests
|
├── .github/workflows/ci.yml # GitHub Actions workflow
├── docker-compose.yml # Multi-service (API + dashboard)
├── Dockerfile
├── requirements.txt
├── .env.example
├── LICENSE
└── README.md
```
---
# 🧱 Environment Setup

1️⃣ Clone or Unzip Project
```
unzip regional_feedback_full.zip
cd regional_feedback_full
```

2️⃣ Create Virtual Environment
```
Windows:
python -m venv venv
venv\Scripts\activate
macOS / Linux:
python3 -m venv venv
source venv/bin/activate
```

3️⃣ Install Dependencies
```
pip install -r requirements.txt
```

4️⃣ Configure Environment Variables
```
Copy and edit the .env file:
cp .env.example .env
Then open .env and set your credentials:
TWITTER_BEARER_TOKEN=your_actual_twitter_api_bearer_token
DATABASE_URL=sqlite:///./data/feedback.db
API_PORT=8000
```
---

# 🗃️ Database Initialization

python -m app.database

---

# 🚀 Run the Application

▶️ Run Flask API
```
python -m app.main
Access it at: http://localhost:8000
```

▶️ Fetch Tweets from Twitter/X
```
Open another terminal and run:
python -m app.twitter_etl --query "#BanarasNews -is:retweet lang:en"
```
---

📊 Open Streamlit Dashboard

streamlit run dashboard/streamlit_app.py
Dashboard URL → http://localhost:8501
You can:
• View urgent or corrective feedback posts
• Inspect sentiment analysis results
• Track new audience reactions

---

🐳 Docker Setup (Optional)

If you prefer running everything in containers:
docker-compose up --build
This will launch:
• Flask API: http://localhost:8000
• Streamlit Dashboard: http://localhost:8501

---

🧪 Run Tests

pytest -q

---

# 🧠 Example API Request

curl -X POST http://localhost:8000/ingest_manual \
 -H "Content-Type: application/json" \
 -d '{"raw_text": "Please correct the statistics in today’s report", "channel": "email"}'

---

# 🧾 Future Enhancements

• Advanced topic classification (TF-IDF + Logistic Regression)
• Multi-channel integration (YouTube, Facebook)
• Role-based authentication for newsroom staff
• Data visualization enhancements (word clouds, timelines)

---

# 🧑‍💻 Maintainer

Developed by: Ashwani Pandey
Tech Stack: Python · Flask · SQLAlchemy · Streamlit · Docker · Twitter API
