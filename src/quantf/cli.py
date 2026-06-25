from __future__ import annotations

import argparse

from quantf.alerts.rules import generate_asset_alerts, save_alerts
from quantf.data.prices import download_prices, load_prices, save_prices
from quantf.db.connection import connect
from quantf.db.schema import ensure_schema
from quantf.indicators.trend import compute_signals, load_latest_signals, save_signals


def main() -> None:
    parser = argparse.ArgumentParser(prog="quantf")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init-db")
    subparsers.add_parser("update-prices")
    subparsers.add_parser("compute-signals")
    subparsers.add_parser("generate-alerts")
    subparsers.add_parser("run-daily")
    args = parser.parse_args()

    conn = connect()
    ensure_schema(conn)

    if args.command == "init-db":
        print("Database schema is ready.")
    elif args.command == "update-prices":
        prices = download_prices()
        count = save_prices(conn, prices)
        print(f"Saved {count} price rows.")
    elif args.command == "compute-signals":
        prices = load_prices(conn)
        signals = compute_signals(prices)
        count = save_signals(conn, signals)
        print(f"Saved {count} signal rows.")
    elif args.command == "generate-alerts":
        latest = load_latest_signals(conn)
        alerts = generate_asset_alerts(latest)
        count = save_alerts(conn, alerts)
        print(f"Saved {count} alerts.")
    elif args.command == "run-daily":
        prices = download_prices()
        price_count = save_prices(conn, prices)
        all_prices = load_prices(conn)
        signals = compute_signals(all_prices)
        signal_count = save_signals(conn, signals)
        latest = load_latest_signals(conn)
        alerts = generate_asset_alerts(latest)
        alert_count = save_alerts(conn, alerts)
        print(
            f"Daily run complete: {price_count} prices, "
            f"{signal_count} signals, {alert_count} alerts."
        )
