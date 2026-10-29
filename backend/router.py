"""Few-Shot Agent Router with Historical Date Support."""

from openai import OpenAI


def choose_agent(user_input: str, model: str = "gpt-4o-mini") -> str:
    """Classifies user query into AGENT_A, AGENT_B, AGENT_C, AGENT_D, HISTORICAL, or ADVICE."""
    client = OpenAI()
    few_shot_messages = [
        {
            "role": "system",
            "content": (
                "Classify user query into exactly ONE token:\n"
                "- AGENT_A: When asking for current live price, CMP, or today's tick numbers.\n"
                "- AGENT_B: When asking to see or analyze a chart, graph, or visual plot.\n"
                "- AGENT_C: When asking about textbook rules, definitions, indicators.\n"
                "- AGENT_D: When asking for latest breaking news, market headlines, or macro events.\n"
                "- HISTORICAL: When asking for yesterday's price, historical dates, or past 5-year values.\n"
                "- ADVICE: When asking 'should I buy or sell', 'call or put', or trade decisions.\n"
                "Output ONLY the token: AGENT_A, AGENT_B, AGENT_C, AGENT_D, HISTORICAL, or ADVICE."
            ),
        },
        {"role": "user", "content": "What is the current price of Nifty right now?"},
        {"role": "assistant", "content": "AGENT_A"},
        {"role": "user", "content": "Show me the 3-month chart and visual trend."},
        {"role": "assistant", "content": "AGENT_B"},
        {"role": "user", "content": "What does Murphy's book say about moving averages?"},
        {"role": "assistant", "content": "AGENT_C"},
        {"role": "user", "content": "What is the latest market news on Nifty today?"},
        {"role": "assistant", "content": "AGENT_D"},
        {"role": "user", "content": "what was nifty value yesterday?"},
        {"role": "assistant", "content": "HISTORICAL"},
        {"role": "user", "content": "what was nifty close on 4th june 2024?"},
        {"role": "assistant", "content": "HISTORICAL"},
        {"role": "user", "content": "show me nifty price on 2023-01-15"},
        {"role": "assistant", "content": "HISTORICAL"},
        {"role": "user", "content": "should i buy ninfty toady should i call or put"},
        {"role": "assistant", "content": "ADVICE"},
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
