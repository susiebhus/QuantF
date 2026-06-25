from __future__ import annotations

import duckdb


def ensure_schema(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_prices (
          symbol TEXT NOT NULL,
          date_range TEXT NOT NULL,
          raw_payload JSON NOT NULL,
          provider TEXT NOT NULL,
          fetched_at TIMESTAMP NOT NULL,
          hash TEXT NOT NULL,
          PRIMARY KEY (hash)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ingestion_runs (
          run_id TEXT NOT NULL,
          symbol TEXT NOT NULL,
          provider TEXT NOT NULL,
          start_date DATE NOT NULL,
          end_date DATE NOT NULL,
          status TEXT NOT NULL,
          error_message TEXT,
          rows_fetched INTEGER NOT NULL,
          fetched_at TIMESTAMP NOT NULL,
          PRIMARY KEY (run_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_prices (
          symbol TEXT NOT NULL,
          date DATE NOT NULL,
          open DOUBLE,
          high DOUBLE,
          low DOUBLE,
          close DOUBLE,
          adj_close DOUBLE,
          volume DOUBLE,
          source TEXT NOT NULL,
          updated_at TIMESTAMP NOT NULL,
          PRIMARY KEY (symbol, date)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS data_quality_report (
          id TEXT NOT NULL,
          symbol TEXT NOT NULL,
          date DATE NOT NULL,
          check_name TEXT NOT NULL,
          severity TEXT NOT NULL,
          message TEXT NOT NULL,
          created_at TIMESTAMP NOT NULL,
          PRIMARY KEY (id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS signals_daily (
          symbol TEXT NOT NULL,
          date DATE NOT NULL,
          close DOUBLE,
          ma_20 DOUBLE,
          ma_50 DOUBLE,
          ma_200 DOUBLE,
          return_20d DOUBLE,
          return_60d DOUBLE,
          return_252d DOUBLE,
          volatility_20d DOUBLE,
          volatility_60d DOUBLE,
          drawdown_from_52w_high DOUBLE,
          drawdown_from_all_time_high DOUBLE,
          rs_spy DOUBLE,
          rs_qqq DOUBLE,
          trend_state TEXT,
          risk_state TEXT,
          updated_at TIMESTAMP NOT NULL,
          PRIMARY KEY (symbol, date)
        )
        """
    )
    conn.execute("ALTER TABLE signals_daily ADD COLUMN IF NOT EXISTS ma_20 DOUBLE")
    conn.execute("ALTER TABLE signals_daily ADD COLUMN IF NOT EXISTS rs_spy DOUBLE")
    conn.execute("ALTER TABLE signals_daily ADD COLUMN IF NOT EXISTS rs_qqq DOUBLE")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
          id TEXT NOT NULL,
          created_at TIMESTAMP NOT NULL,
          symbol TEXT,
          alert_type TEXT NOT NULL,
          severity TEXT NOT NULL,
          title TEXT NOT NULL,
          message TEXT NOT NULL,
          resolved BOOLEAN NOT NULL DEFAULT false,
          PRIMARY KEY (id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
          event_id TEXT NOT NULL,
          event_time TIMESTAMP NOT NULL,
          symbol TEXT,
          event_type TEXT NOT NULL,
          severity TEXT NOT NULL,
          title TEXT NOT NULL,
          message TEXT NOT NULL,
          payload JSON NOT NULL,
          source_date DATE,
          PRIMARY KEY (event_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS portfolio (
          symbol TEXT NOT NULL,
          shares DOUBLE NOT NULL,
          cost_basis DOUBLE NOT NULL,
          target_weight DOUBLE NOT NULL,
          updated_at TIMESTAMP NOT NULL,
          PRIMARY KEY (symbol)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS portfolio_stats (
          symbol TEXT NOT NULL,
          date DATE NOT NULL,
          shares DOUBLE NOT NULL,
          market_value DOUBLE,
          cost_basis DOUBLE,
          weight DOUBLE,
          target_weight DOUBLE,
          drift DOUBLE,
          updated_at TIMESTAMP NOT NULL,
          PRIMARY KEY (symbol, date)
        )
        """
    )
