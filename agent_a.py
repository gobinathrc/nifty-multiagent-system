"""Agent A: Real-Time Market Quote Engine for Nifty 50."""

from typing import Dict, Any
import yfinance as yf


def get_current_nifty_quote(ticker: str = "^NSEI") -> Dict[str, Any]:
    """Retrieves real-time current price and day metrics for a Nifty ticker.

    Args:
        ticker: Symbol to query ('^NSEI' for Nifty 50, or 'RELIANCE.NS').

    Returns:
        Dictionary containing current market price and daily changes.
    """
    stock = yf.Ticker(ticker)
    info = stock.fast_info
    current_price = round(float(info.last_price), 2)
    prev_close = round(float(info.previous_close), 2)

    change = round(current_price - prev_close, 2)
    change_pct = round((change / prev_close) * 100, 2)

    return {
        "ticker": ticker,
        "current_price": current_price,
        "previous_close": prev_close,
        "day_change": change,
        "day_change_pct": change_pct,
        "day_high": round(float(info.day_high), 2) if info.day_high else None,
        "day_low": round(float(info.day_low), 2) if info.day_low else None,
    }


if __name__ == "__main__":
    quote = get_current_nifty_quote("^NSEI")
    print(quote)
