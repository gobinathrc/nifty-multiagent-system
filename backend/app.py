"""Main Application: Multi-Agent Nifty System with Dynamic SQL, Caching, and Session History."""

import json
import re
from openai import OpenAI

from agent_a import get_current_nifty_quote
from agent_b import agent_b_chart_vision
from agent_c import AgentC
from cache import ResponseCache
from market_db import init_database, query_market_sql
from router import choose_agent
from session import SessionManager

client = OpenAI()
query_cache = ResponseCache(ttl_seconds=1800)
session_mgr = SessionManager(max_history_turns=5)
agent_c_instance = AgentC()


def extract_sql_params(user_input: str) -> tuple[str, int]:
    """Extracts column (open/close/high/low) and days count from text."""
    column = "close"
    if "open" in user_input.lower():
        column = "open"
    elif "high" in user_input.lower():
        column = "high"
    elif "low" in user_input.lower():
        elif_vol = "volume"
        if elif_vol in user_input.lower():
            column = elif_vol

    match = re.search(r"(\d+)\s*day", user_input.lower())
    days = int(match.group(1)) if match else 7
    return column, days


def run_chatbot_turn(user_input: str, session_id: str = "default_user", model: str = "gpt-4o-mini") -> str:
    """Processes a user message via Cache -> Intent Router -> Agent/SQL -> LLM."""
    # 1. Cache Check
    cached = query_cache.get(user_input)
    if cached:
        return f"[CACHE HIT]\n{cached}"

    # 2. Intent Routing
    decision = choose_agent(user_input, model=model)

    if "AGENT_A" in decision:
        quote = get_current_nifty_quote("^NSEI")
        reply = f"[Agent A - Live Quote] Nifty: ₹{quote['current_price']} ({quote['day_change_pct']}%)"

    elif "AGENT_B" in decision:
        reply = f"[Agent B - Vision Plot]\n{agent_b_chart_vision('^NSEI', model=model)}"

    elif "AGENT_C" in decision:
        reply = f"[Agent C - Book Rules]\n{agent_c_instance.consult_book(user_input, model=model)}"

    else:
        # Default SQL Historical Query
        col, days = extract_sql_params(user_input)
        sql_rows = query_market_sql(column=col, days=days)
        session_mgr.add_user_message(session_id, user_input)
        hist = session_mgr.get_history(session_id)

        prompt_sys = (
            f"You are a Nifty Market Analyst. Here is recent data ({col.upper()} for {days} days):\n"
            f"{json.dumps(sql_rows)}\nAnswer the user based on this data."
        )
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": prompt_sys}] + hist,
            max_tokens=300,
        )
        reply = resp.choices[0].message.content.strip()
        session_mgr.add_assistant_message(session_id, reply)

    # 3. Store to Cache
    query_cache.set(user_input, reply)
    return reply


if __name__ == "__main__":
    init_database()
    print("Nifty Multi-Agent System Initialized.")
    print(run_chatbot_turn("What is the current live price of Nifty?"))
