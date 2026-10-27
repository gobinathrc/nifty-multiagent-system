"""Few-Shot Agent Router with Dedicated Strategy Decision Routing."""

from openai import OpenAI


def choose_agent(user_input: str, model: str = "gpt-4o-mini") -> str:
    """Uses few-shot prompting to classify user intent into:
    - AGENT_A: Raw current price, ticker quote, or daily change.
    - AGENT_B: Visual chart trends, graphs, patterns, or plot analysis.
    - AGENT_C: Book rules, trading theory, definitions, or textbook concepts.
    - STRATEGY: Trade direction (Buy vs Sell, Call vs Put), market outlook, or actionable setups.

    Args:
        user_input: The user query string.
        model: OpenAI model name.

    Returns:
        AGENT_A, AGENT_B, AGENT_C, or STRATEGY.
    """
    client = OpenAI()
    few_shot_messages = [
        {
            "role": "system",
            "content": (
                "You are an intent router for a Nifty 50 market system. Classify the user query into exactly ONE token:\n"
                "- AGENT_A: When the user only asks for the current price, quote, CMP, or daily high/low.\n"
                "- AGENT_B: When the user explicitly asks to plot, view, or analyze the chart/graph.\n"
                "- AGENT_C: When the user asks about textbook definitions, trading books, or indicators theory.\n"
                "- STRATEGY: When the user asks 'should I buy or sell', 'call or put', trade direction, or market decision.\n"
                "Output ONLY one token: AGENT_A, AGENT_B, AGENT_C, or STRATEGY."
            ),
        },
        {"role": "user", "content": "What is the current price of Nifty?"},
        {"role": "assistant", "content": "AGENT_A"},
        {"role": "user", "content": "Show me the 3-month chart and visual trend."},
        {"role": "assistant", "content": "AGENT_B"},
        {"role": "user", "content": "What does John Murphy say about moving averages?"},
        {"role": "assistant", "content": "AGENT_C"},
        {"role": "user", "content": "should i buy ninfty toady should i call or put"},
        {"role": "assistant", "content": "STRATEGY"},
        {"role": "user", "content": "should i buy or sell nifty"},
        {"role": "assistant", "content": "STRATEGY"},
        {"role": "user", "content": "is nifty bullish or bearish for options today?"},
        {"role": "assistant", "content": "STRATEGY"},
        {"role": "user", "content": user_input},
    ]

    resp = client.chat.completions.create(
        model=model,
        messages=few_shot_messages,
        temperature=0.0,
        max_tokens=10,
    )
    return resp.choices[0].message.content.strip().upper()
