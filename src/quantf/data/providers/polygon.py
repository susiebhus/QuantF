from __future__ import annotations

from datetime import date

from quantf.data.providers.base import PriceFetchResult


class PolygonProvider:
    name = "polygon"

    def fetch_prices(self, symbol: str, start: date, end: date) -> PriceFetchResult:
        raise NotImplementedError("PolygonProvider is reserved for a future data source.")
