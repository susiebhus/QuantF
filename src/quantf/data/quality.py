from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from hashlib import sha1
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    import duckdb


def validate_prices(prices: pd.DataFrame, start: date | None = None, end: date | None = None) -> pd.DataFrame:
    reports: list[dict[str, object]] = []
    created_at = datetime.now(timezone.utc).replace(tzinfo=None)

    if prices.empty:
        return _report_dataframe(reports)

    for row in prices.to_dict(orient="records"):
        symbol = row["symbol"]
        row_date = row["date"]
        if pd.isna(row.get("open")) or pd.isna(row.get("close")):
            reports.append(
                _report(created_at, symbol, row_date, "price_validity", "error", "open/close is null")
            )
        if not pd.isna(row.get("high")) and not pd.isna(row.get("low")) and row["high"] < row["low"]:
            reports.append(
                _report(created_at, symbol, row_date, "price_validity", "error", "high is lower than low")
            )
        if not pd.isna(row.get("volume")) and row["volume"] < 0:
            reports.append(
                _report(created_at, symbol, row_date, "price_validity", "error", "volume is negative")
            )

    for symbol, group in prices.groupby("symbol"):
        frame = group.sort_values("date").copy()
        frame["return_1d"] = frame["close"].pct_change()
        for row in frame[frame["return_1d"].abs() > 0.40].to_dict(orient="records"):
            reports.append(
                _report(
                    created_at,
                    symbol,
                    row["date"],
                    "spike_detection",
                    "warning",
                    f"single-day return is {row['return_1d']:.1%}",
                )
            )

        if start and end:
            expected = _weekdays(start, end)
            actual = set(pd.to_datetime(frame["date"]).dt.date)
            missing = sorted(expected - actual)
            for missing_date in missing:
                reports.append(
                    _report(
                        created_at,
                        symbol,
                        missing_date,
                        "missing_data",
                        "warning",
                        "weekday price is missing; holidays may require manual review",
                    )
                )

    return _report_dataframe(reports)


def has_quality_errors(report: pd.DataFrame) -> bool:
    return not report.empty and bool((report["severity"] == "error").any())


def save_quality_report(conn: "duckdb.DuckDBPyConnection", report: pd.DataFrame) -> int:
    if report.empty:
        return 0
    conn.register("incoming_quality_report", report)
    conn.execute(
        """
        DELETE FROM data_quality_report
        USING incoming_quality_report
        WHERE data_quality_report.id = incoming_quality_report.id
        """
    )
    conn.execute(
        """
        INSERT INTO data_quality_report
        SELECT id, symbol, date, check_name, severity, message, created_at
        FROM incoming_quality_report
        """
    )
    conn.unregister("incoming_quality_report")
    return len(report)


def load_quality_summary(conn: "duckdb.DuckDBPyConnection") -> pd.DataFrame:
    return conn.execute(
        """
        SELECT severity, check_name, count(*) AS count
        FROM data_quality_report
        GROUP BY severity, check_name
        ORDER BY severity, check_name
        """
    ).fetchdf()


def load_recent_quality_report(conn: "duckdb.DuckDBPyConnection", limit: int = 200) -> pd.DataFrame:
    return conn.execute(
        """
        SELECT *
        FROM data_quality_report
        ORDER BY created_at DESC, symbol, date DESC
        LIMIT ?
        """,
        [limit],
    ).fetchdf()


def _weekdays(start: date, end: date) -> set[date]:
    days: set[date] = set()
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.add(current)
        current += timedelta(days=1)
    return days


def _report(
    created_at: datetime,
    symbol: str,
    report_date: date,
    check_name: str,
    severity: str,
    message: str,
) -> dict[str, object]:
    raw_id = f"{symbol}:{report_date}:{check_name}:{severity}:{message}"
    return {
        "id": sha1(raw_id.encode("utf-8")).hexdigest(),
        "symbol": symbol,
        "date": report_date,
        "check_name": check_name,
        "severity": severity,
        "message": message,
        "created_at": created_at,
    }


def _report_dataframe(reports: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(
        reports,
        columns=["id", "symbol", "date", "check_name", "severity", "message", "created_at"],
    )
