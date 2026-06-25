from __future__ import annotations

import pandas as pd


def compute_market_regime(latest_signals: pd.DataFrame) -> dict[str, str]:
    if latest_signals.empty:
        return {"regime": "Unknown", "reason": "No signals available"}

    by_symbol = {row["symbol"]: row for row in latest_signals.to_dict(orient="records")}
    spy = by_symbol.get("SPY")
    qqq = by_symbol.get("QQQ")

    if not spy or not qqq:
        return {"regime": "Neutral", "reason": "SPY or QQQ is missing from the watchlist"}

    if spy.get("risk_state") == "warning" or qqq.get("risk_state") == "warning":
        return {"regime": "Risk Off", "reason": "SPY or QQQ is in warning risk state"}

    if spy.get("trend_state") == "downtrend" or qqq.get("trend_state") == "downtrend":
        return {"regime": "Risk Off", "reason": "SPY or QQQ is in a long-term downtrend"}

    if (
        spy.get("trend_state") == "uptrend"
        and qqq.get("trend_state") == "uptrend"
        and spy.get("risk_state") == "normal"
        and qqq.get("risk_state") == "normal"
    ):
        return {"regime": "Risk On", "reason": "SPY and QQQ are in healthy uptrends"}

    return {"regime": "Neutral", "reason": "Market state is mixed"}
