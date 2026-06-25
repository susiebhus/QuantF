from __future__ import annotations

import duckdb


def ensure_schema(conn: duckdb.DuckDBPyConnection) -> None:
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
        CREATE TABLE IF NOT EXISTS signals_daily (
          symbol TEXT NOT NULL,
          date DATE NOT NULL,
          close DOUBLE,
          ma_50 DOUBLE,
          ma_200 DOUBLE,
          return_20d DOUBLE,
          return_60d DOUBLE,
          return_252d DOUBLE,
          volatility_20d DOUBLE,
          volatility_60d DOUBLE,
          drawdown_from_52w_high DOUBLE,
          drawdown_from_all_time_high DOUBLE,
          trend_state TEXT,
          risk_state TEXT,
          updated_at TIMESTAMP NOT NULL,
          PRIMARY KEY (symbol, date)
        )
        """
    )
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
