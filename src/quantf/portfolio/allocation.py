from __future__ import annotations

from pathlib import Path

import pandas as pd

from quantf.config import DEFAULT_PORTFOLIO_PATH, load_yaml


def load_target_allocation(path: Path = DEFAULT_PORTFOLIO_PATH) -> pd.DataFrame:
    config = load_yaml(path)
    allocation = config.get("target_allocation", {})
    rows = [
        {"symbol": symbol.upper(), "target_weight": float(weight) / 100}
        for symbol, weight in allocation.items()
    ]
    return pd.DataFrame(rows)


def compare_to_target(snapshot: pd.DataFrame, target: pd.DataFrame) -> pd.DataFrame:
    if snapshot.empty and target.empty:
        return pd.DataFrame()

    current = snapshot[["symbol", "weight"]].copy() if not snapshot.empty else pd.DataFrame()
    comparison = target.merge(current, on="symbol", how="outer")
    comparison["target_weight"] = comparison["target_weight"].fillna(0.0)
    comparison["weight"] = comparison["weight"].fillna(0.0)
    comparison["deviation"] = comparison["weight"] - comparison["target_weight"]
    return comparison.sort_values("deviation", key=lambda series: series.abs(), ascending=False)
