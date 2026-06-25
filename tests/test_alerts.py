from __future__ import annotations

import pandas as pd

from quantf.alerts.rules import generate_asset_alerts


def test_generate_asset_alerts_for_warning_drawdown() -> None:
    latest = pd.DataFrame(
        [
            {
                "symbol": "NVDA",
                "date": "2026-06-25",
                "trend_state": "neutral",
                "risk_state": "warning",
                "drawdown_from_52w_high": -0.35,
            }
        ]
    )

    alerts = generate_asset_alerts(latest)

    assert len(alerts) == 1
    assert alerts.iloc[0]["severity"] == "warning"
