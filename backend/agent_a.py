"""Agent A: Real-Time Market Quote Engine for Nifty 50."""

from typing import Dict, Any
import yfinance as yf


def get_current_nifty_quote(ticker: str = "^NSEI") -> Dict[str, Any]:

    """
    stock = yf.Ticker(ticker)
    info = stock.fast_info
    current_price = round(float(info.last_price), 2)


    return {
        "ticker": ticker,
        "current_price": current_price,
       
    }


if __name__ == "__main__":
    quote = get_current_nifty_quote("^NSEI")
    print(quote)
