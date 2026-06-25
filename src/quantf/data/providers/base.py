from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

import pandas as pd


@dataclass(frozen=True)
class PriceFetchResult:
    symbol: str
    start: date
    end: date
    provider: str
    raw_payload: str
    prices: pd.DataFrame


class MarketDataProvider(Protocol):
    name: str

    def fetch_prices(self, symbol: str, start: date, end: date) -> PriceFetchResult:
        pass
