from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from quantf.data.providers.base import PriceFetchResult


PRICE_COLUMNS = {
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Adj Close": "adj_close",
    "Volume": "volume",
}


class YahooFinanceProvider:
    name = "yahoo"

    def fetch_prices(self, symbol: str, start: date, end: date) -> PriceFetchResult:
        # yfinance treats end as exclusive, so request one extra day for inclusive ranges.
        raw = yf.download(
            symbol,
            start=start.isoformat(),
            end=(end + timedelta(days=1)).isoformat(),
            auto_adjust=False,
            group_by="ticker",
            progress=False,
            threads=False,
        )
        prices = normalize_yahoo_prices(raw, symbol, self.name)
        raw_payload = prices.to_json(orient="records", date_format="iso")
        return PriceFetchResult(
            symbol=symbol,
            start=start,
            end=end,
            provider=self.name,
            raw_payload=raw_payload,
            prices=prices,
        )


def normalize_yahoo_prices(raw: pd.DataFrame, symbol: str, provider: str) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame(
            columns=[
                "symbol",
                "date",
                "open",
                "high",
                "low",
                "close",
                "adj_close",
                "volume",
                "source",
                "updated_at",
            ]
        )

    frame = raw.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        if symbol in frame.columns.get_level_values(0):
            frame = frame[symbol]
        else:
            frame.columns = frame.columns.get_level_values(-1)

    frame = frame.rename(columns=PRICE_COLUMNS)
    frame = frame.reset_index().rename(columns={"Date": "date"})
    frame["date"] = pd.to_datetime(frame["date"]).dt.date
    frame["symbol"] = symbol.upper()
    frame["source"] = provider
    frame["updated_at"] = pd.Timestamp.utcnow().tz_localize(None)
    columns = [
        "symbol",
        "date",
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume",
        "source",
        "updated_at",
    ]
    return frame[[column for column in columns if column in frame.columns]].dropna(
        subset=["symbol", "date", "close"]
    )
