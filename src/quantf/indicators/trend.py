from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    import duckdb


def compute_signals(prices: pd.DataFrame) -> pd.DataFrame:
    if prices.empty:
        return pd.DataFrame()

    frames: list[pd.DataFrame] = []
    for symbol, group in prices.groupby("symbol", sort=True):
        frame = group.sort_values("date").copy()
        price = frame["adj_close"].fillna(frame["close"])
        returns = price.pct_change()

        frame["close"] = price
        frame["ma_50"] = price.rolling(50, min_periods=50).mean()
        frame["ma_200"] = price.rolling(200, min_periods=200).mean()
        frame["return_20d"] = price.pct_change(20)
        frame["return_60d"] = price.pct_change(60)
        frame["return_252d"] = price.pct_change(252)
        frame["volatility_20d"] = returns.rolling(20, min_periods=20).std() * (252**0.5)
        frame["volatility_60d"] = returns.rolling(60, min_periods=60).std() * (252**0.5)
        frame["drawdown_from_52w_high"] = price / price.rolling(252, min_periods=20).max() - 1
        frame["drawdown_from_all_time_high"] = price / price.cummax() - 1
        frame["trend_state"] = frame.apply(_trend_state, axis=1)
        frame["risk_state"] = frame.apply(_risk_state, axis=1)
        frame["symbol"] = symbol
        frames.append(frame)

    signals = pd.concat(frames, ignore_index=True)
    signals["updated_at"] = datetime.now(timezone.utc).replace(tzinfo=None)
    columns = [
        "symbol",
        "date",
        "close",
        "ma_50",
        "ma_200",
        "return_20d",
        "return_60d",
        "return_252d",
        "volatility_20d",
        "volatility_60d",
        "drawdown_from_52w_high",
        "drawdown_from_all_time_high",
        "trend_state",
        "risk_state",
        "updated_at",
    ]
    return signals[columns]


def save_signals(conn: "duckdb.DuckDBPyConnection", signals: pd.DataFrame) -> int:
    if signals.empty:
        return 0

    conn.register("incoming_signals", signals)
    conn.execute(
        """
        DELETE FROM signals_daily
        USING incoming_signals
        WHERE signals_daily.symbol = incoming_signals.symbol
          AND signals_daily.date = incoming_signals.date
        """
    )
    conn.execute(
        """
        INSERT INTO signals_daily
        SELECT *
        FROM incoming_signals
        """
    )
    conn.unregister("incoming_signals")
    return len(signals)


def load_latest_signals(conn: "duckdb.DuckDBPyConnection") -> pd.DataFrame:
    return conn.execute(
        """
        SELECT s.*
        FROM signals_daily s
        INNER JOIN (
          SELECT symbol, max(date) AS date
          FROM signals_daily
          GROUP BY symbol
        ) latest
          ON s.symbol = latest.symbol
         AND s.date = latest.date
        ORDER BY s.symbol
        """
    ).fetchdf()


def _trend_state(row: pd.Series) -> str:
    close = row.get("close")
    ma_50 = row.get("ma_50")
    ma_200 = row.get("ma_200")
    if pd.isna(close) or pd.isna(ma_50) or pd.isna(ma_200):
        return "insufficient_data"
    if close > ma_200 and ma_50 > ma_200:
        return "uptrend"
    if close < ma_200 and ma_50 < ma_200:
        return "downtrend"
    return "neutral"


def _risk_state(row: pd.Series) -> str:
    drawdown = row.get("drawdown_from_52w_high")
    close = row.get("close")
    ma_200 = row.get("ma_200")

    if pd.isna(drawdown):
        return "insufficient_data"
    if drawdown <= -0.30:
        return "warning"
    if drawdown <= -0.20:
        return "watch"
    if not pd.isna(ma_200) and close < ma_200:
        return "watch"
    return "normal"
