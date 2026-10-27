"""SQLite Market Database and Dynamic SQL Query Engine."""

import sqlite3
from typing import Dict, Any, List
import pandas as pd
import yfinance as yf

DB_PATH = "nifty_market.db"


def init_database(ticker: str = "^NSEI", period: str = "1y") -> None:
    """Fetches historical OHLCV data and stores it in SQLite."""
    df = yf.download(ticker, period=period, interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nifty_ohlcv (
            date TEXT PRIMARY KEY,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER
        )
    """)

    records = [
        (row["Date"], round(float(row["Open"]), 2), round(float(row["High"]), 2),
         round(float(row["Low"]), 2), round(float(row["Close"]), 2), int(row["Volume"]))
        for _, row in df.iterrows()
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO nifty_ohlcv (date, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?)
    """, records)

    conn.commit()
    conn.close()


def query_market_sql(column: str = "close", days: int = 7) -> List[Dict[str, Any]]:
    """Executes dynamic SQL queries for any metric over N days."""
    valid_cols = {"open", "high", "low", "close", "volume"}
    col_clean = column.lower().strip()
    if col_clean not in valid_cols:
        col_clean = "close"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    sql = f"SELECT date, {col_clean} FROM nifty_ohlcv ORDER BY date DESC LIMIT ?"
    cursor.execute(sql, (days,))
    rows = cursor.fetchall()
    conn.close()

    rows.reverse()
    return [{"date": r[0], col_clean: r[1]} for r in rows]
