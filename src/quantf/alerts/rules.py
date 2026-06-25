from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha1
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    import duckdb


def generate_asset_alerts(latest_signals: pd.DataFrame) -> pd.DataFrame:
    alerts: list[dict[str, object]] = []
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    for row in latest_signals.to_dict(orient="records"):
        symbol = row["symbol"]
        date = str(row["date"])
        trend_state = row.get("trend_state")
        risk_state = row.get("risk_state")
        drawdown = row.get("drawdown_from_52w_high")

        if trend_state == "downtrend":
            alerts.append(
                _alert(
                    now=now,
                    symbol=symbol,
                    date=date,
                    alert_type="trend",
                    severity="watch",
                    title=f"{symbol} long-term trend is weak",
                    message=f"{symbol} is below its 200-day moving average with a weak long-term trend.",
                )
            )

        if risk_state == "warning":
            alerts.append(
                _alert(
                    now=now,
                    symbol=symbol,
                    date=date,
                    alert_type="drawdown",
                    severity="warning",
                    title=f"{symbol} drawdown warning",
                    message=f"{symbol} is down {drawdown:.1%} from its 52-week high.",
                )
            )
        elif risk_state == "watch":
            alerts.append(
                _alert(
                    now=now,
                    symbol=symbol,
                    date=date,
                    alert_type="risk",
                    severity="watch",
                    title=f"{symbol} needs attention",
                    message=f"{symbol} is in watch state. Current 52-week drawdown: {drawdown:.1%}.",
                )
            )

    return pd.DataFrame(alerts)


def save_alerts(conn: "duckdb.DuckDBPyConnection", alerts: pd.DataFrame) -> int:
    if alerts.empty:
        return 0

    conn.register("incoming_alerts", alerts)
    conn.execute(
        """
        DELETE FROM alerts
        USING incoming_alerts
        WHERE alerts.id = incoming_alerts.id
        """
    )
    conn.execute(
        """
        INSERT INTO alerts
        SELECT id, created_at, symbol, alert_type, severity, title, message, resolved
        FROM incoming_alerts
        """
    )
    conn.unregister("incoming_alerts")
    return len(alerts)


def load_open_alerts(conn: "duckdb.DuckDBPyConnection") -> pd.DataFrame:
    return conn.execute(
        """
        SELECT *
        FROM alerts
        WHERE resolved = false
        ORDER BY
          CASE severity
            WHEN 'critical' THEN 1
            WHEN 'warning' THEN 2
            WHEN 'watch' THEN 3
            ELSE 4
          END,
          created_at DESC
        """
    ).fetchdf()


def _alert(
    *,
    now: datetime,
    symbol: str,
    date: str,
    alert_type: str,
    severity: str,
    title: str,
    message: str,
) -> dict[str, object]:
    raw_id = f"{symbol}:{date}:{alert_type}:{severity}:{title}"
    return {
        "id": sha1(raw_id.encode("utf-8")).hexdigest(),
        "created_at": now,
        "symbol": symbol,
        "alert_type": alert_type,
        "severity": severity,
        "title": title,
        "message": message,
        "resolved": False,
    }
