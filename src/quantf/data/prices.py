from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd

from quantf.config import DEFAULT_WATCHLIST_PATH, load_watchlist
from quantf.data.provider_factory import get_market_data_provider


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
    provider_name: str = "yahoo",
) -> pd.DataFrame:
    """Compatibility helper for manual full downloads.

    The v1.1 pipeline uses incremental provider fetches. This function remains
    for ad-hoc research commands and tests, but it still goes through the
    provider abstraction.
    """
    if symbols is None:
        symbols = load_watchlist(watchlist_path)
    if not symbols:
        raise ValueError("No symbols configured.")

    end = datetime.now(timezone.utc).date()
    days = _period_to_days(period)
    start = end - pd.Timedelta(days=days).to_pytimedelta()
    provider = get_market_data_provider(provider_name)
    frames = [provider.fetch_prices(symbol, start, end).prices for symbol in symbols]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


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


def get_last_price_date(conn: duckdb.DuckDBPyConnection, symbol: str) -> date | None:
    result = conn.execute(
        """
        SELECT max(date)
        FROM daily_prices
        WHERE symbol = ?
        """,
        [symbol.upper()],
    ).fetchone()
    if not result or result[0] is None:
        return None
    value = result[0]
    if isinstance(value, datetime):
        return value.date()
    return value


def _period_to_days(period: str) -> int:
    normalized = period.strip().lower()
    if normalized.endswith("y"):
        return int(normalized[:-1]) * 365
    if normalized.endswith("mo"):
        return int(normalized[:-2]) * 30
    if normalized.endswith("d"):
        return int(normalized[:-1])
    return 3650
