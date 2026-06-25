from __future__ import annotations

import pandas as pd

from quantf.data.quality import validate_prices


def test_validate_prices_reports_invalid_high_low() -> None:
    prices = pd.DataFrame(
        [
            {
                "symbol": "NVDA",
                "date": pd.Timestamp("2026-06-25").date(),
                "open": 100,
                "high": 90,
                "low": 95,
                "close": 98,
                "volume": 1000,
            }
        ]
    )

    report = validate_prices(prices)

    assert len(report) == 1
    assert report.iloc[0]["severity"] == "error"
    assert report.iloc[0]["check_name"] == "price_validity"
