"""SQLite Market Database and 5-Year Dynamic SQL Query Engine."""

from datetime import datetime, timedelta
import sqlite3
from typing import Dict, Any, List, Optional
import pandas as pd
import yfinance as yf

DB_PATH = "nifty_market.db"


def init_database(ticker: str = "^NSEI", period: str = "5y") -> None:
    """Fetches 5 years of historical OHLCV data and stores it in SQLite.

    Why: 5-year lookback enables instant querying of any past date,
    including yesterday, specific election/budget days, and multi-year comparisons.
    """
    df = yf.download(ticker, period=period, interval="1d", progress=False)
    if df.empty:
        print(f"[Warning] No data retrieved for {ticker}")
        return

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

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
        (
            row["Date"],
            round(float(row["Open"]), 2),
            round(float(row["High"]), 2),
            round(float(row["Low"]), 2),
            round(float(row["Close"]), 2),
            int(row["Volume"]) if pd.notna(row["Volume"]) else 0,
        )
        for _, row in df.iterrows()
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO nifty_ohlcv (date, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?)
    """, records)

    conn.commit()
    conn.close()
    print(f"[DB] Initialized '{DB_PATH}' with {len(records)} records (5-year historical depth).")


def get_nifty_by_date(date_str: str = "yesterday") -> Optional[Dict[str, Any]]:
    """Retrieves full OHLCV and daily % change for yesterday or any specific date.

    Args:
        date_str: Target date string ('yesterday', 'YYYY-MM-DD', or natural date).

    Returns:
        Structured record containing OHLCV, day change, and trading day context.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    is_yesterday_query = date_str.lower().strip() in (
        "yesterday",
        "prev",
        "previous",
        "last session",
        "yesterday's",
    )

    if is_yesterday_query:
        # Fetch the two most recent recorded trading sessions
        cursor.execute("""
            SELECT date, open, high, low, close, volume 
            FROM nifty_ohlcv 
            ORDER BY date DESC 
            LIMIT 2
        """)
        rows = cursor.fetchall()
        if not rows:
            conn.close()
            return None

        # Determine if the topmost row is today or the last closed day
        today_str = datetime.now().strftime("%Y-%m-%d")
        if rows[0][0] == today_str and len(rows) > 1:
            target_row = rows[1]
            prev_close = rows[1][4]
        else:
            # Last available session is yesterday's trading close
            target_row = rows[0]
            # Fetch the session prior to target_row for % change calculation
            cursor.execute(
                "SELECT close FROM nifty_ohlcv WHERE date < ? ORDER BY date DESC LIMIT 1",
                (target_row[0],),
            )
            prev_row = cursor.fetchone()
            prev_close = prev_row[0] if prev_row else target_row[1]

        actual_date = target_row[0]
        note = "Yesterday's official trading session"
        is_exact = True

    else:
        # Specific date lookup (e.g. '2024-06-04')
        cursor.execute(
            "SELECT date, open, high, low, close, volume FROM nifty_ohlcv WHERE date = ?",
            (date_str,),
        )
        target_row = cursor.fetchone()

        if target_row:
            actual_date = target_row[0]
            note = "Exact trading session match"
            is_exact = True
        else:
            # If weekend or market holiday, fetch the closest preceding trading session
            cursor.execute(
                """
                SELECT date, open, high, low, close, volume 
                FROM nifty_ohlcv 
                WHERE date <= ? 
                ORDER BY date DESC 
                LIMIT 1
                """,
                (date_str,),
            )
            target_row = cursor.fetchone()
            if not target_row:
                conn.close()
                return None
            actual_date = target_row[0]
            note = f"Market was closed on {date_str} (weekend/holiday). Showing preceding trading session."
            is_exact = False

        # Calculate previous day's close for % change
        cursor.execute(
            "SELECT close FROM nifty_ohlcv WHERE date < ? ORDER BY date DESC LIMIT 1",
            (actual_date,),
        )
        prev_row = cursor.fetchone()
        prev_close = prev_row[0] if prev_row else target_row[1]

    conn.close()

    open_p = target_row[1]
    high_p = target_row[2]
    low_p = target_row[3]
    close_p = target_row[4]
    volume = target_row[5]

    change = round(close_p - prev_close, 2)
    change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0

    return {
        "requested_date": date_str,
        "date": actual_date,
        "open": open_p,
        "high": high_p,
        "low": low_p,
        "close": close_p,
        "volume": volume,
        "previous_close": prev_close,
        "change": change,
        "change_pct": change_pct,
        "note": note,
        "is_exact_match": is_exact,
    }


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
