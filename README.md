# Nifty 50 Multi-Agent System

An intelligent multi-agent financial assistant powered by OpenAI multimodal models, SQLite dynamic querying, query-level caching, and session memory.

## Architecture

- **Agent A (`agent_a.py`)**: Real-time ticker and market quotes fetched via Yahoo Finance (`fast_info`).
- **Agent B (`agent_b.py`)**: Historical series aggregation, in-memory Matplotlib charting to Base64, and LLM Vision trend analysis (`gpt-4o-mini`).
- **Agent C (`agent_c.py`)**: Literature retrieval agent citing principles from *Technical Analysis of the Financial Markets* by John J. Murphy.
- **Router (`router.py`)**: Few-shot classifier routing queries directly to the designated agent without unnecessary model calls.
- **Dynamic SQL Engine (`market_db.py`)**: Stores OHLCV records in SQLite and dynamically queries flexible columns (Open, High, Low, Close) and custom day windows.
- **Cache Engine (`cache.py`)**: Normalizes input query hashes and provides sub-millisecond cached responses, saving LLM tokens.
- **Session Manager (`session.py`)**: Multi-turn conversation sliding window memory.

## Setup & Running

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your-api-key"
python app.py
```
