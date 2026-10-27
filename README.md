# Nifty 50 Multi-Agent System

An autonomous financial intelligence platform with decoupled **backend** (agents, SQLite, caching, session memory) and **frontend** (glassmorphic UI).

## Folder Structure

```
nifty_multiagent_system/
├── backend/
│   ├── agent_a.py        # Live price & ticker quote engine (Yahoo Finance)
│   ├── agent_b.py        # In-memory plotting to Base64 + LLM Vision (gpt-4o-mini)
│   ├── agent_c.py        # Literature/book rule retrieval (John J. Murphy)
│   ├── router.py         # Few-shot intent router (Agent A / B / C selector)
│   ├── market_db.py      # SQLite storage & dynamic SQL engine (Open/Close, N days)
│   ├── cache.py          # Normalized query cache (Zero token waste)
│   ├── session.py        # Multi-turn conversation sliding window
│   ├── app.py            # Main application runner & orchestration
│   └── requirements.txt  # Backend Python dependencies
├── frontend/
│   ├── index.html        # Glassmorphic responsive dashboard
│   ├── styles.css        # Google Antigravity dark glass theme
│   └── app.js            # Client-side agent interaction logic
├── .gitignore
└── README.md
```

## Running the Project

### 1. Backend
```bash
cd backend
pip install -r requirements.txt
export OPENAI_API_KEY="your-api-key"
python app.py
```

### 2. Frontend
Open `frontend/index.html` directly in your browser or serve using:
```bash
cd frontend
python -m http.server 3000
```
