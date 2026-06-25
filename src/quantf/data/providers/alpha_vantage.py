from __future__ import annotations

from datetime import date

from quantf.data.providers.base import PriceFetchResult


class AlphaVantageProvider:
    name = "alpha_vantage"

    def fetch_prices(self, symbol: str, start: date, end: date) -> PriceFetchResult:
        raise NotImplementedError("AlphaVantageProvider is reserved for a future data source.")
