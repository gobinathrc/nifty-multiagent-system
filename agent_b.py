"""Agent B: Historical Data, In-Memory Plotting, and Multimodal Vision Analysis."""

import base64
import io
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from openai import OpenAI
import yfinance as yf


def agent_b_chart_vision(ticker: str = "^NSEI", model: str = "gpt-4o-mini") -> str:
    """Agent B: Computes 3-month stats, plots to Base64 in RAM, and analyzes visually.

    Args:
        ticker: Symbol to query.
        model: OpenAI model name.

    Returns:
        Visual technical analysis text.
    """
    df = yf.download(ticker, period="3mo", progress=False)
    stats = df["Close"].describe().round(2).to_dict()

    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.plot(df.index, df["Close"], color="#2563EB", linewidth=2)
    ax.set_title(f"{ticker} 3-Month Trend")
    ax.grid(True)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    b64_chart = base64.b64encode(buf.getvalue()).decode("utf-8")

    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Analyze technical trend for {ticker}. Stats: {stats}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_chart}"}},
                ],
            }
        ],
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    print(agent_b_chart_vision("^NSEI"))
