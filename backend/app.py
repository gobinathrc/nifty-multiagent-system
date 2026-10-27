"""FastAPI Backend Server with Clean Multi-Agent Dispatch and Trade Advice."""

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
    from backend.router import choose_agent
except ImportError:
    from agent_a import get_current_nifty_quote
    from agent_b import agent_b_chart_vision
    from agent_c import AgentC
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
    """Dispatches to the requested agent or generates strategic trading advice."""
    user_input = req.message.strip()
    if not user_input:
        return {"reply": "Please enter a question.", "source": "error"}

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    decision = choose_agent(user_input)

    # 1. TRADE DECISION / ADVICE (Buy vs Sell, Call vs Put)
    if "ADVICE" in decision:
        quote = get_current_nifty_quote("^NSEI")
        chart_analysis = agent_b_chart_vision("^NSEI")

        prompt = (
            f"User asked: '{user_input}'\n\n"
            f"LIVE MARKET DATA:\n"
            f"- Current Price: ₹{quote['current_price']}\n"
            f"- Day High: ₹{quote['day_high']}\n"
            f"- Day Low: ₹{quote['day_low']}\n"
            f"- Change: {quote['day_change_pct']}%\n\n"
            f"CHART VISUAL ANALYSIS:\n{chart_analysis}\n\n"
            f"Provide a direct technical trading answer:\n"
            f"1. Directional Bias: (Is Call/CE or Put/PE favored?)\n"
            f"2. Call (CE) Entry Setup: Breakout level and target.\n"
            f"3. Put (PE) Entry Setup: Breakdown level and target.\n"
            f"4. Key Stop-Loss: Exact level based on today's range."
        )

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=350,
            temperature=0.2,
        )
        reply = f"[Strategic Market Setup]\n" + resp.choices[0].message.content.strip()

    # 2. RAW LIVE QUOTE (Agent A)
    elif "AGENT_A" in decision:
        quote = get_current_nifty_quote("^NSEI")
        reply = (
            f"[Agent A - Live Quote]\n"
            f"Nifty 50: ₹{quote['current_price']} ({quote['day_change_pct']}% today)\n"
            f"High: ₹{quote['day_high']} | Low: ₹{quote['day_low']}"
        )

    # 3. VISUAL CHART ANALYSIS (Agent B)
    elif "AGENT_B" in decision:
        reply = f"[Agent B - Vision Plot]\n{agent_b_chart_vision('^NSEI')}"

    # 4. BOOK THEORY & CONCEPTS (Agent C)
    elif "AGENT_C" in decision:
        reply = f"[Agent C - Book Theory]\n{agent_c_instance.consult_book(user_input)}"

    else:
        quote = get_current_nifty_quote("^NSEI")
        reply = f"[Agent A - Live Quote] Nifty: ₹{quote['current_price']} ({quote['day_change_pct']}%)"

    return {"reply": reply, "source": decision}


# Mount frontend static UI
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
