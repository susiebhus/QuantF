from __future__ import annotations

import pandas as pd

from quantf.indicators.trend import compute_signals


def test_compute_signals_detects_uptrend() -> None:
    prices = pd.DataFrame(
        {
            "symbol": ["SPY"] * 260,
            "date": pd.date_range("2024-01-01", periods=260, freq="D"),
            "close": range(100, 360),
            "adj_close": range(100, 360),
        }
    )

    signals = compute_signals(prices)
    latest = signals.iloc[-1]

    assert latest["trend_state"] == "uptrend"
    assert latest["risk_state"] == "normal"
