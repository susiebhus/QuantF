from __future__ import annotations

from quantf.data.providers import MarketDataProvider, YahooFinanceProvider
from quantf.data.providers.alpha_vantage import AlphaVantageProvider
from quantf.data.providers.polygon import PolygonProvider


def get_market_data_provider(name: str = "yahoo") -> MarketDataProvider:
    normalized = name.strip().lower()
    if normalized in {"yahoo", "yfinance", "yahoo_finance"}:
        return YahooFinanceProvider()
    if normalized == "polygon":
        return PolygonProvider()
    if normalized in {"alpha_vantage", "alphavantage"}:
        return AlphaVantageProvider()
    raise ValueError(f"Unsupported market data provider: {name}")
