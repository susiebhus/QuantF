from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256

import duckdb
import pandas as pd

from quantf.data.providers.base import PriceFetchResult


def save_raw_prices(conn: duckdb.DuckDBPyConnection, result: PriceFetchResult) -> str:
    fetched_at = datetime.now(timezone.utc).replace(tzinfo=None)
    date_range = f"{result.start.isoformat()}:{result.end.isoformat()}"
    digest = sha256(
        f"{result.provider}:{result.symbol}:{date_range}:{result.raw_payload}".encode("utf-8")
    ).hexdigest()
    row = pd.DataFrame(
        [
            {
                "symbol": result.symbol.upper(),
                "date_range": date_range,
                "raw_payload": result.raw_payload,
                "provider": result.provider,
                "fetched_at": fetched_at,
                "hash": digest,
            }
        ]
    )
    conn.register("incoming_raw_prices", row)
    conn.execute(
        """
        DELETE FROM raw_prices
        USING incoming_raw_prices
        WHERE raw_prices.hash = incoming_raw_prices.hash
        """
    )
    conn.execute(
        """
        INSERT INTO raw_prices
        SELECT symbol, date_range, raw_payload::JSON, provider, fetched_at, hash
        FROM incoming_raw_prices
        """
    )
    conn.unregister("incoming_raw_prices")
    return digest
