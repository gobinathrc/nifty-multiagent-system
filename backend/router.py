"""Few-Shot Agent Router with Period Analysis and Targeted News Support."""

from openai import OpenAI


def choose_agent(user_input: str, model: str = "gpt-4o-mini") -> str:
    """Classifies user query into AGENT_A, AGENT_B, AGENT_C, AGENT_D, HISTORICAL, or ADVICE."""
    client = OpenAI()
    few_shot_messages = [
        {
            "role": "system",
            "content": (
                "Classify user query into exactly ONE token:\n"
                "- AGENT_A: Only asking for current price, live CMP, or today's tick numbers.\n"
                "- AGENT_B: Asking for trend analysis, 30-day/multi-day analysis, charts, or visual plots.\n"
                "- AGENT_C: Asking about textbook rules, definitions, indicators.\n"
                "- AGENT_D: Asking for news, headlines, catalysts, or events for Nifty or any stock (e.g. Jio, Reliance, TCS).\n"
                "- HISTORICAL: Asking for yesterday's price or a specific single past date (e.g. 2024-06-04).\n"
                "- ADVICE: Asking 'should I buy or sell', 'call or put', or trade decisions.\n"
                "Output ONLY the token: AGENT_A, AGENT_B, AGENT_C, AGENT_D, HISTORICAL, or ADVICE."
            ),
        },
        {"role": "user", "content": "What is the current price of Nifty right now?"},
        {"role": "assistant", "content": "AGENT_A"},
        {"role": "user", "content": "give the news on jio"},
        {"role": "assistant", "content": "AGENT_D"},
        {"role": "user", "content": "what is happening with reliance news today?"},
        {"role": "assistant", "content": "AGENT_D"},
        {"role": "user", "content": "any breaking news on tata motors?"},
        {"role": "assistant", "content": "AGENT_D"},
        {"role": "user", "content": "What is the latest market news on Nifty today?"},
        {"role": "assistant", "content": "AGENT_D"},
        {"role": "user", "content": "give nifty 50 analysis of last 30 days"},
        {"role": "assistant", "content": "AGENT_B"},
        {"role": "user", "content": "analyze nifty trend for the past month"},
        {"role": "assistant", "content": "AGENT_B"},
        {"role": "user", "content": "Show me the 3-month chart and visual trend."},
        {"role": "assistant", "content": "AGENT_B"},
        {"role": "user", "content": "What does Murphy's book say about moving averages?"},
        {"role": "assistant", "content": "AGENT_C"},
        {"role": "user", "content": "what was nifty value yesterday?"},
        {"role": "assistant", "content": "HISTORICAL"},
        {"role": "user", "content": "should i buy or sell nifty"},
        {"role": "assistant", "content": "ADVICE"},
        {"role": "user", "content": user_input},
    ]

    resp = client.chat.completions.create(
        model=model,
        messages=few_shot_messages,
        temperature=0.0,
        max_tokens=10,
    )
    return resp.choices[0].message.content.strip().upper()
