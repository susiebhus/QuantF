from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd
import yfinance as yf

from quantf.config import DEFAULT_WATCHLIST_PATH, load_watchlist


PRICE_COLUMNS = {
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Adj Close": "adj_close",
    "Volume": "volume",
}


def download_prices(
    symbols: list[str] | None = None,
    watchlist_path: Path = DEFAULT_WATCHLIST_PATH,
    period: str = "10y",
) -> pd.DataFrame:
    if symbols is None:
        symbols = load_watchlist(watchlist_path)
    if not symbols:
        raise ValueError("No symbols configured.")

    raw = yf.download(
        symbols,
        period=period,
        auto_adjust=False,
        group_by="ticker",
        progress=False,
        threads=True,
    )
    return normalize_yfinance_prices(raw, symbols)


def normalize_yfinance_prices(raw: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if isinstance(raw.columns, pd.MultiIndex):
        for symbol in symbols:
            if symbol not in raw.columns.get_level_values(0):
                continue
            frame = raw[symbol].rename(columns=PRICE_COLUMNS)
            frame["symbol"] = symbol
            frames.append(frame)
    else:
        symbol = symbols[0]
        frame = raw.rename(columns=PRICE_COLUMNS)
        frame["symbol"] = symbol
        frames.append(frame)

    if not frames:
        return pd.DataFrame()

    prices = pd.concat(frames)
    prices = prices.reset_index().rename(columns={"Date": "date"})
    prices["date"] = pd.to_datetime(prices["date"]).dt.date
    prices["source"] = "yfinance"
    prices["updated_at"] = now

    columns = [
        "symbol",
        "date",
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume",
        "source",
        "updated_at",
    ]
    return prices[[column for column in columns if column in prices.columns]].dropna(
        subset=["symbol", "date", "close"]
    )


def save_prices(conn: duckdb.DuckDBPyConnection, prices: pd.DataFrame) -> int:
    if prices.empty:
        return 0

    conn.register("incoming_prices", prices)
    conn.execute(
        """
        DELETE FROM daily_prices
        USING incoming_prices
        WHERE daily_prices.symbol = incoming_prices.symbol
          AND daily_prices.date = incoming_prices.date
        """
    )
    conn.execute(
        """
        INSERT INTO daily_prices
        SELECT symbol, date, open, high, low, close, adj_close, volume, source, updated_at
        FROM incoming_prices
        """
    )
    conn.unregister("incoming_prices")
    return len(prices)


def load_prices(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return conn.execute(
        """
        SELECT *
        FROM daily_prices
        ORDER BY symbol, date
        """
    ).fetchdf()
