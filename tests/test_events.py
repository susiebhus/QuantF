from __future__ import annotations

import pandas as pd

from quantf.events.engine import generate_events


def test_generate_events_emits_trend_changed() -> None:
    latest = pd.DataFrame(
        [
            {
                "symbol": "MSFT",
                "date": pd.Timestamp("2026-06-25").date(),
                "close": 100,
                "ma_200": 110,
                "trend_state": "downtrend",
                "risk_state": "watch",
                "drawdown_from_52w_high": -0.22,
            }
        ]
    )
    previous = pd.DataFrame(
        [
            {
                "symbol": "MSFT",
                "date": pd.Timestamp("2026-06-24").date(),
                "close": 112,
                "ma_200": 110,
                "trend_state": "uptrend",
                "risk_state": "normal",
            }
        ]
    )
    prices = pd.DataFrame(
        {
            "symbol": ["MSFT"] * 30,
            "date": pd.date_range("2026-05-01", periods=30, freq="D").date,
            "close": range(100, 130),
            "adj_close": range(100, 130),
        }
    )

    events = generate_events(latest, previous, prices)

    assert "TrendChanged" in set(events["event_type"])
    assert "RiskEscalated" in set(events["event_type"])
