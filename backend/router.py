"""Few-Shot Agent Router with Decision Support and News Categorization."""

from openai import OpenAI


def choose_agent(user_input: str, model: str = "gpt-4o-mini") -> str:
    """Classifies user query into AGENT_A, AGENT_B, AGENT_C, AGENT_D, or ADVICE."""
    client = OpenAI()
    few_shot_messages = [
        {
            "role": "system",
            "content": (
                "Classify user query into exactly ONE token:\n"
                "- AGENT_A: Only asking for live current price/quote/numbers.\n"
                "- AGENT_B: Asking to see or analyze chart/graph/trend.\n"
                "- AGENT_C: Asking about book rules, definitions, indicators.\n"
                "- AGENT_D: Asking for latest breaking news, market headlines, or macro events.\n"
                "- ADVICE: Asking 'should I buy or sell', 'call or put', or trade decisions.\n"
                "Output ONLY the token: AGENT_A, AGENT_B, AGENT_C, AGENT_D, or ADVICE."
            ),
        },
        {"role": "user", "content": "What is the current price of Nifty today?"},
        {"role": "assistant", "content": "AGENT_A"},
        {"role": "user", "content": "Can you plot and analyze the 3-month chart for Nifty?"},
        {"role": "assistant", "content": "AGENT_B"},
        {"role": "user", "content": "What does Murphy's book say about moving averages?"},
        {"role": "assistant", "content": "AGENT_C"},
        {"role": "user", "content": "What is the latest market news on Nifty today?"},
        {"role": "assistant", "content": "AGENT_D"},
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
