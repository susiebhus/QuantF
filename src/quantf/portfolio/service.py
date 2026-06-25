from __future__ import annotations

from datetime import datetime, timezone

import duckdb
import pandas as pd

from quantf.portfolio.allocation import compare_to_target, load_target_allocation
from quantf.portfolio.holdings import build_portfolio_snapshot, load_positions


def sync_portfolio_from_config(conn: duckdb.DuckDBPyConnection) -> int:
    positions = load_positions()
    targets = load_target_allocation()
    if positions.empty and targets.empty:
        return 0

    rows = targets.merge(positions, on="symbol", how="outer")
    rows["shares"] = rows["shares"].fillna(0.0)
    rows["cost_basis"] = rows["cost_basis"].fillna(0.0)
    rows["target_weight"] = rows["target_weight"].fillna(0.0)
    rows["updated_at"] = datetime.now(timezone.utc).replace(tzinfo=None)
    conn.register("incoming_portfolio", rows)
    conn.execute(
        """
        DELETE FROM portfolio
        USING incoming_portfolio
        WHERE portfolio.symbol = incoming_portfolio.symbol
        """
    )
    conn.execute(
        """
        INSERT INTO portfolio
        SELECT symbol, shares, cost_basis, target_weight, updated_at
        FROM incoming_portfolio
        """
    )
    conn.unregister("incoming_portfolio")
    return len(rows)


def update_portfolio_stats(
    conn: duckdb.DuckDBPyConnection,
    latest_signals: pd.DataFrame,
) -> pd.DataFrame:
    positions = load_positions()
    targets = load_target_allocation()
    snapshot = build_portfolio_snapshot(positions, latest_signals)
    drift = compare_to_target(snapshot, targets)

    if snapshot.empty:
        return drift

    latest_date = latest_signals["date"].max()
    stats = drift.merge(
        snapshot[["symbol", "shares", "market_value", "cost_basis"]],
        on="symbol",
        how="left",
    )
    stats["date"] = latest_date
    stats["updated_at"] = datetime.now(timezone.utc).replace(tzinfo=None)
    stats = stats.rename(columns={"deviation": "drift"})
    stats["shares"] = stats["shares"].fillna(0.0)
    stats["market_value"] = stats["market_value"].fillna(0.0)
    stats["cost_basis"] = stats["cost_basis"].fillna(0.0)
    stats = stats[
        [
            "symbol",
            "date",
            "shares",
            "market_value",
            "cost_basis",
            "weight",
            "target_weight",
            "drift",
            "updated_at",
        ]
    ]

    conn.register("incoming_portfolio_stats", stats)
    conn.execute(
        """
        DELETE FROM portfolio_stats
        USING incoming_portfolio_stats
        WHERE portfolio_stats.symbol = incoming_portfolio_stats.symbol
          AND portfolio_stats.date = incoming_portfolio_stats.date
        """
    )
    conn.execute(
        """
        INSERT INTO portfolio_stats
        SELECT symbol, date, shares, market_value, cost_basis, weight, target_weight, drift, updated_at
        FROM incoming_portfolio_stats
        """
    )
    conn.unregister("incoming_portfolio_stats")

    return drift.rename(columns={"drift": "deviation"}) if "deviation" not in drift else drift


def load_latest_portfolio_stats(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return conn.execute(
        """
        SELECT p.*
        FROM portfolio_stats p
        INNER JOIN (
          SELECT max(date) AS date
          FROM portfolio_stats
        ) latest
          ON p.date = latest.date
        ORDER BY abs(p.drift) DESC
        """
    ).fetchdf()


def estimate_betas(prices: pd.DataFrame, benchmark: str = "SPY", window: int = 252) -> pd.DataFrame:
    if prices.empty or benchmark not in set(prices["symbol"]):
        return pd.DataFrame(columns=["symbol", "beta"])

    pivot = prices.pivot(index="date", columns="symbol", values="adj_close").sort_index()
    if benchmark not in pivot:
        return pd.DataFrame(columns=["symbol", "beta"])
    returns = pivot.pct_change().tail(window)
    benchmark_returns = returns[benchmark]
    variance = benchmark_returns.var()
    rows: list[dict[str, object]] = []
    for symbol in returns.columns:
        if symbol == benchmark or variance == 0 or pd.isna(variance):
            continue
        beta = returns[symbol].cov(benchmark_returns) / variance
        rows.append({"symbol": symbol, "beta": beta})
    return pd.DataFrame(rows)
