"""FastAPI Backend Server for Render Hosting with Strategy Decision Engine."""

from contextlib import asynccontextmanager
import json
import os
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI

try:
    from backend.agent_a import get_current_nifty_quote
    from backend.agent_b import agent_b_chart_vision
    from backend.agent_c import AgentC
    from backend.cache import ResponseCache
    from backend.market_db import init_database, query_market_sql
    from backend.router import choose_agent
    from backend.session import SessionManager
except ImportError:
    from agent_a import get_current_nifty_quote
    from agent_b import agent_b_chart_vision
    from agent_c import AgentC
    from cache import ResponseCache
    from market_db import init_database, query_market_sql
    from router import choose_agent
    from session import SessionManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes SQLite historical market database on startup."""
    try:
        init_database()
    except Exception as e:
        print(f"[Warning] DB initialization skipped or failed: {e}")
    yield


app = FastAPI(title="Nifty Multi-Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

query_cache = ResponseCache(ttl_seconds=900)
session_mgr = SessionManager(max_history_turns=5)
agent_c_instance = AgentC()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"


def extract_sql_params(text: str) -> tuple[str, int]:
    """Parses column and lookback days from natural language."""
    column = "close"
    if "open" in text.lower():
        column = "open"
    elif "high" in text.lower():
        column = "high"
    elif "low" in text.lower():
        column = "low"
    elif "volume" in text.lower():
        column = "volume"

    match = re.search(r"(\d+)\s*day", text.lower())
    days = int(match.group(1)) if match else 7
    return column, days


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    """Unified API endpoint routing queries to Agent A, B, C, or STRATEGY synthesis."""
    user_input = req.message.strip()
    if not user_input:
        return {"reply": "Please enter a question.", "source": "error"}

    # 1. Cache hit check
    cached = query_cache.get(user_input)
    if cached:
        return {"reply": cached, "source": "cache"}

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # 2. Intent routing
    decision = choose_agent(user_input)

    # CASE 1: STRATEGY (Buy vs Sell / Call vs Put / Market Decision)
    if "STRATEGY" in decision:
        quote = get_current_nifty_quote("^NSEI")
        chart_analysis = agent_b_chart_vision("^NSEI")
        book_rule = agent_c_instance.consult_book(
            "Rules for buying Call options versus Put options based on intraday high/low breakouts and trend support"
        )

        strategy_prompt = f"""
You are a Senior Quantitative Market Strategist for Indian Equities (NSE/Nifty 50).
The user is asking: "{user_input}"

Here is real-time market data from your specialist agents:
- LIVE INTRADAY METRICS (Agent A):
  * Current Price: ₹{quote['current_price']}
  * Day High (Immediate Resistance): ₹{quote['day_high']}
  * Day Low (Immediate Support): ₹{quote['day_low']}
  * Today's Change: {quote['day_change_pct']}%

- 3-MONTH CHART & VISUAL TREND (Agent B):
{chart_analysis}

- TECHNICAL ANALYSIS LITERATURE & RULES (Agent C - John J. Murphy):
{book_rule}

TASK:
Directly answer whether the market bias favors BUY (Call/CE) or SELL (Put/PE):
1. **Executive Bias**: State clearly whether bias is Bullish (Call), Bearish (Put), or Neutral/Range-Bound.
2. **Call (CE) Setup**: Specific breakout level (e.g. above Day High ₹{quote['day_high']}) and target.
3. **Put (PE) Setup**: Specific breakdown level (e.g. below Day Low ₹{quote['day_low']}) and target.
4. **Key Risk & Stop-Loss Level**: Based on today's range.

Keep it concise, actionable, and structured with bullet points.
"""
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": strategy_prompt}],
            max_tokens=450,
            temperature=0.2,
        )
        reply = f"[Strategic Market Setup]\n" + resp.choices[0].message.content.strip()

    # CASE 2: AGENT A (Raw Price / Ticker Quote)
    elif "AGENT_A" in decision:
        quote = get_current_nifty_quote("^NSEI")
        reply = (
            f"[Agent A - Live Quote]\n"
            f"Nifty 50: ₹{quote['current_price']} ({quote['day_change_pct']}% today)\n"
            f"High: ₹{quote['day_high']} | Low: ₹{quote['day_low']}"
        )

    # CASE 3: AGENT B (Explicit Chart/Plot Request)
    elif "AGENT_B" in decision:
        reply = f"[Agent B - Vision Plot]\n{agent_b_chart_vision('^NSEI')}"

    # CASE 4: AGENT C (Textbook & Literature Concepts)
    elif "AGENT_C" in decision:
        reply = f"[Agent C - Book Theory]\n{agent_c_instance.consult_book(user_input)}"

    # CASE 5: DYNAMIC SQL FALLBACK
    else:
        col, days = extract_sql_params(user_input)
        sql_rows = query_market_sql(column=col, days=days)
        session_mgr.add_user_message(req.session_id, user_input)
        hist = session_mgr.get_history(req.session_id)

        prompt_sys = (
            f"You are a Nifty Market Analyst. Here is recent {col.upper()} data for {days} days:\n"
            f"{json.dumps(sql_rows)}\nAnswer the user based on this data."
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt_sys}] + hist,
            max_tokens=300,
        )
        reply = resp.choices[0].message.content.strip()
        session_mgr.add_assistant_message(req.session_id, reply)

    query_cache.set(user_input, reply)
    return {"reply": reply, "source": decision}


# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
