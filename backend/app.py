"""FastAPI Backend Server with 5-Year Historical Date Support & Multi-Agent Dispatch."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI

try:
    from backend.agent_a import get_current_nifty_quote
    from backend.agent_b import agent_b_chart_vision
    from backend.agent_c import AgentC
    from backend.agent_news import get_live_market_news, format_news_for_prompt
    from backend.market_db import init_database, get_nifty_by_date, query_market_sql
    from backend.router import choose_agent
except ImportError:
    from agent_a import get_current_nifty_quote
    from agent_b import agent_b_chart_vision
    from agent_c import AgentC
    from agent_news import get_live_market_news, format_news_for_prompt
    from market_db import init_database, get_nifty_by_date, query_market_sql
    from router import choose_agent

app = FastAPI(title="Nifty Multi-Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_c_instance = AgentC()


@app.on_event("startup")
def on_startup():
    """Initializes SQLite database with 5 years of historical data."""
    try:
        init_database(period="5y")
    except Exception as e:
        print(f"[Warning] Failed to initialize 5-year DB: {e}")


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"


def extract_target_date(user_input: str, client: OpenAI) -> str:
    """Extracts target historical date as 'YYYY-MM-DD' or 'yesterday'."""
    lower = user_input.lower()
    if any(w in lower for w in ["yesterday", "previous day", "last session", "yesterday's"]):
        return "yesterday"

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract the specific date requested by the user and convert to 'YYYY-MM-DD'. "
                        "If referring to yesterday, output 'yesterday'. Output ONLY the date string."
                    ),
                },
                {"role": "user", "content": user_input},
            ],
            max_tokens=15,
            temperature=0.0,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return "yesterday"


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    """Dispatches to the requested agent or retrieves historical date data."""
    user_input = req.message.strip()
    if not user_input:
        return {"reply": "Please enter a question.", "source": "error"}

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    decision = choose_agent(user_input)

    # 1. HISTORICAL SINGLE-DAY LOOKUP (Yesterday or exact date)
    if "HISTORICAL" in decision or ("yesterday" in user_input.lower() and "analysis" not in user_input.lower()):
        target_date = extract_target_date(user_input, client)
        record = get_nifty_by_date(target_date)

        if record:
            sign = "+" if record["change"] >= 0 else ""
            reply = (
                f"### Nifty 50 Historical Data: {record['date']}\n"
                f"- **Closing Price**: ₹{record['close']:,} ({sign}{record['change']} | {sign}{record['change_pct']}%)\n"
                f"- **Opening Price**: ₹{record['open']:,}\n"
                f"- **Day High**: ₹{record['high']:,}\n"
                f"- **Day Low**: ₹{record['low']:,}\n"
                f"- **Total Volume**: {record['volume']:,}\n"
                f"- **Previous Session Close**: ₹{record['previous_close']:,}\n\n"
                f"_{record['note']}_"
            )
        else:
            reply = f"Could not find historical trading data for '{target_date}'. Please specify a date within the last 5 years (e.g. 2024-06-04)."

    # 2. MULTI-DAY / 30-DAY / PERIOD ANALYSIS (Agent B + Live Quote)
    elif "AGENT_B" in decision or "analysis" in user_input.lower() or "trend" in user_input.lower():
        # Detect timeframe requested (default 1mo for 30 days, or 3mo)
        period = "1mo" if any(w in user_input.lower() for w in ["30 day", "30day", "1 month", "month", "last 30"]) else "3mo"
        
        # 1. Pull current live price from Agent A
        quote = get_current_nifty_quote("^NSEI")
        
        # 2. Pull visual & technical trend from Agent B
        trend_analysis = agent_b_chart_vision("^NSEI", period=period)
        
        reply = (
            f"### Nifty 50: Current Price & {period.upper()} Analysis\n"
            f"- **Live Price (CMP)**: ₹{quote['current_price']} ({quote['day_change_pct']}% today)\n"
            f"- **Today's Intraday Range**: Low ₹{quote['day_low']} | High ₹{quote['day_high']}\n\n"
            f"### Technical Trend Analysis (Agent B)\n"
            f"{trend_analysis}"
        )

    # 3. TRADE DECISION / ADVICE (Buy vs Sell, Call vs Put)
    elif "ADVICE" in decision:
        quote = get_current_nifty_quote("^NSEI")
        chart_analysis = agent_b_chart_vision("^NSEI", period="1mo")
        live_news = get_live_market_news("^NSEI", max_items=4)
        news_text = format_news_for_prompt(live_news)

        prompt = (
            f"User asked: '{user_input}'\n\n"
            f"LIVE INTRADAY PRICE & RANGE:\n"
            f"- Current Price: ₹{quote['current_price']}\n"
            f"- Day High (Immediate Resistance): ₹{quote['day_high']}\n"
            f"- Day Low (Immediate Support): ₹{quote['day_low']}\n"
            f"- Today's Move: {quote['day_change_pct']}%\n\n"
            f"LATEST EXTERNAL BREAKING NEWS & MACRO SENTIMENT:\n{news_text}\n\n"
            f"CHART VISUAL ANALYSIS (Agent B):\n{chart_analysis}\n\n"
            f"INSTRUCTIONS:\n"
            f"Evaluate the live price, breaking external news, and visual chart together to answer:\n"
            f"1. Directional Bias: State whether Call (CE) or Put (PE) is favored today based on news and price action.\n"
            f"2. News & Sentiment Driver: Mention which breaking news or macro cue is impacting today's move.\n"
            f"3. Call (CE) Setup: Breakout level above Day High and target.\n"
            f"4. Put (PE) Setup: Breakdown level below Day Low and target.\n"
            f"5. Key Stop-Loss: Exact risk control level."
        )

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=420,
            temperature=0.2,
        )
        reply = f"### Strategic Market Setup\n" + resp.choices[0].message.content.strip()

    # 4. LATEST BREAKING NEWS (Agent D)
    elif "AGENT_D" in decision:
        news_items = get_live_market_news("^NSEI", max_items=5)
        reply = "### Latest Nifty 50 Breaking News & Catalysts\n" + format_news_for_prompt(news_items)

    # 5. RAW LIVE QUOTE (Agent A)
    elif "AGENT_A" in decision:
        quote = get_current_nifty_quote("^NSEI")
        reply = (
            f"### Agent A - Live Quote\n"
            f"- **Nifty 50 CMP**: ₹{quote['current_price']} ({quote['day_change_pct']}% today)\n"
            f"- **Day High**: ₹{quote['day_high']}\n"
            f"- **Day Low**: ₹{quote['day_low']}"
        )

    # 6. BOOK THEORY & CONCEPTS (Agent C)
    elif "AGENT_C" in decision:
        reply = f"### Agent C - Book Theory\n" + agent_c_instance.consult_book(user_input)

    else:
        quote = get_current_nifty_quote("^NSEI")
        reply = f"### Market Status\nNifty is at ₹{quote['current_price']} ({quote['day_change_pct']}%)."

    return {"reply": reply, "source": decision}


frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
