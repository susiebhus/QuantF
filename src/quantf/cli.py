from __future__ import annotations

import argparse

from quantf.data.pipeline import update_market_data
from quantf.data.prices import load_prices
from quantf.db.connection import connect
from quantf.db.schema import ensure_schema
from quantf.events.engine import (
    generate_events,
    load_previous_signals,
    save_events,
)
from quantf.indicators.trend import compute_signals, load_latest_signals, save_signals
from quantf.portfolio.service import sync_portfolio_from_config, update_portfolio_stats


def main() -> None:
    parser = argparse.ArgumentParser(prog="quantf")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init-db")
    subparsers.add_parser("update-prices")
    subparsers.add_parser("compute-signals")
    subparsers.add_parser("generate-alerts")
    subparsers.add_parser("generate-events")
    subparsers.add_parser("run-daily")
    args = parser.parse_args()

    conn = connect()
    ensure_schema(conn)

    if args.command == "init-db":
        print("Database schema is ready.")
    elif args.command == "update-prices":
        result = update_market_data(conn)
        print(
            f"Market data update complete: {result.symbols} symbols, "
            f"{result.prices} prices, {result.quality_reports} quality reports, "
            f"{result.ingestion_runs} ingestion runs."
        )
    elif args.command == "compute-signals":
        prices = load_prices(conn)
        signals = compute_signals(prices)
        count = save_signals(conn, signals)
        print(f"Saved {count} signal rows.")
    elif args.command in {"generate-alerts", "generate-events"}:
        prices = load_prices(conn)
        latest = load_latest_signals(conn)
        previous = load_previous_signals(conn)
        sync_portfolio_from_config(conn)
        portfolio_drift = update_portfolio_stats(conn, latest)
        events = generate_events(latest, previous, prices, portfolio_drift)
        count = save_events(conn, events)
        print(f"Saved {count} new events.")
    elif args.command == "run-daily":
        pipeline_result = update_market_data(conn)
        prices = load_prices(conn)
        signals = compute_signals(prices)
        signal_count = save_signals(conn, signals)
        latest = load_latest_signals(conn)
        previous = load_previous_signals(conn)
        portfolio_rows = sync_portfolio_from_config(conn)
        portfolio_drift = update_portfolio_stats(conn, latest)
        events = generate_events(latest, previous, prices, portfolio_drift)
        event_count = save_events(conn, events)
        print(
            f"Daily run complete: {pipeline_result.prices} prices, "
            f"{signal_count} signals, {event_count} new events, "
            f"{pipeline_result.quality_reports} quality reports, "
            f"{portfolio_rows} portfolio rows."
        )
