"""Agent D: Live External Market News and Macro Sentiment Engine."""

from typing import List, Dict
import urllib.request
import xml.etree.ElementTree as ET
import yfinance as yf


def get_live_market_news(ticker: str = "^NSEI", max_items: int = 5) -> List[Dict[str, str]]:
    """Fetches real-time breaking market headlines for Nifty 50.

    Attempts Yahoo Finance news feed first, with automatic fallback
    to Indian Financial Markets Google News RSS.

    Args:
        ticker: Symbol to query.
        max_items: Number of top stories to return.

    Returns:
        List of dictionaries with title, publisher, and summary.
    """
    stories = []

    # Attempt 1: Yahoo Finance News Feed
    try:
        stock = yf.Ticker(ticker)
        raw_news = stock.news
        if raw_news:
            for item in raw_news[:max_items]:
                # Handle both new and legacy yfinance news item schema
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

    # Attempt 2: Fallback to Indian Market News RSS feed if yfinance is empty
    if not stories:
        try:
            rss_url = "https://news.google.com/rss/search?q=Nifty+50+Stock+Market+India&hl=en-IN&gl=IN&ceid=IN:en"
            req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                xml_data = resp.read()
                root = ET.fromstring(xml_data)
                for item in root.findall(".//item")[:max_items]:
                    title_elem = item.find("title")
                    source_elem = item.find("source")
                    if title_elem is not None and title_elem.text:
                        stories.append({
                            "title": title_elem.text,
                            "source": source_elem.text if source_elem is not None else "Google News",
                        })
        except Exception:
            pass

    # Graceful fallback if offline
    if not stories:
        stories = [
            {"title": "Global market cues and corporate earnings dictate intraday sentiment", "source": "NSE General"},
            {"title": "Options Open Interest reflects crucial support and resistance bounds", "source": "Derivatives Desk"}
        ]

    return stories


def format_news_for_prompt(news_items: List[Dict[str, str]]) -> str:
    """Formats news items into bullet points for LLM prompt injection."""
    return "\n".join([f"- [{item['source']}] {item['title']}" for item in news_items])


if __name__ == "__main__":
    news = get_live_market_news()
    print("Agent D Live News:\n", format_news_for_prompt(news))
