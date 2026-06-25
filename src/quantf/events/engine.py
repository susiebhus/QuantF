from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha1
import json
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    import duckdb


RISK_LEVELS = {
    "insufficient_data": 0,
    "normal": 1,
    "watch": 2,
    "warning": 3,
    "critical": 4,
}


def generate_events(
    latest_signals: pd.DataFrame,
    previous_signals: pd.DataFrame,
    prices: pd.DataFrame,
    portfolio_drift: pd.DataFrame | None = None,
) -> pd.DataFrame:
    events: list[dict[str, object]] = []
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    previous_by_symbol = {
        row["symbol"]: row for row in previous_signals.to_dict(orient="records")
    }

    for row in latest_signals.to_dict(orient="records"):
        symbol = row["symbol"]
        previous = previous_by_symbol.get(symbol)
        source_date = row["date"]

        if previous and row.get("trend_state") != previous.get("trend_state"):
            events.append(
                _event(
                    now,
                    symbol,
                    source_date,
                    "TrendChanged",
                    "watch",
                    f"{symbol} trend changed",
                    f"{symbol} trend changed from {previous.get('trend_state')} to {row.get('trend_state')}.",
                    {"from": previous.get("trend_state"), "to": row.get("trend_state")},
                )
            )

        if previous and _risk_level(row.get("risk_state")) > _risk_level(previous.get("risk_state")):
            events.append(
                _event(
                    now,
                    symbol,
                    source_date,
                    "RiskEscalated",
                    row.get("risk_state") or "watch",
                    f"{symbol} risk escalated",
                    f"{symbol} risk changed from {previous.get('risk_state')} to {row.get('risk_state')}.",
                    {"from": previous.get("risk_state"), "to": row.get("risk_state")},
                )
            )

        if previous and _crossed_ma200(previous, row):
            direction = "above" if row["close"] > row["ma_200"] else "below"
            events.append(
                _event(
                    now,
                    symbol,
                    source_date,
                    "PriceCrossMA200",
                    "watch",
                    f"{symbol} crossed MA200",
                    f"{symbol} closed {direction} its 200-day moving average.",
                    {"direction": direction, "close": row.get("close"), "ma_200": row.get("ma_200")},
                )
            )

        drawdown = row.get("drawdown_from_52w_high")
        if pd.notna(drawdown) and drawdown >= -0.000001:
            events.append(
                _event(
                    now,
                    symbol,
                    source_date,
                    "New52WeekHigh",
                    "info",
                    f"{symbol} made a new 52-week high",
                    f"{symbol} closed at or near a new 52-week high.",
                    {"close": row.get("close")},
                )
            )

    events.extend(_new_52_week_low_events(now, prices))

    if portfolio_drift is not None and not portfolio_drift.empty:
        for row in portfolio_drift[portfolio_drift["deviation"].abs() >= 0.05].to_dict(orient="records"):
            symbol = row["symbol"]
            events.append(
                _event(
                    now,
                    symbol,
                    now.date(),
                    "PortfolioDrift",
                    "watch",
                    f"{symbol} allocation drift",
                    f"{symbol} is {row['deviation']:.1%} away from target weight.",
                    {
                        "weight": row.get("weight"),
                        "target_weight": row.get("target_weight"),
                        "deviation": row.get("deviation"),
                    },
                )
            )

    return pd.DataFrame(
        events,
        columns=[
            "event_id",
            "event_time",
            "symbol",
            "event_type",
            "severity",
            "title",
            "message",
            "payload",
            "source_date",
        ],
    )


def save_events(conn: "duckdb.DuckDBPyConnection", events: pd.DataFrame) -> int:
    if events.empty:
        return 0
    existing = conn.execute("SELECT event_id FROM events").fetchdf()
    existing_ids = set(existing["event_id"]) if not existing.empty else set()
    new_events = events[~events["event_id"].isin(existing_ids)].copy()
    if new_events.empty:
        return 0

    conn.register("incoming_events", new_events)
    conn.execute(
        """
        INSERT INTO events
        SELECT
          event_id,
          event_time,
          symbol,
          event_type,
          severity,
          title,
          message,
          payload::JSON,
          source_date
        FROM incoming_events
        WHERE event_id NOT IN (SELECT event_id FROM events)
        """
    )
    conn.unregister("incoming_events")
    return len(new_events)


def load_events(conn: "duckdb.DuckDBPyConnection", limit: int = 500) -> pd.DataFrame:
    return conn.execute(
        """
        SELECT *
        FROM events
        ORDER BY event_time DESC
        LIMIT ?
        """,
        [limit],
    ).fetchdf()


def load_previous_signals(conn: "duckdb.DuckDBPyConnection") -> pd.DataFrame:
    return conn.execute(
        """
        WITH ranked AS (
          SELECT
            *,
            row_number() OVER (PARTITION BY symbol ORDER BY date DESC) AS rn
          FROM signals_daily
        )
        SELECT *
        FROM ranked
        WHERE rn = 2
        ORDER BY symbol
        """
    ).fetchdf()


def _event(
    now: datetime,
    symbol: str,
    source_date: object,
    event_type: str,
    severity: str,
    title: str,
    message: str,
    payload: dict[str, object],
) -> dict[str, object]:
    raw_id = f"{symbol}:{source_date}:{event_type}:{title}"
    return {
        "event_id": sha1(raw_id.encode("utf-8")).hexdigest(),
        "event_time": now,
        "symbol": symbol,
        "event_type": event_type,
        "severity": severity,
        "title": title,
        "message": message,
        "payload": json.dumps(_json_safe(payload), ensure_ascii=False),
        "source_date": source_date,
    }


def _risk_level(value: object) -> int:
    return RISK_LEVELS.get(str(value), 0)


def _crossed_ma200(previous: dict[str, object], current: dict[str, object]) -> bool:
    if pd.isna(previous.get("close")) or pd.isna(previous.get("ma_200")):
        return False
    if pd.isna(current.get("close")) or pd.isna(current.get("ma_200")):
        return False
    was_above = previous["close"] > previous["ma_200"]
    is_above = current["close"] > current["ma_200"]
    return was_above != is_above


def _new_52_week_low_events(now: datetime, prices: pd.DataFrame) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    if prices.empty:
        return events

    for symbol, group in prices.groupby("symbol"):
        frame = group.sort_values("date").copy()
        if len(frame) < 20:
            continue
        price = frame["adj_close"].fillna(frame["close"])
        latest_price = price.iloc[-1]
        latest_date = frame["date"].iloc[-1]
        low_52w = price.tail(252).min()
        if pd.notna(low_52w) and latest_price <= low_52w:
            events.append(
                _event(
                    now,
                    symbol,
                    latest_date,
                    "New52WeekLow",
                    "warning",
                    f"{symbol} made a new 52-week low",
                    f"{symbol} closed at or near a new 52-week low.",
                    {"close": latest_price, "low_52w": low_52w},
                )
            )
    return events


def _json_safe(payload: dict[str, object]) -> dict[str, object]:
    safe: dict[str, object] = {}
    for key, value in payload.items():
        if pd.isna(value):
            safe[key] = None
        elif hasattr(value, "item"):
            safe[key] = value.item()
        else:
            safe[key] = value
    return safe
