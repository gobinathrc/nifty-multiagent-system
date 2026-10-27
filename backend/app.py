"""FastAPI Backend Server with News-Grounded Trade Strategy & Clean Formatting."""

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
    from backend.router import choose_agent
except ImportError:
    from agent_a import get_current_nifty_quote
    from agent_b import agent_b_chart_vision
    from agent_c import AgentC
    from agent_news import get_live_market_news, format_news_for_prompt
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


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    """Dispatches to the requested agent or generates news-grounded trading advice."""
    user_input = req.message.strip()
    if not user_input:
        return {"reply": "Please enter a question.", "source": "error"}

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    decision = choose_agent(user_input)

    # 1. TRADE DECISION / ADVICE (Buy vs Sell, Call vs Put)
    if "ADVICE" in decision:
        quote = get_current_nifty_quote("^NSEI")
        chart_analysis = agent_b_chart_vision("^NSEI")
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

    # 2. LATEST BREAKING NEWS (Agent D)
    elif "AGENT_D" in decision:
        news_items = get_live_market_news("^NSEI", max_items=5)
        reply = "### Latest Nifty 50 Breaking News & Catalysts\n" + format_news_for_prompt(news_items)

    # 3. RAW LIVE QUOTE (Agent A)
    elif "AGENT_A" in decision:
        quote = get_current_nifty_quote("^NSEI")
        reply = (
            f"### Agent A - Live Quote\n"
            f"- **Nifty 50 CMP**: ₹{quote['current_price']} ({quote['day_change_pct']}% today)\n"
            f"- **Day High**: ₹{quote['day_high']}\n"
            f"- **Day Low**: ₹{quote['day_low']}"
        )

    # 4. VISUAL CHART ANALYSIS (Agent B)
    elif "AGENT_B" in decision:
        reply = f"### Agent B - Vision Plot\n" + agent_b_chart_vision("^NSEI")

    # 5. BOOK THEORY & CONCEPTS (Agent C)
    elif "AGENT_C" in decision:
        reply = f"### Agent C - Book Theory\n" + agent_c_instance.consult_book(user_input)

    else:
        quote = get_current_nifty_quote("^NSEI")
        reply = f"### Market Status\nNifty is at ₹{quote['current_price']} ({quote['day_change_pct']}%)."

    return {"reply": reply, "source": decision}


# Mount frontend static UI
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
