from __future__ import annotations

from pathlib import Path

import pandas as pd

from quantf.config import DEFAULT_PORTFOLIO_PATH, load_yaml


def load_positions(path: Path = DEFAULT_PORTFOLIO_PATH) -> pd.DataFrame:
    config = load_yaml(path)
    positions = config.get("positions", [])
    if not positions:
        return pd.DataFrame(columns=["symbol", "shares", "cost_basis"])
    frame = pd.DataFrame(positions)
    frame["symbol"] = frame["symbol"].str.upper()
    frame["shares"] = frame["shares"].astype(float)
    frame["cost_basis"] = frame["cost_basis"].astype(float)
    return frame


def build_portfolio_snapshot(positions: pd.DataFrame, latest_signals: pd.DataFrame) -> pd.DataFrame:
    if positions.empty:
        return pd.DataFrame()

    latest = latest_signals[["symbol", "close"]].copy()
    snapshot = positions.merge(latest, on="symbol", how="left")
    snapshot["market_value"] = snapshot["shares"] * snapshot["close"]
    total_value = snapshot["market_value"].sum()
    snapshot["weight"] = 0.0 if total_value == 0 else snapshot["market_value"] / total_value
    snapshot["unrealized_pnl"] = snapshot["market_value"] - snapshot["shares"] * snapshot["cost_basis"]
    return snapshot.sort_values("market_value", ascending=False)
