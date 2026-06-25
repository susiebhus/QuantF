from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import duckdb
import pandas as pd

from quantf.config import load_watchlist
from quantf.data.prices import get_last_price_date, load_prices, save_prices
from quantf.data.provider_factory import get_market_data_provider
from quantf.data.quality import has_quality_errors, save_quality_report, validate_prices
from quantf.data.raw import save_raw_prices


@dataclass(frozen=True)
class PipelineResult:
    symbols: int
    prices: int
    quality_reports: int
    ingestion_runs: int


def update_market_data(
    conn: duckdb.DuckDBPyConnection,
    provider_name: str = "yahoo",
    lookback_years: int = 10,
    end_date: date | None = None,
) -> PipelineResult:
    symbols = load_watchlist()
    provider = get_market_data_provider(provider_name)
    end = end_date or datetime.now(timezone.utc).date()

    price_count = 0
    quality_count = 0
    run_count = 0

    for symbol in symbols:
        start = _next_start_date(conn, symbol, end, lookback_years)
        if start > end:
            _log_ingestion_run(
                conn,
                symbol=symbol,
                provider=provider.name,
                start_date=start,
                end_date=end,
                status="skipped",
                error_message="already up to date",
                rows_fetched=0,
            )
            run_count += 1
            continue

        try:
            result = provider.fetch_prices(symbol, start, end)
            save_raw_prices(conn, result)
            report = validate_prices(result.prices, start=start, end=end)
            quality_count += save_quality_report(conn, report)

            if has_quality_errors(report):
                status = "quality_failed"
                error_message = "data quality errors detected"
                rows = 0
            else:
                rows = save_prices(conn, result.prices)
                price_count += rows
                status = "success"
                error_message = None

            _log_ingestion_run(
                conn,
                symbol=symbol,
                provider=provider.name,
                start_date=start,
                end_date=end,
                status=status,
                error_message=error_message,
                rows_fetched=len(result.prices),
            )
            run_count += 1
        except Exception as exc:
            _log_ingestion_run(
                conn,
                symbol=symbol,
                provider=provider.name,
                start_date=start,
                end_date=end,
                status="failed",
                error_message=str(exc),
                rows_fetched=0,
            )
            run_count += 1

    return PipelineResult(
        symbols=len(symbols),
        prices=price_count,
        quality_reports=quality_count,
        ingestion_runs=run_count,
    )


def load_ingestion_runs(conn: duckdb.DuckDBPyConnection, limit: int = 200) -> pd.DataFrame:
    return conn.execute(
        """
        SELECT *
        FROM ingestion_runs
        ORDER BY fetched_at DESC
        LIMIT ?
        """,
        [limit],
    ).fetchdf()


def load_ingestion_summary(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return conn.execute(
        """
        SELECT
          count(*) AS total_runs,
          sum(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS successful_runs,
          sum(CASE WHEN status IN ('failed', 'quality_failed') THEN 1 ELSE 0 END) AS failed_runs,
          max(fetched_at) AS last_update_time
        FROM ingestion_runs
        """
    ).fetchdf()


def _next_start_date(
    conn: duckdb.DuckDBPyConnection,
    symbol: str,
    end: date,
    lookback_years: int,
) -> date:
    last_date = get_last_price_date(conn, symbol)
    if last_date is None:
        return end - timedelta(days=365 * lookback_years)
    return last_date + timedelta(days=1)


def _log_ingestion_run(
    conn: duckdb.DuckDBPyConnection,
    *,
    symbol: str,
    provider: str,
    start_date: date,
    end_date: date,
    status: str,
    error_message: str | None,
    rows_fetched: int,
) -> None:
    fetched_at = datetime.now(timezone.utc).replace(tzinfo=None)
    run_id = f"{symbol}:{provider}:{start_date}:{end_date}:{fetched_at.isoformat()}"
    row = pd.DataFrame(
        [
            {
                "run_id": run_id,
                "symbol": symbol,
                "provider": provider,
                "start_date": start_date,
                "end_date": end_date,
                "status": status,
                "error_message": error_message,
                "rows_fetched": rows_fetched,
                "fetched_at": fetched_at,
            }
        ]
    )
    conn.register("incoming_ingestion_runs", row)
    conn.execute(
        """
        INSERT INTO ingestion_runs
        SELECT run_id, symbol, provider, start_date, end_date, status, error_message, rows_fetched, fetched_at
        FROM incoming_ingestion_runs
        """
    )
    conn.unregister("incoming_ingestion_runs")


def load_clean_prices(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return load_prices(conn)
