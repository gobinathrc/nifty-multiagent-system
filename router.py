"""Few-Shot Agent Router for Single Agent Selection."""

from openai import OpenAI


def choose_agent(user_input: str, model: str = "gpt-4o-mini") -> str:
    """Uses few-shot prompting to classify user intent into AGENT_A, AGENT_B, or AGENT_C.

    Args:
        user_input: The user query string.
        model: OpenAI model name.

    Returns:
        AGENT_A, AGENT_B, or AGENT_C.
    """
    client = OpenAI()
    few_shot_messages = [
        {
            "role": "system",
            "content": (
                "You are an intent router. Classify the user query into exactly ONE choice:\n"
                "- AGENT_A: For live current price, ticker quote, or daily change.\n"
                "- AGENT_B: For visual chart trends, graphs, patterns, or plot analysis.\n"
                "- AGENT_C: For book rules, trading theory, definitions, or textbook concepts.\n"
                "Output ONLY the token: AGENT_A, AGENT_B, or AGENT_C."
            ),
        },
        {"role": "user", "content": "What is the current price of Nifty today?"},
        {"role": "assistant", "content": "AGENT_A"},
        {"role": "user", "content": "Can you plot and analyze the 3-month chart for Nifty?"},
        {"role": "assistant", "content": "AGENT_B"},
        {"role": "user", "content": "What does Murphy's book say about head and shoulders patterns?"},
        {"role": "assistant", "content": "AGENT_C"},
        {"role": "user", "content": user_input},
    ]

    resp = client.chat.completions.create(
        model=model,
        messages=few_shot_messages,
        temperature=0.0,
        max_tokens=10,
    )
    return resp.choices[0].message.content.strip().upper()
