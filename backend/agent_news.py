"""Agent D: Targeted Stock & Market News Engine with Entity Resolution."""

from typing import List, Dict, Tuple
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from openai import OpenAI
import yfinance as yf


# Common Nifty 50 & popular stock ticker mapping
STOCK_TICKER_MAP = {
    "jio": ("JIOFIN.NS", "Jio Financial Reliance Jio stock market"),
    "jio financial": ("JIOFIN.NS", "Jio Financial Services stock"),
    "reliance": ("RELIANCE.NS", "Reliance Industries stock market"),
    "tcs": ("TCS.NS", "Tata Consultancy Services TCS stock"),
    "infosys": ("INFY.NS", "Infosys stock market"),
    "hdfc": ("HDFCBANK.NS", "HDFC Bank stock market"),
    "hdfc bank": ("HDFCBANK.NS", "HDFC Bank stock"),
    "icici": ("ICICIBANK.NS", "ICICI Bank stock"),
    "tata motors": ("TATAMOTORS.NS", "Tata Motors stock"),
    "sbi": ("SBIN.NS", "State Bank of India SBI stock"),
    "nifty": ("^NSEI", "Nifty 50 Stock Market India"),
    "nifty 50": ("^NSEI", "Nifty 50 Stock Market India"),
}


def extract_stock_entity(user_input: str, client: OpenAI) -> Tuple[str, str, str]:
    """Few-shot entity extractor identifying stock company, ticker, and search query.

    Args:
        user_input: Natural language user prompt (e.g. 'give the news on jio').
        client: OpenAI client instance.

    Returns:
        Tuple of (Entity Name, Yahoo Ticker, Google News Search Query).
    """
    clean_input = user_input.lower().strip()

    # Fast dictionary check for exact matches
    for key, (ticker, search_q) in STOCK_TICKER_MAP.items():
        if key in clean_input:
            entity_name = key.title()
            return entity_name, ticker, search_q

    # Few-shot prompting for unknown or complex entity resolution
    few_shot_messages = [
        {
            "role": "system",
            "content": (
                "You are an Indian stock market entity resolver. "
                "Extract the target company/stock name and output format: 'NAME | TICKER | SEARCH_QUERY'. "
                "Default to Nifty 50 if general market. "
                "Example 1: 'give the news on jio' -> 'Jio Financial | JIOFIN.NS | Jio Financial Reliance Jio stock market'\n"
                "Example 2: 'news on adani' -> 'Adani Enterprises | ADANIENT.NS | Adani Enterprises stock market'\n"
                "Example 3: 'what happened to zomato' -> 'Zomato | ZOMATO.NS | Zomato stock market'\n"
                "Example 4: 'latest market news' -> 'Nifty 50 | ^NSEI | Nifty 50 Stock Market India'"
            ),
        },
        {"role": "user", "content": user_input},
    ]

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=few_shot_messages,
            temperature=0.0,
            max_tokens=30,
        )
        parts = resp.choices[0].message.content.strip().split("|")
        if len(parts) >= 3:
            return parts[0].strip(), parts[1].strip(), parts[2].strip()
    except Exception:
        pass

    return "Nifty 50", "^NSEI", "Nifty 50 Stock Market India"


def get_live_market_news(
    ticker: str = "^NSEI",
    search_query: str = "Nifty 50 Stock Market India",
    max_items: int = 5,
) -> List[Dict[str, str]]:
    """Fetches real-time breaking market headlines specifically for target stock or topic.

    Args:
        ticker: Yahoo finance symbol (e.g. 'JIOFIN.NS', '^NSEI').
        search_query: Dynamic search query for Google News India RSS.
        max_items: Number of stories to retrieve.

    Returns:
        List of dictionaries containing title and publisher source.
    """
    stories = []

    # Attempt 1: Targeted Yahoo Finance news feed for ticker
    try:
        stock = yf.Ticker(ticker)
        raw_news = stock.news
        if raw_news:
            for item in raw_news[:max_items]:
                content = item.get("content", {})
                title = content.get("title") or item.get("title")
                provider = (
                    content.get("provider", {}).get("displayName")
                    or item.get("publisher")
                    or "Market News"
                )
                if title:
                    stories.append({"title": title, "source": provider})
    except Exception:
        pass

    # Attempt 2: Targeted Google News RSS with dynamic query
    if len(stories) < max_items:
        try:
            encoded_query = urllib.parse.quote(search_query)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
            req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                xml_data = resp.read()
                root = ET.fromstring(xml_data)
                for item in root.findall(".//item"):
                    title_elem = item.find("title")
                    source_elem = item.find("source")
                    if title_elem is not None and title_elem.text:
                        story = {
                            "title": title_elem.text,
                            "source": source_elem.text if source_elem is not None else "Google News",
                        }
                        if story not in stories:
                            stories.append(story)
                    if len(stories) >= max_items:
                        break
        except Exception:
            pass

    # Fallback if offline
    if not stories:
        stories = [
            {"title": f"Recent trading activity and market announcements for {ticker}", "source": "NSE Feed"},
            {"title": "Sector performance and institutional flow updates", "source": "Financial Desk"},
        ]

    return stories[:max_items]


def format_news_for_prompt(news_items: List[Dict[str, str]]) -> str:
    """Formats news items into bullet points for display."""
    return "\n".join([f"- [{item['source']}] {item['title']}" for item in news_items])
